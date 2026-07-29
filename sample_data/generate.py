#!/usr/bin/env python3
"""Deterministically generate PakkaHisaab's committed Day 2.5 demo artifacts."""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FONT_PATH = ROOT / "fonts" / "Kalam-Regular.ttf"
RNG = random.Random(73026)


@dataclass(frozen=True)
class KhaataRow:
    party: str
    description: str
    amount_rupees: int
    entry_type: str


KHAATA_ONE = (
    KhaataRow("रमेश / Ramesh", "उधार दिया / credit", 2500, "credit_given"),
    KhaataRow("Mehta Kirana Shop", "supplier invoice", 4800, "purchase"),
    KhaataRow("Milk Booth", "दूध", 1200, "purchase"),
    KhaataRow("Asha Stores", "masala stock", 1730, "purchase"),
    KhaataRow("Cash Sale", "बिक्री", 3500, "sale"),
    KhaataRow("Mohan", "cash received", 1000, "payment_in"),
    KhaataRow("किराया / Rent", "July rent", 3000, "payment_out"),
    KhaataRow("Misc.", "छोटा खर्च", 1000, "payment_out"),
)
KHAATA_ONE_SUM = sum(row.amount_rupees for row in KHAATA_ONE)
KHAATA_ONE_WRITTEN_TOTAL = 18_930

KHAATA_TWO = (
    ("Shiv Oil", 3200, 160),
    ("सूरज दाल", 1850, 93),
    ("Kumar Rice", 4600, 230),
    ("चाय पत्ती", 1250, 63),
    ("Ramesh Snacks", 980, 49),
    ("Milk Booth", 720, 36),
)

# INV-231 is a PHOTOGRAPH of a real printed invoice, committed at
# sample_data/mehta_inv_231.jpg. SPEC §11 offers photographed staged pages as an
# alternative to rendered ones, and a real document is stronger evidence for the demo's
# headline exception. It is listed here so GROUND_TRUTH.md and the ledger stay in sync with
# it, but it is deliberately NOT redrawn — see RENDERED_INVOICES below.
PHOTOGRAPHED_INVOICE = ("mehta_inv_231.jpg", "INV-231", "Mehta Kirana Shop", "2026-07-12", 4800)

RENDERED_INVOICES = (
    ("kumar_inv_232.jpg", "INV-232", "Kumar Suppliers", "2026-07-10", 7200),
    ("kumar_inv_233.jpg", "INV-233", "Kumar Suppliers", "2026-07-11", 7200),
)

# Ground-truth order: the photographed invoice first, then the rendered duplicate pair.
INVOICES = (PHOTOGRAPHED_INVOICE, *RENDERED_INVOICES)
PERSONAL_UPI_ROWS = (
    ("2026-07-03", "Rahul Bhai transfer (personal)", "15000.00", "UPI-PERS-15000"),
    ("2026-07-07", "Family pharmacy (personal)", "-2500.00", "UPI-PERS-2500"),
    ("2026-07-18", "Home electricity (personal)", "-1800.00", "UPI-PERS-1800"),
    ("2026-07-25", "Personal mobile recharge", "-1200.00", "UPI-PERS-1200"),
)
MATCHING_UPI_ROWS = (
    ("2026-07-10", "Kumar Suppliers", "-7200.00", "UPI-KUMAR-0710"),
    ("2026-07-11", "Kumar Suppliers", "-7200.00", "UPI-KUMAR-0711"),
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def _paper(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height), "#f8efd7")
    pixels = image.load()
    for _ in range((width * height) // 180):
        x, y = RNG.randrange(width), RNG.randrange(height)
        base = RNG.choice((222, 230, 238))
        pixels[x, y] = (base, max(0, base - 7), max(0, base - 25))
    return image


def _save_handwritten(image: Image.Image, destination: Path, angle: float) -> None:
    image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="#f8efd7").save(
        destination, "JPEG", quality=88, optimize=True
    )


