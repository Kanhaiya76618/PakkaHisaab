"""Regression checks for reproducible Milestone 2.5 demo artifacts."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "sample_data" / "generate.py"


def test_generator_creates_the_specified_ground_truthed_artifacts(tmp_path: Path) -> None:
    subprocess.run([sys.executable, str(GENERATOR), "--output", str(tmp_path)], check=True)

    for filename in (
        "khaata_page_1.jpg",
        "khaata_page_2.jpg",
        "gupta_inv_231.jpg",
        "gupta_inv_232.jpg",
        "sharma_wholesale_078.jpg",
        "july_upi.csv",
        "gst_notice_sample.txt",
        "GROUND_TRUTH.md",
    ):
        assert (tmp_path / filename).is_file(), filename

    with (tmp_path / "july_upi.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 60
    assert sum(int(row["Amount"] == "15000.00") for row in rows) >= 1
    truth = (tmp_path / "GROUND_TRUTH.md").read_text(encoding="utf-8")
    assert "₹18,730" in truth
    assert "₹18,930" in truth
    assert "₹4,800" in truth
