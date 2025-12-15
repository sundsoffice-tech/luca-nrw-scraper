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
    assert report["invalid_email"] >= 0
    assert report["invalid_phone"] >= 0
    assert "dedup_reasons" in report


def test_dedup_fallback_name_phone():
    rows = [
        {"name": "Alex Example", "rolle": "Lead", "email": "", "telefon": "+49 221 1234567"},
        {"name": "Alex   Example", "rolle": "Lead", "email": "", "telefon": "+49 (221) 1234567"},
    ]

    deduped, removed = deduplicate_by_email_domain(rows)

    assert len(deduped) == 1
    assert removed == 1


def test_validate_dataset_reports_categories():
    rows = [
        {"name": "No Contact", "rolle": "Lead", "email": "", "telefon": "  "},
        {"name": "Bad Email", "rolle": "Lead", "email": "foo@", "telefon": ""},
        {"name": "Bad Phone", "rolle": "Lead", "email": "", "telefon": "123"},
    ]

    _, report = validate_dataset(rows)

    assert report["missing_contact"] == 1
    assert report["invalid_email"] == 1
    assert report["invalid_phone"] == 1


def test_min_confidence_filters():
    rows = [
        {"name": "Low Phone Conf", "rolle": "Lead", "email": "a@example.com", "telefon": "0176 111111", "phone_confidence": 10},
        {"name": "Low Email Conf", "rolle": "Lead", "email": "b@example.com", "email_confidence": 5, "telefon": "0176 222222"},
        {"name": "Good", "rolle": "Lead", "email": "c@example.com", "telefon": "0176 333333", "phone_confidence": 90, "email_confidence": 90},
    ]

    final_rows, _ = clean_and_validate_leads(
        rows,
        verbose=False,
        min_confidence_phone=20,
        min_confidence_email=10,
    )

    assert [r["name"] for r in final_rows] == ["Good"]


def test_validate_dataset_basic():
    pytest.skip("wird in späteren Tickets implementiert")
