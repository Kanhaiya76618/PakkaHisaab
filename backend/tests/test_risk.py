"""Risk radar contract (SPEC §14). Deterministic, model-free, integer paise."""
from __future__ import annotations

from pathlib import Path

from engine.types import Entry

ROOT = Path(__file__).resolve().parents[2]


def _upi(identifier: str, entry_type: str, paise: int, day: str, personal: bool = False) -> Entry:
    return Entry(
        id=identifier, source_id="july-upi", entry_type=entry_type, party_name="Customer",
        amount_paise=paise, entry_date=day, upi_ref=identifier, source_kind="upi_csv", personal=personal,
    )


def test_monthly_receipts_count_only_upi_inflows_as_integer_paise() -> None:
    from engine.risk import monthly_upi_receipts

    received = monthly_upi_receipts([
        _upi("a", "payment_in", 500000, "2026-07-02"),
        _upi("b", "payment_in", 250000, "2026-07-20"),
        _upi("c", "payment_out", 900000, "2026-07-21"),
        _upi("d", "payment_in", 100000, "2026-06-11"),
        Entry("k1", "khaata-page-1", "sale", "Cash", 700000, "2026-07-05", source_kind="khaata_photo"),
    ])
    assert received == {"2026-06": 100000, "2026-07": 750000}
    assert all(isinstance(value, int) for value in received.values())


def test_gap_by_month_is_received_minus_declared_with_integer_percent() -> None:
    from engine.risk import gap_by_month

    gaps = gap_by_month({"2026-07": 10526400}, {"2026-07": 7100000})
    assert len(gaps) == 1
    assert gaps[0].month == "2026-07"
    assert gaps[0].upi_received_paise == 10526400
    assert gaps[0].declared_paise == 7100000
    assert gaps[0].gap_paise == 3426400
    assert gaps[0].gap_pct == 33
    assert isinstance(gaps[0].gap_pct, int)


def test_risk_score_is_the_documented_weighted_sum() -> None:
    from engine.risk import score_components

    components = score_components(gap_pct=33, open_exception_count=4, personal_pct=12)
    assert components.gap_points == 39
    assert components.exception_points == 20
    assert components.personal_points == 9
    assert components.total == 68


def test_risk_score_is_bounded_and_banded() -> None:
    from engine.risk import band, score_components

    assert score_components(gap_pct=500, open_exception_count=99, personal_pct=99).total == 100
    assert score_components(gap_pct=0, open_exception_count=0, personal_pct=0).total == 0
    assert band(20) == "low"
    assert band(40) == "watch"
    assert band(68) == "watch"
    assert band(70) == "high"


def test_warnings_fire_on_a_month_over_month_spike_above_forty_percent() -> None:
    from engine.risk import assess

    report = assess(
        entries=[_upi("a", "payment_in", 10000000, "2026-07-02")],
        declared_by_month={"2026-06": 6000000, "2026-07": 6000000},
        open_exception_count=0,
        history={"2026-06": 6500000},
    )
    codes = {warning.code for warning in report.warnings}
    assert "mom_spike" in codes
    assert all(warning.message_en and warning.message_hi for warning in report.warnings)


def test_seeded_demo_lands_in_the_amber_band_at_sixty_eight() -> None:
    """SPEC §14: the seeded store must read ≈68 Amber with the July gap visible."""
    from engine.reconciler import reconcile_sample_data
    from engine.risk import assess_sample_data

    result = reconcile_sample_data(ROOT / "sample_data")
    report = assess_sample_data(ROOT / "sample_data", result)

    assert report.risk_score == 68
    assert report.band == "watch"
    july = next(item for item in report.gap_by_month if item.month == "2026-07")
    assert july.upi_received_paise == 10526400
    assert july.gap_paise == 3426400
    assert len(report.gap_by_month) == 4
    assert report.warnings


def test_risk_module_is_model_free_and_float_free() -> None:
    source = (ROOT / "backend" / "engine" / "risk.py").read_text(encoding="utf-8")
    assert "openai" not in source.lower()
    assert "float(" not in source
