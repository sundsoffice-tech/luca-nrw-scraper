# -*- coding: utf-8 -*-
"""
Erweiterte Telefon-Extraktion mit Konfidenz-Scoring

Dieses Modul bietet fortgeschrittene Telefonnummern-Extraktion:
- Mehrere Regex-Patterns für verschiedene Formate
- Verschleierte Nummern (mit Worten, Sternen, etc.)
- Konfidenz-Score basierend auf Kontext
- Blacklist für Fake-Nummern
"""

import re
from typing import List, Tuple, Optional, Dict


# Erweiterte Regex-Patterns für deutsche Telefonnummern
PHONE_PATTERNS = [
    # Standard deutsche Mobilnummern
    r'(?:(?:\+49|0049|0)[\s.\-]?)?(1[5-7][0-9])[\s.\-]?(\d{3,4})[\s.\-]?(\d{3,5})',
    
    # Mit Vorwahl in Klammern
    r'\(0(1[5-7][0-9])\)[\s.\-]?(\d{3,4})[\s.\-]?(\d{3,5})',
    
    # Festnetz mit Vorwahl
    r'(?:(?:\+49|0049|0)[\s.\-]?)?(2[0-9]{2,4})[\s.\-]?(\d{5,8})',
    
    # WhatsApp-Nummern
    r'[Ww]hats?[Aa]pp[:\s]*(?:\+49|0049|0)?(1[5-7][0-9][\s.\-]?\d{3,4}[\s.\-]?\d{3,5})',
    
    # Telegram
    r'[Tt]elegram[:\s]*(?:\+49|0049|0)?(1[5-7][0-9][\s.\-]?\d{3,4}[\s.\-]?\d{3,5})',
    
    # Mit Beschreibung
    r'(?:[Tt]el(?:efon)?|[Mm]obil|[Hh]andy|[Rr]ückruf)[:\s./]*(?:\+49|0049|0)?(1[5-7][0-9][\s.\-]?\d{3,4}[\s.\-]?\d{3,5})',
    
    # Kompakte Formate ohne Trenner
    r'\b(?:\+49|0049|0)?1[5-7][0-9]\d{7,8}\b',
    
    # Mit Schrägstrich als Trenner
    r'(?:\+49|0049|0)?\s*1[5-7][0-9]\s*/\s*\d{3,4}\s*/\s*\d{3,5}',
]

# Verschleierte Nummern - Ersetzungsmuster
OBFUSCATION_REPLACEMENTS = [
    # Mit Worten
    (r'\bnull\b', '0'),
    (r'\beins\b', '1'),
    (r'\bzwei\b', '2'),
    (r'\bdrei\b', '3'),
    (r'\bvier\b', '4'),
    (r'\bfünf\b', '5'),
    (r'\bfuenf\b', '5'),
    (r'\bsechs\b', '6'),
    (r'\bsieben\b', '7'),
    (r'\bacht\b', '8'),
    (r'\bneun\b', '9'),
]

# Blacklist für Fake-Nummern
PHONE_BLACKLIST = [
    '0123456789',
    '1234567890',
    '0000000000',
    '1111111111',
    '2222222222',
    '3333333333',
    '4444444444',
    '5555555555',
    '6666666666',
    '7777777777',
    '8888888888',
    '9999999999',
    '0800',  # Kostenlose Nummern
    '0900',  # Premium-Nummern
    '0180',  # Service-Nummern
    '0137',  # Massenverkehr
    '0700',  # Persönliche Nummer
]


