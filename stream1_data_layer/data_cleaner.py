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


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def deduplicate_by_email_domain(
    rows: List[Dict[str, Any]],
    *,
    with_reasons: bool = False,
) -> Tuple[List[Dict[str, Any]], int] | Tuple[List[Dict[str, Any]], int, Dict[str, int]]:
    """Entfernt künftig doppelte Leads basierend auf E-Mail-Domains (Fallback: Telefon/Name) und zählt die entfernten Duplikate."""
    dedup_rows: List[Dict[str, Any]] = []
    index_by_key: Dict[str, int] = {}
    removed_count = 0
    reason_counts: Dict[str, int] = {}

    for row in rows:
        email_raw = row.get("email", "")
        email_norm = email_raw.strip().lower() if isinstance(email_raw, str) else str(email_raw).strip().lower()
        email_domain = email_norm.split("@", 1)[1].strip() if "@" in email_norm else ""
        phone_norm = fix_phone_formatting(row.get("telefon"))
        name_norm = _normalize_name(row.get("name", ""))

        reason = "unknown"
        if email_norm:
            key = email_norm
            reason = "email"
        elif email_domain:
            key = email_domain
            reason = "domain"
        else:
            key_tuple = (name_norm, phone_norm or "")
            key = "|".join(key_tuple)
            reason = "name_phone" if any(key_tuple) else "phone"

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
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    if with_reasons:
        return dedup_rows, removed_count, reason_counts
    return dedup_rows, removed_count


def _validate_and_flags(row: Dict[str, Any]) -> Tuple[bool, bool, bool]:
    """Returns tuple of (is_valid, has_valid_email, has_valid_phone) and normalizes in-place."""
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

    return has_valid_phone or has_valid_email, has_valid_email, has_valid_phone


def validate_lead(row: Dict[str, Any]) -> bool:
    """Validiert später einzelne Leads gegen Mindestanforderungen (z. B. Kontaktfelder, Formate)."""
    is_valid, _, _ = _validate_and_flags(row)
    return is_valid


def validate_dataset(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Validiert künftig ein ganzes Dataset, behält gültige Leads und liefert Metriken zu Fehlerarten."""
    valid_rows: List[Dict[str, Any]] = []
    total = len(rows)
    invalid_email = 0
    invalid_phone = 0
    missing_contact = 0

    for row in rows:
        is_valid, has_valid_email, has_valid_phone = _validate_and_flags(row)
        has_email_raw = bool((row.get("email") or "").strip())
        has_phone_raw = bool(str(row.get("telefon") or "").strip())

        if is_valid:
            valid_rows.append(row)
        else:
            if has_email_raw and not has_valid_email:
                invalid_email += 1
            if has_phone_raw and not has_valid_phone:
                invalid_phone += 1
            if not has_email_raw and not has_phone_raw:
                missing_contact += 1

    report = {
        "total": total,
        "valid": len(valid_rows),
        "invalid": total - len(valid_rows),
        "invalid_email": invalid_email,
        "invalid_phone": invalid_phone,
        "missing_contact": missing_contact,
    }

    return valid_rows, report


def clean_and_validate_leads(
    raw_rows: List[Dict[str, Any]],
    verbose: bool = True,
    *,
    min_confidence_phone: Optional[float] = None,
    min_confidence_email: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Kapselt den gesamten Reinigungs- und Validierungs-Flow für eine Raw-Lead-Liste, optional mit Logs."""
    stage1_rows, removed_junk = filter_junk_rows(raw_rows)

    def _passes_conf(row: Dict[str, Any], keys: List[str], threshold: Optional[float]) -> bool:
        if threshold is None:
            return True
        for k in keys:
            if k in row:
                try:
                    return float(row.get(k)) >= float(threshold)
                except Exception:
                    continue
        return True

    filtered_conf: List[Dict[str, Any]] = []
    for r in stage1_rows:
        if "telefon" in r:
            r["telefon"] = fix_phone_formatting(r.get("telefon"))
        if not _passes_conf(r, ["phone_confidence", "confidence_phone"], min_confidence_phone):
            continue
        if not _passes_conf(r, ["email_confidence", "confidence_email"], min_confidence_email):
            continue
        filtered_conf.append(r)

    stage2_rows, removed_dupes, dedup_reasons = deduplicate_by_email_domain(filtered_conf, with_reasons=True)

    final_rows, val_report = validate_dataset(stage2_rows)

    report = {
        "input_total": len(raw_rows),
        "removed_junk": removed_junk,
        "removed_duplicates": removed_dupes,
        "dedup_reasons": dedup_reasons,
        **val_report,
    }

    return final_rows, report
