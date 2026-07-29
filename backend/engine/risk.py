"""GST notice-risk scoring (SPEC §14).

Model-free and fully deterministic, like the rest of `engine/`. Every figure below is
integer paise or an integer percentage; percentages are computed with rounded integer
division so the score is byte-stable across runs and machines.

Score formula, documented here and surfaced in the UI's "How is this computed?" panel:

    risk_score = gap_points + exception_points + personal_points        (0-100)

    gap_points       = min(latest gap_pct, 50) * 60 / 50     — weight 60%
    exception_points = min(open exceptions, 5) * 25 / 5      — weight 25%
    personal_points  = min(personal_pct, 20)   * 15 / 20     — weight 15%

`personal_pct` is the share of total UPI volume (in + out) that carries a personal
label — the business/personal ambiguity the department reads as under-declaration.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from engine.exception_text import format_paise
from engine.types import Entry, ReconciliationResult

GAP_WEIGHT, GAP_CAP_PCT = 60, 50
EXCEPTION_WEIGHT, EXCEPTION_CAP = 25, 5
PERSONAL_WEIGHT, PERSONAL_CAP_PCT = 15, 20

WATCH_BAND, HIGH_BAND = 40, 70
MOM_SPIKE_PCT = 40
GST_REGISTRATION_THRESHOLD_PAISE = 4_000_000_00  # ₹40,00,000 annual turnover, goods
THRESHOLD_PROXIMITY_PCT = 80

INFLOW_TYPES = frozenset({"sale", "payment_in", "credit_received"})


@dataclass(frozen=True)
class MonthGap:
    month: str
    upi_received_paise: int
    declared_paise: int
    gap_paise: int
    gap_pct: int


@dataclass(frozen=True)
class ScoreComponents:
    gap_points: int
    exception_points: int
    personal_points: int
    total: int


@dataclass(frozen=True)
class RiskWarning:
    code: str
    severity: str
    message_en: str
    message_hi: str


@dataclass(frozen=True)
class RiskReport:
    risk_score: int
    band: str
    gap_by_month: tuple[MonthGap, ...]
    warnings: tuple[RiskWarning, ...]
    components: ScoreComponents
    personal_pct: int
    open_exception_count: int


def percent(part: int, whole: int) -> int:
    """Rounded integer percent. Returns 0 when the denominator is zero."""
    if whole <= 0:
        return 0
    return (abs(part) * 100 + whole // 2) // whole


def monthly_upi_receipts(entries: tuple[Entry, ...] | list[Entry]) -> dict[str, int]:
    """UPI money *in*, grouped by ISO month. Non-UPI sources are excluded by design:
    the department's claim is built from the UPI rail, so our comparison must be too."""
    totals: dict[str, int] = {}
    for entry in entries:
        if entry.source_kind != "upi_csv" or entry.entry_type not in INFLOW_TYPES:
            continue
        month = entry.entry_date[:7]
        totals[month] = totals.get(month, 0) + entry.amount_paise
    return dict(sorted(totals.items()))


def personal_share_pct(entries: tuple[Entry, ...] | list[Entry]) -> int:
    upi = [entry for entry in entries if entry.source_kind == "upi_csv"]
    volume = sum(entry.amount_paise for entry in upi)
    personal = sum(entry.amount_paise for entry in upi if entry.personal)
    return percent(personal, volume)


def gap_by_month(received: dict[str, int], declared: dict[str, int]) -> tuple[MonthGap, ...]:
    months = sorted(set(received) | set(declared))
    gaps = []
    for month in months:
        got, said = received.get(month, 0), declared.get(month, 0)
        gaps.append(MonthGap(month, got, said, got - said, percent(got - said, got)))
    return tuple(gaps)


def score_components(gap_pct: int, open_exception_count: int, personal_pct: int) -> ScoreComponents:
    gap = min(max(gap_pct, 0), GAP_CAP_PCT) * GAP_WEIGHT // GAP_CAP_PCT
    exceptions = min(max(open_exception_count, 0), EXCEPTION_CAP) * EXCEPTION_WEIGHT // EXCEPTION_CAP
    personal = min(max(personal_pct, 0), PERSONAL_CAP_PCT) * PERSONAL_WEIGHT // PERSONAL_CAP_PCT
    return ScoreComponents(gap, exceptions, personal, min(gap + exceptions + personal, 100))


