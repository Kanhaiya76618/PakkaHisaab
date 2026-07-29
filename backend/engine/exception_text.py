"""Deterministic bilingual exception copy.

The Exception Agent in SPEC §7.3 uses a model to phrase exceptions. This module is
its model-free floor: every exception the engine detects gets a correct Hindi and
English summary and a `suggested_action` from the closed set, computed by code with
no network call. Demo mode therefore survives total API failure with real copy, and
`engine/` stays deterministic. A model may later enrich these strings; it may never
replace the number in them.
"""
from __future__ import annotations

SUGGESTED_ACTIONS = frozenset(
    {"create_entry", "merge_duplicates", "mark_personal", "adjust_amount", "ask_user"}
)

_ACTION_BY_KIND = {
    "unmatched_invoice": "create_entry",
    "possible_duplicate": "merge_duplicates",
    "arithmetic_error": "adjust_amount",
    "personal_vs_business": "mark_personal",
    "amount_mismatch": "adjust_amount",
}


def format_paise(amount_paise: int) -> str:
    """Render integer paise as Indian-grouped rupees. Integer math only — no floats."""
    sign = "-" if amount_paise < 0 else ""
    rupees, paise = divmod(abs(amount_paise), 100)
    digits = str(rupees)
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"{sign}₹{digits}.{paise:02d}"


def summarize(kind: str, amount_paise: int, party_name: str | None = None) -> tuple[str, str, str]:
    """Return (summary_en, summary_hi, suggested_action) for a detected exception."""
    money = format_paise(amount_paise)
    party = party_name or "this party"
    party_hi = party_name or "इस पार्टी"
    if kind == "unmatched_invoice":
        return (
            f"{money} invoice from {party} has no matching payment in any source.",
            f"{party_hi} का {money} का बिल किसी भी स्रोत में भुगतान से नहीं मिला।",
            _ACTION_BY_KIND[kind],
        )
    if kind == "possible_duplicate":
        return (
            f"Two {money} records for {party} appear one day apart in different sources.",
            f"{party_hi} के {money} के दो रिकॉर्ड अलग-अलग स्रोतों में एक दिन के अंतर पर हैं।",
            _ACTION_BY_KIND[kind],
        )
    if kind == "arithmetic_error":
        return (
            f"The khaata page total differs from the sum of its rows by {money}.",
            f"खाता पेज का लिखा जोड़ उसकी पंक्तियों के योग से {money} अलग है।",
            _ACTION_BY_KIND[kind],
        )
    if kind == "personal_vs_business":
        return (
            f"A {money} transfer looks personal but sits in the business account.",
            f"{money} का ट्रांसफर निजी लगता है पर व्यापार खाते में दर्ज है।",
            _ACTION_BY_KIND[kind],
        )
    if kind == "amount_mismatch":
        return (
            f"A matched pair differs by {money} — likely a digit read incorrectly.",
            f"मिलान की गई जोड़ी में {money} का अंतर है — शायद कोई अंक गलत पढ़ा गया।",
            _ACTION_BY_KIND[kind],
        )
    return (
        f"{money} needs your review.",
        f"{money} की जाँच आपको करनी है।",
        "ask_user",
    )