def _draw_khaata_one(destination: Path) -> None:
    image = _paper(1600, 2200)
    draw = ImageDraw.Draw(image)
    title = _font(74)
    header = _font(42)
    row_font = _font(40)
    ink = "#2e251e"
    draw.text((130, 105), "Sharma Kirana  |  खाताबही", font=title, fill=ink)
    draw.text((130, 205), "July 2026 • Page 1", font=header, fill="#6e4f33")
    y = 330
    columns = (130, 615, 1020)
    for label, x in zip(("Party / पार्टी", "Details", "₹ Amount"), columns):
        draw.text((x, y), label, font=header, fill="#8a4a22")
    draw.line((115, y + 70, 1490, y + 70), fill="#b87333", width=4)
    y += 110
    for index, row in enumerate(KHAATA_ONE, start=1):
        jitter = RNG.randint(-7, 7)
        draw.text((columns[0], y + jitter), f"{index}. {row.party}", font=row_font, fill=ink)
        draw.text((columns[1], y - jitter), row.description, font=row_font, fill=ink)
        draw.text((columns[2], y + jitter), f"₹ {row.amount_rupees:,}", font=row_font, fill=ink)
        draw.line((115, y + 66, 1490, y + 66), fill="#d6b98a", width=2)
        y += 150
    draw.text((155, y + 80), "लिखा हुआ कुल / Written total:", font=header, fill="#9b1c1c")
    draw.text((1030, y + 80), f"₹ {KHAATA_ONE_WRITTEN_TOTAL:,}", font=title, fill="#9b1c1c")
    _save_handwritten(image, destination, angle=-0.7)


def _draw_khaata_two(destination: Path) -> None:
    image = _paper(1600, 1900)
    draw = ImageDraw.Draw(image)
    title, header, row_font = _font(72), _font(42), _font(40)
    draw.text((130, 110), "Sharma Kirana  |  खाता पन्ना 2", font=title, fill="#2e251e")
    draw.text((130, 210), "New GST column • July 2026", font=header, fill="#8a4a22")
    y, columns = 340, (130, 680, 1050, 1320)
    for label, x in zip(("Party", "Item", "₹ Amount", "GST"), columns):
        draw.text((x, y), label, font=header, fill="#8a4a22")
    draw.line((115, y + 70, 1490, y + 70), fill="#b87333", width=4)
    y += 115
    for index, (party, amount, gst) in enumerate(KHAATA_TWO, start=1):
        draw.text((columns[0], y), f"{index}. {party}", font=row_font, fill="#2e251e")
        draw.text((columns[1], y), "stock", font=row_font, fill="#2e251e")
        draw.text((columns[2], y), f"₹ {amount:,}", font=row_font, fill="#2e251e")
        draw.text((columns[3], y), f"₹ {gst}", font=row_font, fill="#9b1c1c")
        draw.line((115, y + 66, 1490, y + 66), fill="#d6b98a", width=2)
        y += 160
    _save_handwritten(image, destination, angle=0.55)


def _draw_invoice(destination: Path, number: str, party: str, invoice_date: str, amount: int) -> None:
    image = Image.new("RGB", (1300, 1700), "#fffdf7")
    draw = ImageDraw.Draw(image)
    title, body, total = _font(72), _font(42), _font(60)
    draw.rectangle((55, 55, 1245, 1645), outline="#ae6d32", width=6)
    draw.text((110, 120), "SHARMA KIRANA", font=title, fill="#592f18")
    draw.text((110, 220), "Tax invoice / बिक्री बिल", font=body, fill="#7c5a3c")
    draw.text((110, 360), f"Invoice: {number}", font=body, fill="#2e251e")
    draw.text((110, 430), f"Date: {invoice_date}", font=body, fill="#2e251e")
    draw.text((110, 500), f"Supplier: {party}", font=body, fill="#2e251e")
    draw.line((100, 610, 1200, 610), fill="#ae6d32", width=4)
    draw.text((120, 680), "Description", font=body, fill="#7c5a3c")
    draw.text((930, 680), "Amount", font=body, fill="#7c5a3c")
    draw.text((120, 780), "Kiranas & stock supply", font=body, fill="#2e251e")
    draw.text((930, 780), f"₹ {amount:,}", font=body, fill="#2e251e")
    draw.line((100, 880, 1200, 880), fill="#ae6d32", width=4)
    draw.text((620, 980), "Grand total", font=body, fill="#7c5a3c")
    draw.text((865, 1060), f"₹ {amount:,}", font=total, fill="#592f18")
    draw.text((110, 1510), "Computer generated invoice • Thank you", font=body, fill="#7c5a3c")
    image.save(destination, "JPEG", quality=90, optimize=True)


def _upi_rows() -> list[tuple[str, str, str, str]]:
    rows = list(MATCHING_UPI_ROWS + PERSONAL_UPI_ROWS)
    merchants = ("Daily cash sale", "Vegetable Market", "Metro Wholesale", "Tea Stall", "Walk-in sale", "Electricity bill")
    start = date(2026, 7, 1)
    for index in range(54):
        day = start + timedelta(days=index % 31)
        merchant = merchants[index % len(merchants)]
        amount = 600 + ((index * 137) % 4300)
        signed = amount if index % 3 else -amount
        rows.append((day.isoformat(), merchant, f"{signed:.2f}", f"UPI-JUL-{index + 1:04d}"))
    assert len(rows) == 60
    return rows


