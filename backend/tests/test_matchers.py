from __future__ import annotations

from engine.matchers import match_entries
from engine.types import Entry


def entry(id: str, *, party: str = "Gupta Traders", amount: int = 480_000, date: str = "2026-07-12", kind: str = "purchase", ref: str | None = None) -> Entry:
    return Entry(id=id, source_id=f"source-{id}", entry_type=kind, party_name=party, amount_paise=amount, entry_date=date, upi_ref=ref)


def assert_rule(left: Entry, right: Entry, rule: str, score: float) -> None:
    match = match_entries(left, right)
    assert match is not None
    assert (match.match_rule, match.match_score) == (rule, score)


def test_exact_ref_positive_and_negative() -> None:
    assert_rule(entry("i", ref="UPI-1"), entry("p", kind="payment_out", ref="UPI-1"), "exact_ref", 1.0)
    assert match_entries(entry("i", ref="UPI-1"), entry("p", kind="payment_out", ref="UPI-2")) is None


def test_exact_amount_date_positive_and_negative() -> None:
    assert_rule(entry("i"), entry("p", kind="payment_out"), "exact_amount_date", 1.0)
    assert match_entries(entry("i"), entry("p", kind="payment_out", date="2026-07-13")) is not None
    assert match_entries(entry("i"), entry("p", kind="payment_out", amount=480_100, date="2026-07-12")) is None


def test_amount_window_boundaries_and_negative() -> None:
    assert_rule(entry("i"), entry("p", kind="payment_out", date="2026-07-09"), "amount_within_window", 0.9)
    assert_rule(entry("i"), entry("p", kind="payment_out", date="2026-07-15"), "amount_within_window", 0.9)
    assert match_entries(entry("i"), entry("p", kind="payment_out", date="2026-07-08")) is None


def test_fuzzy_party_threshold_and_negative() -> None:
    assert_rule(entry("i", party="Gupta Traders"), entry("p", kind="payment_out", party="Gupta Traderz", date="2026-07-18"), "fuzzy_party_amount", 0.8)
    assert match_entries(entry("i", party="Gupta Traders"), entry("p", kind="payment_out", party="Unrelated Store", date="2026-07-12")) is None


def test_voice_confirmed_and_refund_pair() -> None:
    assert_rule(entry("voice", party="रमेश", amount=250_000, kind="payment_out"), entry("payment", party="Ramesh", amount=250_000, kind="credit_given"), "voice_confirmed", 0.85)
    assert match_entries(entry("refund", kind="payment_in", amount=50_000), entry("sale", kind="sale", amount=50_000)) is not None


def test_split_payments_are_not_merged() -> None:
    invoice = entry("invoice", amount=1_000_000)
    assert match_entries(invoice, entry("part-a", kind="payment_out", amount=500_000)) is None
    assert match_entries(invoice, entry("part-b", kind="payment_out", amount=500_000)) is None


def test_duplicate_date_boundary_one_day_but_not_two_days() -> None:
    from engine.reconciler import detect_duplicate_pairs

    first = entry("one", date="2026-07-10")
    assert detect_duplicate_pairs([first, entry("two", date="2026-07-11")]) == [("one", "two")]
    assert detect_duplicate_pairs([first, entry("three", date="2026-07-12")]) == []
