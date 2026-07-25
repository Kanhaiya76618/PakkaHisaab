"""Runs committed eval cases without network calls; results are deterministic."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

CASES = Path(__file__).parent / "cases" / "cases.json"

def run() -> dict[str, Any]:
    cases = json.loads(CASES.read_text())
    results = [{**case, "passed": case["expected"] == case["actual"], "cost_usd": 0} for case in cases]
    categories: dict[str, list[bool]] = {}
    for item in results: categories.setdefault(item["category"], []).append(item["passed"])
    return {"cases": results, "summary": {name: sum(values) / len(values) for name, values in categories.items()}, "count": len(results)}
