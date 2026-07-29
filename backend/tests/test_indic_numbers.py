"""Hindi/Hinglish spoken-number parsing.

Measured justification for this module: Saaras v3 normalized the seeded voice note to
`₹2500` on 5 of 5 live calls, but the same sentence with different synthesis prosody came
back as `पच्चीस सौ` in words. A cashbook cannot depend on which one it gets.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from engine.indic_numbers import amount_paise_from_words, parse_number_words

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        # The colloquial hundreds multiplier — the exact form in SPEC §11's voice note.
        ("पच्चीस सौ", 2500),
        ("रमेश को पच्चीस सौ रुपये कैश दिए, याद रखना।", 2500),
        ("pachchees sau", 2500),
        # Standard multiplicative forms.
        ("चार हज़ार आठ सौ", 4800),
        ("चार हजार आठ सौ", 4800),
        ("पंद्रह हज़ार", 15000),
        ("दो हज़ार पांच सौ", 2500),
        ("सात सौ बीस", 720),
        ("एक लाख", 100000),
        # Idiomatic half-forms, integral throughout.
        ("ढाई हज़ार", 2500),
        ("डेढ़ हज़ार", 1500),
        # Plain small numbers.
        ("बीस", 20),
        ("nau", 9),
    ],
)
def test_spoken_numbers_parse_to_the_right_integer(spoken: str, expected: int) -> None:
    assert parse_number_words(spoken) == expected


@pytest.mark.parametrize("text", ["", "रमेश को कैश दिए", "no numbers here", "।।।"])
def test_text_without_a_number_yields_none_rather_than_a_guess(text: str) -> None:
    assert parse_number_words(text) is None


def test_amounts_are_returned_as_integer_paise() -> None:
    paise = amount_paise_from_words("पच्चीस सौ रुपये")
    assert paise == 250_000
    assert isinstance(paise, int)
    assert amount_paise_from_words("कुछ नहीं") is None


def test_module_is_model_free_and_float_free() -> None:
    source = (ROOT / "backend" / "engine" / "indic_numbers.py").read_text(encoding="utf-8")
    assert "openai" not in source.lower()
    assert "float(" not in source
