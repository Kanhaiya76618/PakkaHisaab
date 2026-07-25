from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "backend" / "engine"


def test_engine_amounts_are_integer_paise_only() -> None:
    from engine.types import Entry

    entry = Entry(id="e1", source_id="s1", entry_type="sale", party_name="Cash", amount_paise=187_300, entry_date="2026-07-12")
    assert isinstance(entry.amount_paise, int)
    assert not isinstance(entry.amount_paise, bool)


def test_engine_has_no_float_money_conversion_or_openai_import() -> None:
    sources = "\n".join(path.read_text(encoding="utf-8") for path in ENGINE.rglob("*.py"))
    assert "float(" not in sources
    assert "openai" not in sources.lower()
