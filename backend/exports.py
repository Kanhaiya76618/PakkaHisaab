"""CSV and PDF exports (SPEC §16).

The PDF is the "Month-End Evidence Pack": cover summary, ledger table, exception log
with resolutions, and the risk summary. Both formats are generated from the same live
reconciliation result, so an export can never disagree with the screen.
"""
from __future__ import annotations

import csv
import io

from engine.exception_text import format_paise
from engine.risk import RiskReport
from engine.types import ReconciliationResult
from evidence import evidence_files_for, evidence_for

CSV_COLUMNS = [
    "entry_id", "date", "party", "entry_type", "amount_paise", "amount",
    "source_kind", "evidence_files", "match_rule", "status",
]


def ledger_csv(result: ReconciliationResult) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for entry in result.ledger_entries:
        passport = evidence_for(result, entry.id) or {}
        writer.writerow({
            "entry_id": entry.id,
            "date": entry.entry_date,
            "party": entry.party_name or "",
            "entry_type": entry.entry_type,
            "amount_paise": entry.amount_paise,
            "amount": format_paise(entry.amount_paise),
            "source_kind": entry.source_kind,
            "evidence_files": evidence_files_for(result, entry.id),
            "match_rule": passport.get("match_rule") or "",
            "status": passport.get("status") or "",
        })
    return buffer.getvalue()


def evidence_pack_pdf(
    result: ReconciliationResult,
    exceptions: list[dict[str, object]],
    report: RiskReport,
    store_name: str = "Sharma Kirana Store",
) -> bytes:
    """Render the month-end pack. Imported lazily so the CSV path never pays for it."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, title=f"{store_name} — Month-End Evidence Pack",
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    story: list[object] = [
        Paragraph(f"{store_name} — Month-End Evidence Pack", styles["Title"]),
        Paragraph("PakkaHisaab · every number below links to the source that proves it.", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]

    open_count = sum(1 for item in exceptions if item.get("status") == "open")
    summary = [
        ["Ledger entries", str(len(result.ledger_entries))],
        ["Verified matches", str(len(result.matches))],
        ["Net position", format_paise(result.ledger_total_paise)],
        ["Exceptions (open / total)", f"{open_count} / {len(exceptions)}"],
        ["Notice risk score", f"{report.risk_score} / 100 ({report.band})"],
    ]
    story.append(_table(["Summary", "Value"], summary, Table, TableStyle, colors))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Exception log", styles["Heading2"]))
    if exceptions:
        rows = [[
            str(item.get("kind", "")),
            format_paise(int(item.get("amount_paise", 0) or 0)),
            str(item.get("status", "")),
            str(item.get("resolution") or "—"),
        ] for item in exceptions]
        story.append(_table(["Kind", "Amount", "Status", "Resolution"], rows, Table, TableStyle, colors))
    else:
        story.append(Paragraph("No exceptions were raised.", styles["Normal"]))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Notice risk", styles["Heading2"]))
    risk_rows = [[
        gap.month, format_paise(gap.upi_received_paise), format_paise(gap.declared_paise),
        format_paise(gap.gap_paise), f"{gap.gap_pct}%",
    ] for gap in report.gap_by_month]
    story.append(_table(["Month", "UPI received", "Declared", "Gap", "Gap %"], risk_rows, Table, TableStyle, colors))
    for warning in report.warnings:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"• {warning.message_en}", styles["Normal"]))
    story.append(PageBreak())

    story.append(Paragraph("Ledger with evidence", styles["Heading2"]))
    ledger_rows = [[
        entry.entry_date, (entry.party_name or "")[:28], entry.entry_type,
        format_paise(entry.amount_paise), (evidence_files_for(result, entry.id) or "—")[:34],
    ] for entry in result.ledger_entries]
    story.append(_table(["Date", "Party", "Type", "Amount", "Evidence"], ledger_rows, Table, TableStyle, colors))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "This pack is generated from verified records. Please review with a Chartered "
        "Accountant before filing.", styles["Italic"],
    ))

    document.build(story)
    return buffer.getvalue()


def _table(header: list[str], rows: list[list[str]], Table, TableStyle, colors):  # noqa: N803
    table = Table([header, *rows], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C1917")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#FAFAF7")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E7E5E4")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FDF6EC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table