def _write_upi_csv(destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Txn Date", "Transaction Details", "Amount", "UPI Ref"])
        writer.writeheader()
        for txn_date, detail, amount, reference in _upi_rows():
            writer.writerow({"Txn Date": txn_date, "Transaction Details": detail, "Amount": amount, "UPI Ref": reference})


def _ground_truth() -> str:
    khaata_rows = "\n".join(
        f"| {index} | {row.party} | ₹{row.amount_rupees:,} | {row.entry_type} |"
        for index, row in enumerate(KHAATA_ONE, start=1)
    )
    invoice_rows = "\n".join(f"| {number} | {party} | {invoice_date} | ₹{amount:,} |" for _, number, party, invoice_date, amount in INVOICES)
    return f"""# PakkaHisaab sample-data ground truth

Generated by `python sample_data/generate.py` with deterministic seed `73026`.
Do not edit generated values by hand; change the constants in `generate.py` and rerun.

## Khaata page 1 — deliberate arithmetic error

| Row | Party | Amount | Entry type |
|---|---|---:|---|
{khaata_rows}

- Extracted row sum: **₹{KHAATA_ONE_SUM:,}** (1,873,000 paise)
- Written total on image: **₹{KHAATA_ONE_WRITTEN_TOTAL:,}** (1,893,000 paise)
- Deliberate difference: **₹200** (20,000 paise), expected `arithmetic_error`.

## Invoice truth

| Invoice | Party | Date | Amount |
|---|---|---|---:|
{invoice_rows}

- `INV-231` / Mehta Kirana Shop for **₹4,800** has no UPI payment: expected
  `unmatched_invoice`. Its source document is `mehta_inv_231.jpg`, a **photograph of a real
  printed invoice** (₹2,600 atta + ₹1,900 sunflower oil + ₹300 sugar = ₹4,800, so its own
  arithmetic is internally consistent — the deliberate arithmetic error lives on khaata
  page 1, not here). The generator never overwrites this file.
- `INV-232` and `INV-233` are same-party/same-amount invoices one day apart: expected `possible_duplicate`.

## July PhonePe export

- Exactly **60** data rows, with PhonePe-style `Txn Date`, `Transaction Details`, `Amount`, and `UPI Ref` headers.
- `UPI-KUMAR-0710` and `UPI-KUMAR-0711` pay the two ₹7,200 Kumar invoices.
- No row pays Mehta Kirana Shop / `INV-231` for ₹4,800.
- Four personal rows: `UPI-PERS-15000`, `UPI-PERS-2500`, `UPI-PERS-1800`, `UPI-PERS-1200`.
- `UPI-PERS-15000` is a **₹15,000 credit** from Rahul Bhai: expected `personal_vs_business`.

## Khaata page 2 schema-drift trigger

Six rows include a visible **GST** column. Their GST values are ₹160, ₹93, ₹230,
₹63, ₹49, and ₹36; this page is the explicit `gst_amount` schema-drift trigger.

## GST notice truth

The notice claims July UPI receipts of **₹1,05,264** — exactly the credit total in
`july_upi.csv` — versus the declared turnover of **₹71,000** held in
`fixtures/risk_history.json`. The **₹34,264** difference is what the risk radar shows
and what the notice asks about, so the seeded notice, CSV, and Kavach score all agree.
"""


def _write_notice(destination: Path) -> None:
    destination.write_text(
        "GST NOTICE — July 2026\n\n"
        "Our records indicate UPI receipts of ₹1,05,264 for July 2026 while your declared turnover is ₹71,000. "
        "Please explain the ₹34,264 difference and submit supporting books, invoices, and payment evidence.\n",
        encoding="utf-8",
    )


def generate(output: Path) -> None:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Bundled Kalam font missing: {FONT_PATH}")
    output.mkdir(parents=True, exist_ok=True)
    _draw_khaata_one(output / "khaata_page_1.jpg")
    _draw_khaata_two(output / "khaata_page_2.jpg")
    # Only the rendered invoices are drawn. The photographed one is real evidence; drawing
    # over it would replace a genuine document with a synthetic lookalike.
    for filename, number, party, invoice_date, amount in RENDERED_INVOICES:
        _draw_invoice(output / filename, number, party, invoice_date, amount)
    _write_upi_csv(output / "july_upi.csv")
    _write_notice(output / "gst_notice_sample.txt")
    (output / "GROUND_TRUTH.md").write_text(_ground_truth(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT, help="artifact directory (default: sample_data)")
    args = parser.parse_args()
    generate(args.output)
    print(f"Generated reproducible sample data in {args.output}")


if __name__ == "__main__":
    main()