def extract_phones_advanced(text: str, html: str = "") -> List[Tuple[str, str, float]]:
    """
    Extrahiert Telefonnummern mit Konfidenz-Score
    
    Args:
        text: Sichtbarer Text-Inhalt
        html: HTML-Inhalt (optional, für zusätzlichen Kontext)
    
    Returns:
        Liste von Tupeln: (normalized_phone, raw_match, confidence)
    """
    results = []
    combined_text = text + " " + html if html else text
    text_lower = combined_text.lower()
    
    # 1. Standard-Patterns anwenden
    for pattern in PHONE_PATTERNS:
        try:
            for match in re.finditer(pattern, combined_text, re.IGNORECASE):
                raw = match.group(0)
                normalized = normalize_phone(raw)
                if normalized and is_valid_phone(normalized):
                    confidence = calculate_confidence(raw, combined_text)
                    results.append((normalized, raw, confidence))
        except re.error:
            # Ungültiges Pattern überspringen
            continue
    
    # 2. Verschleierte Nummern
    deobfuscated_phones = deobfuscate_phone(text_lower)
    for phone in deobfuscated_phones:
        normalized = normalize_phone(phone)
        if normalized and is_valid_phone(normalized):
            confidence = 0.6  # Niedrigere Konfidenz für verschleierte Nummern
            results.append((normalized, phone, confidence))
    
    # 2.5. ML-based confidence boosting
    try:
        # Import ML phone extractor for context-based scoring
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stream2_extraction_layer'))
        from ml_extractors import get_phone_extractor
        
        ml_extractor = get_phone_extractor()
        boosted_results = []
        for norm, raw, conf in results:
            # Use ML to refine confidence score
            ml_conf = ml_extractor.score_phone(norm, raw, combined_text)
            # Weighted average: 60% original, 40% ML
            final_conf = 0.6 * conf + 0.4 * ml_conf
            boosted_results.append((norm, raw, final_conf))
        results = boosted_results
    except Exception:
        pass  # Fallback to original confidence if ML not available
    
    # 3. Deduplizieren nach normalisierter Nummer
    seen = set()
    unique_results = []
    for norm, raw, conf in results:
        if norm not in seen:
            seen.add(norm)
            unique_results.append((norm, raw, conf))
    
    # Sortieren nach Konfidenz (höchste zuerst)
    unique_results.sort(key=lambda x: x[2], reverse=True)
    
    return unique_results


def normalize_phone(raw: str) -> str:
    """
    Normalisiert Telefonnummer zu +49...
    
    Args:
        raw: Rohe Telefonnummer
    
    Returns:
        Normalisierte Nummer im Format +49... oder leer bei Fehler
    """
    # Entferne alles außer Ziffern und +
    digits = re.sub(r'[^\d+]', '', raw)
    
    # + am Anfang behalten, dann nur Ziffern
    if digits.startswith('+'):
        digits = '+' + re.sub(r'\D', '', digits[1:])
    else:
        digits = re.sub(r'\D', '', digits)
    
    # Deutsche Nummer normalisieren
    if digits.startswith('+49'):
        digits = digits[3:]
    elif digits.startswith('0049'):
        digits = digits[4:]
    elif digits.startswith('49') and len(digits) >= 11:
        digits = digits[2:]
    elif digits.startswith('0'):
        digits = digits[1:]
    
    # Prüfe Länge (10-11 Ziffern für deutsche Mobilnummern)
    if 10 <= len(digits) <= 11:
        return f"+49{digits}"
    
    return ""


def is_valid_phone(phone: str) -> bool:
    """
    Prüft ob Telefonnummer gültig ist
    
    Args:
        phone: Normalisierte Telefonnummer
    
    Returns:
        True wenn gültig, False sonst
    """
    if not phone:
        return False
    
    # Entferne +49
    digits = phone.replace('+49', '')
    
    # Prüfe Länge (10-11 Ziffern)
    if len(digits) < 10 or len(digits) > 11:
        return False
    
    # Prüfe Blacklist
    for blacklisted in PHONE_BLACKLIST:
        if digits.startswith(blacklisted) or blacklisted in digits:
            return False
    
    # Prüfe auf zu viele gleiche Ziffern (z.B. 11111...)
    for digit in '0123456789':
        if digit * 6 in digits:  # 6 gleiche Ziffern hintereinander
            return False
    
    # Prüfe Mobilnummer-Prefix (nur Mobilnummern akzeptieren)
    mobile_prefixes = ['15', '16', '17']
    is_mobile = any(digits.startswith(p) for p in mobile_prefixes)
    
    return is_mobile


