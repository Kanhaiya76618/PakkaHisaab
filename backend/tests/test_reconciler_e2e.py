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
