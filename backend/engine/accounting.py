"""Pure accounting identities used by reconciliation and risk reporting.

Store net cashflow is every inflow (`sale`, `payment_in`, `credit_received`)
minus every outflow (`purchase`, `payment_out`, `credit_given`). Notes are not
financial entries. Party balance is credit extended to a party plus credit
sales, minus payments received from that party. All inputs and outputs are
integer paise.
"""
from __future__ import annotations

from engine.types import Entry

INFLOWS = frozenset({"sale", "payment_in", "credit_received"})
OUTFLOWS = frozenset({"purchase", "payment_out", "credit_given"})


def store_total_paise(entries: tuple[Entry, ...] | list[Entry]) -> int:
    return sum(entry.amount_paise if entry.entry_type in INFLOWS else -entry.amount_paise if entry.entry_type in OUTFLOWS else 0 for entry in entries)


def party_balance_paise(entries: tuple[Entry, ...] | list[Entry], party_name: str) -> int:
    party = party_name.casefold().strip()
    relevant = [entry for entry in entries if (entry.party_name or "").casefold().strip() == party]
    return sum(entry.amount_paise if entry.entry_type in {"credit_given", "sale"} else -entry.amount_paise if entry.entry_type == "payment_in" else 0 for entry in relevant)