def calculate_confidence(raw_match: str, context: str) -> float:
    """
    Berechnet Konfidenz-Score für Telefonnummer basierend auf Kontext
    
    Args:
        raw_match: Gefundene Telefonnummer
        context: Umgebender Text
    
    Returns:
        Konfidenz-Score zwischen 0.0 und 1.0
    """
    confidence = 0.5  # Basis-Konfidenz
    
    # Kontext-Signale (case-insensitive)
    context_lower = context.lower()
    
    # Finde Position der Nummer im Kontext
    match_pos = context_lower.find(raw_match.lower())
    if match_pos == -1:
        match_pos = len(context_lower) // 2  # Fallback zur Mitte
    
    # Extrahiere Kontext um die Nummer herum (100 Zeichen vor und nach)
    start = max(0, match_pos - 100)
    end = min(len(context_lower), match_pos + len(raw_match) + 100)
    local_context = context_lower[start:end]
    
    # Positive Signale
    positive_keywords = {
        'telefon': 0.2,
        'tel:': 0.2,
        'tel.': 0.15,
        'mobil': 0.2,
        'handy': 0.2,
        'mobile': 0.15,
        'erreichbar': 0.15,
        'rückruf': 0.15,
        'whatsapp': 0.1,
        'kontakt': 0.1,
        'anrufen': 0.1,
        'melden': 0.1,
        'erreichen': 0.1,
        'rufen sie': 0.15,
        'tel': 0.1,
        'phone': 0.15,
    }
    
    for keyword, boost in positive_keywords.items():
        if keyword in local_context:
            confidence += boost
    
    # Negative Signale
    negative_keywords = {
        'fax': 0.3,
        'impressum': 0.2,
        'hotline': 0.2,
        'service': 0.15,
        'zentrale': 0.15,
        'sekretariat': 0.15,
        'firma': 0.1,
        'unternehmen': 0.1,
        'gmbh': 0.15,
        'ag': 0.1,
    }
    
    for keyword, penalty in negative_keywords.items():
        if keyword in local_context:
            confidence -= penalty
    
    # Format-Bonus: Gut formatierte Nummern sind vertrauenswürdiger
    if re.search(r'[\s\-./]', raw_match):
        confidence += 0.05
    
    # Längen-Check: Vollständige Nummern sind besser
    digits_only = re.sub(r'\D', '', raw_match)
    if len(digits_only) >= 11:
        confidence += 0.05
    
    # Begrenze auf [0.1, 1.0]
    return min(1.0, max(0.1, confidence))


def deobfuscate_phone(text: str) -> List[str]:
    """
    Extrahiert verschleierte Telefonnummern
    
    Args:
        text: Text mit potentiell verschleierten Nummern
    
    Returns:
        Liste der gefundenen Nummern
    """
    results = []
    
    # Ersetze Worte durch Ziffern
    deobfuscated = text.lower()
    for pattern, replacement in OBFUSCATION_REPLACEMENTS:
        deobfuscated = re.sub(pattern, replacement, deobfuscated, flags=re.IGNORECASE)
    
    # Suche nach Ziffernfolgen
    for match in re.finditer(r'(\d[\s\d]{10,25})', deobfuscated):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) >= 10 and len(digits) <= 12:
            results.append(digits)
    
    return results


def extract_phone_from_link(url: str) -> Optional[str]:
    """
    Extrahiert Telefonnummer aus WhatsApp/Telegram Links
    
    Args:
        url: URL die eine Telefonnummer enthalten könnte
    
    Returns:
        Normalisierte Telefonnummer oder None
    """
    # WhatsApp-Pattern
    whatsapp_patterns = [
        r'wa\.me/(\d{10,15})',
        r'api\.whatsapp\.com/send\?phone=(\d{10,15})',
        r'whatsapp://send\?phone=(\d{10,15})',
    ]
    
    # Telegram-Pattern
    telegram_patterns = [
        r't\.me/\+?(\d{10,15})',
    ]
    
    all_patterns = whatsapp_patterns + telegram_patterns
    
    for pattern in all_patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            number = match.group(1)
            # Normalisiere und validiere
            if number.startswith('49'):
                normalized = '+' + number
            elif len(number) == 11 and number.startswith('1'):
                normalized = '+49' + number
            else:
                normalized = '+49' + number.lstrip('0')
            
            if is_valid_phone(normalized):
                return normalized
    
    return None


def get_best_phone(extraction_results: List[Tuple[str, str, float]]) -> Optional[str]:
    """
    Wählt die beste Telefonnummer aus mehreren Ergebnissen
    
    Args:
        extraction_results: Liste von (normalized, raw, confidence) Tupeln
    
    Returns:
        Beste Telefonnummer oder None
    """
    if not extraction_results:
        return None
    
    # Bereits nach Konfidenz sortiert, also erste Nummer nehmen
    # Aber nur wenn Konfidenz > 0.3
    best = extraction_results[0]
    if best[2] >= 0.3:
        return best[0]
    
    return None


def extract_phone_simple(text: str) -> Optional[str]:
    """
    Einfache Telefon-Extraktion (Wrapper für Kompatibilität)
    
    Args:
        text: Text zum Durchsuchen
    
    Returns:
        Erste gefundene Telefonnummer oder None
    """
    results = extract_phones_advanced(text)
    return get_best_phone(results)
