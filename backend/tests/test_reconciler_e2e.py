from __future__ import annotations

from pathlib import Path

from engine.reconciler import reconcile_sample_data


ROOT = Path(__file__).resolve().parents[2]


def test_generated_demo_pipeline_has_exact_seeded_exceptions_and_totals() -> None:
    result = reconcile_sample_data(ROOT / "sample_data")

    assert [exception.kind for exception in result.exceptions] == [
        "unmatched_invoice",
        "possible_duplicate",
        "arithmetic_error",
        "personal_vs_business",
    ]
    assert result.exceptions[0].related_entry_ids == ("invoice-INV-231",)
    assert result.exceptions[1].related_entry_ids == ("invoice-INV-232", "invoice-INV-233")
    assert result.exceptions[2].amount_paise == 20_000
    assert result.exceptions[3].related_entry_ids == ("upi-UPI-PERS-15000",)
    assert result.ledger_total_paise == 15_969_700
    assert all(isinstance(item.amount_paise, int) for item in result.ledger_entries)
    assert all(match.match_rule and match.match_score >= 0.8 for match in result.matches)
