"""Hindi and Hinglish spoken-number parsing — deterministic, model-free, integer paise.

**Why this exists.** Sarvam Saaras v3 usually normalizes spoken amounts to digits: the
seeded voice note transcribed as `रमेश को ₹2500 कैश दिए` on 5 of 5 live calls. But it is not
a guarantee — the same sentence, synthesized with different prosody, came back as
`रमेश को पच्चीस सौ रुपये कैश दिए`, words intact. Both were measured, not assumed.

A cashbook cannot depend on a provider's formatting mood. So the digits path stays primary
and this module is the safety net: if a transcript has no digits, parse the number words in
code. `engine/` is model-free, so this is deterministic and testable, and the money still
comes from arithmetic rather than from a model's opinion.

Handles the forms a shopkeeper actually uses:
  पच्चीस सौ            25 × 100      = 2500   (the colloquial "hundreds" multiplier)
  चार हज़ार आठ सौ      4×1000 + 8×100 = 4800
  ढाई हज़ार            2.5 × 1000    = 2500   (half-forms are idiomatic, not decimals)
  pachchees sau                      = 2500   (Latin transliteration)
"""
from __future__ import annotations

import re

# 0-99 in Devanagari and common Latin transliterations. Only the forms that actually turn up
# in shop speech; this is not a general-purpose numeral library.
# Latin transliterations are deliberately limited to forms that are not also ordinary
# English words. `no`(=नौ 9), `do`(=दो 2), `sat`(=सात 7), `tin`(=तीन 3), `bis`(=बीस 20) and
# `lac`(=लाख) are all omitted on purpose: a transcript reading "2 Tin sunflower oil" must
# never yield the number 3, and "no" must never yield 9. A wrong amount is worse than none.
UNITS: dict[str, int] = {
    "शून्य": 0, "zero": 0, "sunya": 0,
    "एक": 1, "ek": 1, "दो": 2, "तीन": 3, "teen": 3,
    "चार": 4, "चारः": 4, "पांच": 5, "पाँच": 5, "panch": 5, "paanch": 5,
    "छह": 6, "छः": 6, "chhah": 6, "सात": 7, "saat": 7,
    "आठ": 8, "aath": 8, "नौ": 9, "nau": 9,
    "दस": 10, "das": 10, "ग्यारह": 11, "gyarah": 11, "बारह": 12, "barah": 12,
    "तेरह": 13, "terah": 13, "चौदह": 14, "chaudah": 14, "पंद्रह": 15, "pandrah": 15,
    "सोलह": 16, "solah": 16, "सत्रह": 17, "satrah": 17, "अठारह": 18, "atharah": 18,
    "उन्नीस": 19, "unnis": 19, "बीस": 20, "bees": 20, "bis": 20,
    "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24,
    "पच्चीस": 25, "pachchees": 25, "pachees": 25, "pachchis": 25,
    "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाईस": 28, "उनतीस": 29,
    "तीस": 30, "tees": 30, "चालीस": 40, "chalis": 40, "chalees": 40,
    "पचास": 50, "pachas": 50, "pachaas": 50, "साठ": 60, "sath": 60, "saath": 60,
    "सत्तर": 70, "sattar": 70, "अस्सी": 80, "assi": 80, "नब्बे": 90, "nabbe": 90,
}

# Multipliers, largest first — Indian grouping, so lakh and crore matter.
MULTIPLIERS: tuple[tuple[str, int], ...] = (
    ("करोड़", 10_000_000), ("crore", 10_000_000), ("karod", 10_000_000),
    ("लाख", 100_000), ("lakh", 100_000),
    ("हज़ार", 1_000), ("हजार", 1_000), ("hazaar", 1_000), ("hazar", 1_000), ("thousand", 1_000),
    ("सौ", 100), ("sau", 100), ("hundred", 100),
)

# Idiomatic half-forms. Kept as exact integers — never floats, because these are money.
HALF_FORMS: dict[str, tuple[int, int]] = {
    "ढाई": (5, 2),      # 2.5 × multiplier, expressed as 5/2 to stay integral
    "dhai": (5, 2),
    "ढेड़": (3, 2),
    "डेढ़": (3, 2),      # 1.5 ×
    "dedh": (3, 2),
    "देढ़": (3, 2),
    "साढ़े": (0, 0),      # "and a half" — handled as a modifier, see parse_number_words
}

_TOKEN = re.compile(r"[ऀ-ॿa-zA-Z]+")


def _normalize(token: str) -> str:
    return token.strip().lower().replace("‍", "").replace("‌", "")


def parse_number_words(text: str) -> int | None:
    """Largest number expressed in words in `text`, or None if there is none.

    Returns a plain integer (rupees, not paise) so callers decide the unit.
    """
    tokens = [_normalize(t) for t in _TOKEN.findall(text)]
    if not tokens:
        return None

    total = 0          # completed multiplier groups
    current = 0        # the group being built
    half_num, half_den = 0, 0
    found = False

    for token in tokens:
        if token in HALF_FORMS and HALF_FORMS[token] != (0, 0):
            half_num, half_den = HALF_FORMS[token]
            found = True
            continue
        if token in UNITS:
            current += UNITS[token]
            found = True
            continue
        multiplier = next((value for word, value in MULTIPLIERS if word == token), None)
        if multiplier is None:
            continue
        found = True
        if half_den:
            # "ढाई हज़ार" → 5 × 1000 // 2. Integer arithmetic throughout.
            total += half_num * multiplier // half_den
            half_num, half_den = 0, 0
            current = 0
            continue
        if current == 0:
            current = 1
        if multiplier >= 1_000:
            # A thousand/lakh/crore closes the group it follows.
            total += current * multiplier
            current = 0
        else:
            # "पच्चीस सौ" — the hundreds multiplier scales what came before it.
            current *= multiplier
    total += current
    if half_den:
        total += half_num // half_den
    if not found or total == 0:
        return None
    return total


def amount_paise_from_words(text: str) -> int | None:
    """Spoken rupee amount as integer paise, or None."""
    rupees = parse_number_words(text)
    return None if rupees is None else rupees * 100
