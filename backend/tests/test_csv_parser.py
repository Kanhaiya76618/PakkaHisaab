from __future__ import annotations

from intake.csv_parser import parse_csv_text


def test_phonepe_export_normalizes_to_paise() -> None:
    rows = parse_csv_text(
        "Transaction Date,Transaction Details,Amount,UPI Ref\n"
        "12/07/2026,Gupta Traders,4,800.50,617234889912\n".replace("4,800.50", '"4,800.50"'),
        store_id="demo-store",
        source_document_id="phonepe-csv",
    )

    assert len(rows) == 1
    assert rows[0].amount_paise == 480050
    assert rows[0].entry_date == "2026-07-12"
    assert rows[0].upi_ref == "617234889912"
    assert rows[0].confidence == 1.0
    assert rows[0].extraction_model == "deterministic_parser"


def test_gpay_and_paytm_headers_are_detected() -> None:
    gpay = parse_csv_text(
        "Date,Name,Amount,Transaction ID\n2026-07-13,Ramesh,-2500.00,GPA-1\n",
        store_id="demo-store",
        source_document_id="gpay-csv",
    )
    paytm = parse_csv_text(
        "Txn Date,Merchant,Debit,Credit,UPI Ref\n13-07-2026,PhonePe,0,7250.25,PTM-9\n",
        store_id="demo-store",
        source_document_id="paytm-csv",
    )

    assert (gpay[0].entry_type, gpay[0].amount_paise, gpay[0].upi_ref) == ("payment_out", 250000, "GPA-1")
    assert (paytm[0].entry_type, paytm[0].amount_paise, paytm[0].upi_ref) == ("payment_in", 725025, "PTM-9")


def test_hindi_headers_are_detected() -> None:
    rows = parse_csv_text(
        "तारीख,नाम,राशि,यूपीआई रेफ\n2026/07/14,रमेश,₹2,500.00,UPI-HI-1\n".replace("₹2,500.00", '"₹2,500.00"'),
        store_id="demo-store",
        source_document_id="hindi-csv",
    )

    assert rows[0].party_name == "रमेश"
    assert rows[0].amount_paise == 250000
    assert rows[0].upi_ref == "UPI-HI-1"


def test_empty_file_returns_no_entries() -> None:
    assert parse_csv_text("", store_id="demo-store", source_document_id="empty") == []


def test_malformed_rows_are_skipped_without_losing_valid_rows() -> None:
    rows = parse_csv_text(
        "Date,Description,Amount\n2026-07-12,Valid payment,100.00\nnot-a-date,Bad amount,not-money\n",
        store_id="demo-store",
        source_document_id="mixed",
    )

    assert len(rows) == 1
    assert rows[0].party_name == "Valid payment"


def test_parser_never_returns_float_money() -> None:
    rows = parse_csv_text(
        "Date,Description,Amount\n2026-07-12,Decimal-safe,0.10\n",
        store_id="demo-store",
        source_document_id="money-guard",
    )

    assert rows[0].amount_paise == 10
    assert isinstance(rows[0].amount_paise, int)
    assert not any(isinstance(row.amount_paise, float) for row in rows)
