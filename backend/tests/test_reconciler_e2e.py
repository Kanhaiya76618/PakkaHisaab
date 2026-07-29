from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from engine.reconciler import reconcile_sample_data
from engine.accounting import store_total_paise


ROOT = Path(__file__).resolve().parents[2]


def test_generated_demo_pipeline_has_exact_seeded_exceptions_and_totals() -> None:
    result = reconcile_sample_data(ROOT / "sample_data")
    expected = json.loads((ROOT / "sample_data" / "fixtures" / "expected_m3.json").read_text())
    golden = json.loads((ROOT / "sample_data" / "fixtures" / "golden_m3.json").read_text())

    assert [exception.kind for exception in result.exceptions] == expected["exception_kinds"]
    assert result.exceptions[0].related_entry_ids == ("invoice-INV-231",)
    assert result.exceptions[1].related_entry_ids == ("invoice-INV-232", "invoice-INV-233")
    assert result.exceptions[2].amount_paise == expected["arithmetic_error_paise"]
    assert result.exceptions[3].related_entry_ids == (expected["personal_entry_id"],)
    assert result.ledger_total_paise == store_total_paise(result.ledger_entries)
    assert reconcile_sample_data(ROOT / "sample_data") == result
    assert json.loads(json.dumps(asdict(result), sort_keys=True)) == golden
    assert all(isinstance(item.amount_paise, int) for item in result.ledger_entries)
    assert all(match.match_rule and match.match_score >= 0.8 for match in result.matches)


def _entry(identifier: str, kind: str, entry_type: str, party: str, paise: int, day: str, ref: str | None = None):
    from engine.types import Entry

    return Entry(id=identifier, source_id=identifier, entry_type=entry_type, party_name=party, amount_paise=paise, entry_date=day, upi_ref=ref, source_kind=kind)


def test_unmatched_invoice_exception_is_derived_from_matching_not_scripted() -> None:
    """A paid invoice must produce no exception; only an unpaid one may."""
    from engine.reconciler import reconcile

    paid = reconcile([
        _entry("invoice-A", "invoice", "purchase", "Gupta Traders", 480000, "2026-07-12"),
        _entry("upi-A", "upi_csv", "payment_out", "Gupta Traders", 480000, "2026-07-12", "UPI-A"),
    ])
    assert [item.kind for item in paid.exceptions] == []

    unpaid = reconcile([
        _entry("invoice-A", "invoice", "purchase", "Gupta Traders", 480000, "2026-07-12"),
        _entry("upi-A", "upi_csv", "payment_out", "Someone Else", 990000, "2026-07-30", "UPI-A"),
    ])
    unmatched = [item for item in unpaid.exceptions if item.kind == "unmatched_invoice"]
    assert len(unmatched) == 1
    assert unmatched[0].related_entry_ids == ("invoice-A",)
    assert unmatched[0].amount_paise == 480000


def test_every_exception_carries_its_amount_and_a_bilingual_summary() -> None:
    result = reconcile_sample_data(ROOT / "sample_data")
    for exception in result.exceptions:
        assert exception.amount_paise > 0, f"{exception.kind} has no amount"
        assert exception.summary_en and exception.summary_hi, f"{exception.kind} is not bilingual"
        assert exception.summary_en != exception.summary_hi
        assert exception.suggested_action in {"create_entry", "merge_duplicates", "mark_personal", "adjust_amount", "ask_user"}


def test_seeded_unmatched_invoice_is_the_four_thousand_eight_hundred_bill() -> None:
    """INV-231, ₹4,800, dated 2026-07-12 — the invoice whose source document is the
    photograph at sample_data/mehta_inv_231.jpg."""
    result = reconcile_sample_data(ROOT / "sample_data")
    unmatched = [item for item in result.exceptions if item.kind == "unmatched_invoice"]
    assert len(unmatched) == 1
    assert unmatched[0].related_entry_ids == ("invoice-INV-231",)
    assert unmatched[0].amount_paise == 480000
    assert "4,800" in unmatched[0].summary_en


def test_only_personal_credits_into_the_business_account_raise_an_exception() -> None:
    """SPEC §10/§11: the flagged case is a personal *credit* sitting in the business
    account. Personal spending is still labelled, but it is not the notice risk."""
    from engine.reconciler import reconcile

    result = reconcile([
        _entry("upi-in", "upi_csv", "payment_in", "Rahul Bhai", 1500000, "2026-07-03", "UPI-PERS-15000"),
        _entry("upi-out", "upi_csv", "payment_out", "Family pharmacy", 250000, "2026-07-07", "UPI-PERS-2500"),
    ])
    from dataclasses import replace

    labelled = reconcile([
        replace(_entry("upi-in", "upi_csv", "payment_in", "Rahul Bhai", 1500000, "2026-07-03", "UPI-PERS-15000"), personal=True),
        replace(_entry("upi-out", "upi_csv", "payment_out", "Family pharmacy", 250000, "2026-07-07", "UPI-PERS-2500"), personal=True),
    ])
    assert [item.kind for item in result.exceptions] == []
    personal = [item for item in labelled.exceptions if item.kind == "personal_vs_business"]
    assert len(personal) == 1
    assert personal[0].related_entry_ids == ("upi-in",)


def test_all_four_seeded_personal_rows_are_labelled_personal() -> None:
    result = reconcile_sample_data(ROOT / "sample_data")
    personal_entries = [item for item in result.ledger_entries if item.personal]
    assert len(personal_entries) == 4
    assert sum(item.amount_paise for item in personal_entries) == 2_050_000
