"""Regenerate the deterministic M3 golden result from committed seed inputs."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from engine.reconciler import reconcile_sample_data  # noqa: E402

result = reconcile_sample_data(ROOT / "sample_data")
payload = asdict(result)
(ROOT / "sample_data" / "fixtures" / "golden_m3.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
