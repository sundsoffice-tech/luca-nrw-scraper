"""
Data-Cleaning-Funktionen für Leads: Junk-Filter, Telefon-Normalisierung,
Deduplication und Validierung werden hier zentral gebündelt.
"""

from typing import Any, Dict, List, Optional, Tuple
import re


def is_junk_row(row: Dict[str, Any]) -> bool:
    """Prüft, ob ein Lead anhand offensichtlicher Junk-Merkmale verworfen werden soll."""
    name = (row.get("name") or "").strip()
    rolle = (row.get("rolle") or "").strip()
    email = (row.get("email") or "").strip()
    telefon = str(row.get("telefon") or "").strip()
    tags = (row.get("tags") or "").strip()

    text = " ".join([name, rolle, tags]).lower()

    if not email and not telefon and not row.get("whatsapp_link"):
        return True

    junk_keywords = (
        "impressum",
        "datenschutz",
        "privacy",
        "agb",
        "cookies",
        "newsletter",
        "login",
        "anmeldung",
        "registrierung",
    )
    if any(k in text for k in junk_keywords):
        return True

    if name and len(name.split()) == 1 and len(name) <= 2:
        return True

    return False


def filter_junk_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Filtert Junk-Leads aus einer Liste und liefert bereinigte Daten plus Anzahl verworfener Einträge."""
    cleaned: List[Dict[str, Any]] = []
    removed = 0
    for r in rows:
        if is_junk_row(r):
            removed += 1
        else:
            cleaned.append(r)
    return cleaned, removed


def fix_phone_formatting(phone_input: Any) -> Optional[str]:
    """
    Normalisiert beliebige Telefon-Eingaben in ein einheitliches Format
    für Deutschland (E.164-ähnlich, +49...).
    - Akzeptiert auch E-Notation aus CSVs (z.B. 4.9123456789e+09).
    - Entfernt alle Nicht-Ziffern außer führendem '+'.
    - Ergänzt fehlende Landesvorwahl als +49.
    - Liefert None, wenn die Nummer offensichtlich unplausibel (zu kurz/lang) ist.
    """
    if not phone_input:
        return None

    phone_str = str(phone_input).strip()

    # Handle E-Notation (z.B. "4.913456789e+09")
    if "e" in phone_str.lower():
        try:
            phone_str = str(int(float(phone_str)))
        except Exception:
            return None

    # Clean & normalize
    phone_clean = re.sub(r"[^\d+]", "", phone_str)

    # German handling
    if phone_clean.startswith("0"):
        phone_clean = "+49" + phone_clean[1:]
    elif not phone_clean.startswith("+"):
        phone_clean = "+49" + phone_clean

    # Validate length
    digit_only = re.sub(r"[^\d]", "", phone_clean)
    if len(digit_only) < 9 or len(digit_only) > 15:
        return None

    return phone_clean


def deduplicate_by_email_domain(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Entfernt künftig doppelte Leads basierend auf E-Mail-Domains und zählt die entfernten Duplikate."""
    dedup_rows: List[Dict[str, Any]] = []
    index_by_key: Dict[str, int] = {}
    removed_count = 0

    for row in rows:
        email_raw = row.get("email", "")
        email_norm = email_raw.strip().lower() if isinstance(email_raw, str) else str(email_raw).strip().lower()
        email_domain = email_norm.split("@", 1)[1].strip() if "@" in email_norm else ""
        phone_norm = fix_phone_formatting(row.get("telefon"))

        if email_norm:
            key = email_norm
        elif email_domain:
            key = email_domain
        else:
            key = phone_norm or ""

        new_row = dict(row)
        if phone_norm is not None:
            new_row["telefon"] = phone_norm

        if key not in index_by_key:
            index_by_key[key] = len(dedup_rows)
            dedup_rows.append(new_row)
            continue

        existing_idx = index_by_key[key]
        existing_row = dedup_rows[existing_idx]
        existing_phone = existing_row.get("telefon")
        has_existing_phone = bool(str(existing_phone).strip()) if existing_phone is not None else False
        has_new_phone = phone_norm is not None and bool(str(phone_norm).strip())

        if has_new_phone and not has_existing_phone:
            dedup_rows[existing_idx] = new_row

        removed_count += 1

    return dedup_rows, removed_count


def validate_lead(row: Dict[str, Any]) -> bool:
    """Validiert später einzelne Leads gegen Mindestanforderungen (z. B. Kontaktfelder, Formate)."""
    email_raw = row.get("email", "")
    email_clean = email_raw.strip() if isinstance(email_raw, str) else str(email_raw).strip()
    phone_raw = row.get("telefon")
    phone_clean = None

    if phone_raw is not None and str(phone_raw).strip():
        phone_clean = fix_phone_formatting(phone_raw)
        row["telefon"] = phone_clean

    has_valid_phone = False
    if phone_clean:
        digit_only = re.sub(r"\D", "", phone_clean)
        has_valid_phone = 9 <= len(digit_only) <= 15

    has_valid_email = False
    if email_clean:
        if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_clean):
            has_valid_email = True
            row["email"] = email_clean

    return has_valid_phone or has_valid_email


def validate_dataset(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Validiert künftig ein ganzes Dataset, behält gültige Leads und liefert Metriken zu Fehlerarten."""
    valid_rows: List[Dict[str, Any]] = []
    total = len(rows)

    for row in rows:
        if validate_lead(row):
            valid_rows.append(row)

    report = {
        "total": total,
        "valid": len(valid_rows),
        "invalid": total - len(valid_rows),
    }

    return valid_rows, report


def clean_and_validate_leads(raw_rows: List[Dict[str, Any]], verbose: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Kapselt den gesamten Reinigungs- und Validierungs-Flow für eine Raw-Lead-Liste, optional mit Logs."""
    stage1_rows, removed_junk = filter_junk_rows(raw_rows)

    for r in stage1_rows:
        if "telefon" in r:
            r["telefon"] = fix_phone_formatting(r.get("telefon"))

    stage2_rows, removed_dupes = deduplicate_by_email_domain(stage1_rows)

    final_rows, val_report = validate_dataset(stage2_rows)

    report = {
        "input_total": len(raw_rows),
        "removed_junk": removed_junk,
        "removed_duplicates": removed_dupes,
        **val_report,
    }

    return final_rows, report
