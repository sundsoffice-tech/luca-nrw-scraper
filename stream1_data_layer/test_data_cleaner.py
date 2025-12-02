import pytest

from stream1_data_layer.data_cleaner import (
    clean_and_validate_leads,
    deduplicate_by_email_domain,
    filter_junk_rows,
    fix_phone_formatting,
    validate_dataset,
    validate_lead,
    is_junk_row,
)


def test_filter_junk_rows_basic():
    rows = [
        {"name": "Valid Person", "rolle": "Lead", "email": "", "telefon": "   "},
        {"name": "Impressum", "rolle": "Kontakt", "email": "info@site.de", "telefon": "555"},
        {"name": "Carla Example", "rolle": "CEO", "email": "carla@example.com", "telefon": "+491234567"},
        {"name": "Team Support", "rolle": "Support", "email": None, "telefon": "+49111222333"},
    ]

    filtered_rows, removed_count = filter_junk_rows(rows)

    assert filtered_rows == [rows[2], rows[3]]
    assert removed_count == 2


def test_fix_phone_formatting_basic():
    assert fix_phone_formatting("0151 23456789") == "+4915123456789"
    assert fix_phone_formatting("+49 (221) 9876543") == "+492219876543"
    assert fix_phone_formatting("4.912345678e+09") == "+494912345678"
    assert fix_phone_formatting("030-1234567") == "+49301234567"
    assert fix_phone_formatting("123") is None
    assert fix_phone_formatting("") is None


def test_deduplicate_by_email_domain_basic():
    rows = [
        {"name": "First Email Only", "rolle": "Lead", "email": "dup@example.com", "telefon": ""},
        {"name": "Second With Phone", "rolle": "Lead", "email": "dup@example.com", "telefon": "0176 12345678"},
        {"name": "Third With Phone", "rolle": "Lead", "email": "same@example.com", "telefon": "+49 221 1234567"},
        {"name": "Fourth Same Phone", "rolle": "Lead", "email": "same@example.com", "telefon": "+49 (221) 1234567"},
    ]

    deduped, removed_count = deduplicate_by_email_domain(rows)

    assert [row["name"] for row in deduped] == ["Second With Phone", "Third With Phone"]
    assert removed_count == 2


def test_clean_and_validate_leads_pipeline():
    raw_rows = [
        {"name": "No Contact", "rolle": "Lead", "email": "", "telefon": "  "},
        {"name": "Primary", "rolle": "Lead", "email": "dup@example.com", "telefon": "0176 11111111"},
        {"name": "Secondary", "rolle": "Lead", "email": "dup@example.com", "telefon": ""},
        {"name": "Valid Unique", "rolle": "CEO", "email": "ceo@example.com", "telefon": "0301234567"},
        {"name": "Bad Phone Only", "rolle": "Lead", "email": "", "telefon": "123"},
    ]

    final_rows, report = clean_and_validate_leads(raw_rows, verbose=False)

    assert [row["name"] for row in final_rows] == ["Primary", "Valid Unique"]
    assert report["input_total"] == 5
    assert report["removed_junk"] == 1
    assert report["removed_duplicates"] == 1
    assert report["total"] == 3
    assert report["valid"] == 2
    assert report["invalid"] == 1


def test_validate_dataset_basic():
    pytest.skip("wird in späteren Tickets implementiert")