def band(score: int) -> str:
    if score >= HIGH_BAND:
        return "high"
    if score >= WATCH_BAND:
        return "watch"
    return "low"


def build_warnings(gaps: tuple[MonthGap, ...], received: dict[str, int]) -> tuple[RiskWarning, ...]:
    warnings: list[RiskWarning] = []
    months = sorted(received)
    for previous, current in zip(months, months[1:]):
        before, after = received[previous], received[current]
        if before > 0 and percent(after - before, before) > MOM_SPIKE_PCT and after > before:
            jump = percent(after - before, before)
            warnings.append(RiskWarning(
                "mom_spike", "high",
                f"UPI receipts rose {jump}% from {previous} to {current} — a spike this size draws scrutiny.",
                f"{previous} से {current} तक UPI प्राप्ति {jump}% बढ़ी — इतनी बड़ी उछाल जाँच खींचती है।",
            ))
    annualized = sum(received.values()) * 12 // max(len(received), 1)
    if annualized * 100 >= GST_REGISTRATION_THRESHOLD_PAISE * THRESHOLD_PROXIMITY_PCT:
        warnings.append(RiskWarning(
            "registration_threshold", "high",
            f"Annualized receipts of {format_paise(annualized)} are near the {format_paise(GST_REGISTRATION_THRESHOLD_PAISE)} registration threshold.",
            f"वार्षिक अनुमानित प्राप्ति {format_paise(annualized)} है, जो {format_paise(GST_REGISTRATION_THRESHOLD_PAISE)} की पंजीकरण सीमा के पास है।",
        ))
    if gaps and gaps[-1].gap_paise > 0:
        latest = gaps[-1]
        warnings.append(RiskWarning(
            "declared_gap", "medium",
            f"{latest.month}: {format_paise(latest.gap_paise)} more received than declared ({latest.gap_pct}%).",
            f"{latest.month}: घोषित से {format_paise(latest.gap_paise)} अधिक प्राप्त हुआ ({latest.gap_pct}%)।",
        ))
    return tuple(warnings)


def assess(
    entries: tuple[Entry, ...] | list[Entry],
    declared_by_month: dict[str, int],
    open_exception_count: int,
    history: dict[str, int] | None = None,
) -> RiskReport:
    """`history` supplies receipts for months that predate the uploaded sources."""
    received = {**(history or {}), **monthly_upi_receipts(entries)}
    received = dict(sorted(received.items()))
    gaps = gap_by_month(received, declared_by_month)
    latest_gap_pct = gaps[-1].gap_pct if gaps else 0
    personal_pct = personal_share_pct(entries)
    components = score_components(latest_gap_pct, open_exception_count, personal_pct)
    return RiskReport(
        risk_score=components.total,
        band=band(components.total),
        gap_by_month=gaps,
        warnings=build_warnings(gaps, received),
        components=components,
        personal_pct=personal_pct,
        open_exception_count=open_exception_count,
    )


def assess_sample_data(root: Path, result: ReconciliationResult, open_exception_count: int | None = None) -> RiskReport:
    """Risk for the seeded demo store.

    July is computed from the reconciled ledger. Earlier months predate the uploaded
    sources, so their receipts and every month's declared turnover come from the
    committed `fixtures/risk_history.json` — seeded data, never invented at runtime.
    """
    seed = json.loads((root / "fixtures" / "risk_history.json").read_text(encoding="utf-8"))
    count = len(result.exceptions) if open_exception_count is None else open_exception_count
    return assess(
        entries=result.ledger_entries,
        declared_by_month={month: int(value) for month, value in seed["declared_paise"].items()},
        open_exception_count=count,
        history={month: int(value) for month, value in seed["prior_month_receipts_paise"].items()},
    )
