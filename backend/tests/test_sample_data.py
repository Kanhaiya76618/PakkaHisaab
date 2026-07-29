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
        "kumar_inv_232.jpg",
        "kumar_inv_233.jpg",
        "july_upi.csv",
        "gst_notice_sample.txt",
        "GROUND_TRUTH.md",
    ):
        assert (tmp_path / filename).is_file(), filename

    # INV-231 is a photograph of a real printed invoice, not a rendered artifact, so the
    # generator must not produce it — see the next test for the invariant that matters.
    assert not (tmp_path / "mehta_inv_231.jpg").exists()

    with (tmp_path / "july_upi.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 60
    assert sum(int(row["Amount"] == "15000.00") for row in rows) >= 1
    truth = (tmp_path / "GROUND_TRUTH.md").read_text(encoding="utf-8")
    assert "₹18,730" in truth
    assert "₹18,930" in truth
    assert "₹4,800" in truth


def test_photographed_invoice_is_real_and_the_generator_never_overwrites_it() -> None:
    """INV-231 is a photograph of a real printed invoice (SPEC §11 permits staged
    photographs). Regenerating sample data must leave it byte-identical, or a routine
    `python sample_data/generate.py` would silently replace real evidence with a synthetic
    drawing — and the Evidence Passport would then cite a document that never existed."""
    import hashlib

    photo = ROOT / "sample_data" / "mehta_inv_231.jpg"
    assert photo.is_file(), "the photographed invoice is missing from sample_data/"

    digest = hashlib.sha256(photo.read_bytes()).hexdigest()
    synthetic = (ROOT / "sample_data" / "kumar_inv_232.jpg").stat().st_size
    assert photo.stat().st_size > synthetic, "a real photo should be larger than a rendered one"
    assert photo.read_bytes()[:3] == b"\xff\xd8\xff", "expected a JPEG"

    subprocess.run([sys.executable, str(GENERATOR)], check=True)
    assert hashlib.sha256(photo.read_bytes()).hexdigest() == digest, "generator overwrote the photograph"


def test_seeded_unmatched_invoice_names_the_supplier_printed_on_the_photograph() -> None:
    """The ledger party must be the supplier the physical invoice actually names,
    otherwise the Evidence Passport shows one name beside a photo showing another."""
    from engine.reconciler import reconcile_sample_data

    result = reconcile_sample_data(ROOT / "sample_data")
    invoice = next(item for item in result.ledger_entries if item.id == "invoice-INV-231")
    assert invoice.party_name == "Mehta Kirana Shop"
    assert invoice.amount_paise == 480_000
    assert invoice.entry_date == "2026-07-12"

    unmatched = [item for item in result.exceptions if item.kind == "unmatched_invoice"]
    assert len(unmatched) == 1
    assert unmatched[0].party_name == "Mehta Kirana Shop"
    assert "Mehta Kirana Shop" in unmatched[0].summary_en
    assert "Mehta Kirana Shop" in unmatched[0].summary_hi


def test_ground_truth_records_the_photograph_as_the_invoice_source() -> None:
    truth = (ROOT / "sample_data" / "GROUND_TRUTH.md").read_text(encoding="utf-8")
    assert "mehta_inv_231.jpg" in truth
    assert "Mehta Kirana Shop" in truth
    assert "photograph" in truth.lower()
