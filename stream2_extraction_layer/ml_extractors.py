# -*- coding: utf-8 -*-
"""
Machine Learning-basierte Extraktoren für Namen, Telefonnummern und E-Mails.

Ergänzt die Regex-basierten Extraktoren mit ML-Modellen für bessere Genauigkeit:
- Named Entity Recognition (NER) für Namen
- Kontextbasierte Telefonnummer-Erkennung
- E-Mail-Validierung mit Domain-Klassifikation
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MLExtractionResult:
    """Ergebnis einer ML-basierten Extraktion mit Konfidenz."""
    value: Optional[str] = None
    confidence: float = 0.0
    method: str = "ml"
    context: Optional[str] = None


class SimpleNERNameExtractor:
    """
    Einfacher Named Entity Recognition Extraktor für deutsche Personennamen.
    
    Nutzt heuristische Regeln und Kontextanalyse für Namen-Erkennung:
    - Erkennt typische deutsche Namensmuster
    - Analysiert Kontext (Ansprechpartner, Kontakt, etc.)
    - Bewertet Konfidenz basierend auf Mustern
    """
    
    def __init__(self):
        self.title_patterns = [
            r'\b(Herr|Frau|Hr\.|Fr\.|Dr\.|Prof\.)\s+',
            r'\b(Geschäftsführer|Inhaber|Manager|Leiter|CEO|Director)\s*:?\s*',
        ]
        
        self.context_keywords = [
            'ansprechpartner', 'kontakt', 'ihr kontakt', 'ihr ansprechpartner',
            'ansprechperson', 'verantwortlich', 'beratung', 'kundenberater',
            'vertriebsleiter', 'sales manager', 'account manager',
        ]
        
        self.name_pattern = re.compile(
            r'\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)\b'
        )
        
        self.blacklist = {
            'impressum', 'datenschutz', 'agb', 'allgemeine geschäftsbedingungen',
            'gmbh', 'ag', 'kg', 'ug', 'inc', 'ltd', 'llc', 'deutschland',
            'north rhine westphalia', 'nordrhein westfalen', 'nrw',
        }
    
    def _extract_name_from_title_match(self, match: re.Match) -> Optional[str]:
        """
        Extracts name from title pattern match.
        
        Group structure:
        - Group 1: Title (Herr, Dr., etc.)
        - Group 2+: Name (if multiple groups exist)
        
        Returns:
            Extracted name or None
        """
        try:
            # If match has 2+ groups, second group is the name
            if match.lastindex and match.lastindex >= 2:
                return match.group(2).strip()
            # Otherwise, first group might be the name
            return match.group(1).strip()
        except (IndexError, AttributeError):
            return None
    
    def extract(self, text: str, html: str = "") -> MLExtractionResult:
        """
        Extrahiert Personennamen aus Text mit Konfidenz-Score.
        
        Args:
            text: Zu durchsuchender Text
            html: HTML-Inhalt für zusätzlichen Kontext
            
        Returns:
            MLExtractionResult mit extrahiertem Namen und Konfidenz
        """
        combined = f"{text}\n{html[:2000]}" if html else text
        combined_lower = combined.lower()
        
        best_name = None
        best_confidence = 0.0
        best_context = None
        
        # Suche nach Namen in Kontext von Schlüsselwörtern
        for keyword in self.context_keywords:
            keyword_pos = combined_lower.find(keyword)
            if keyword_pos == -1:
                continue
            
            # Extrahiere Kontext um Schlüsselwort (200 Zeichen)
            start = max(0, keyword_pos - 50)
            end = min(len(combined), keyword_pos + 200)
            context = combined[start:end]
            
            # Suche Namen im Kontext
            for match in self.name_pattern.finditer(context):
                candidate = match.group(1).strip()
                
                # Prüfe Blacklist
                if any(blocked in candidate.lower() for blocked in self.blacklist):
                    continue
                
                # Berechne Konfidenz
                confidence = self._calculate_confidence(candidate, context, keyword)
                
                if confidence > best_confidence:
                    best_name = candidate
                    best_confidence = confidence
                    best_context = context[:100]
        
        # Falls kein Name in Kontext gefunden, suche mit Titeln
        if best_confidence < 0.5:
            for title_pattern in self.title_patterns:
                for match in re.finditer(title_pattern + r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)', combined):
                    candidate = self._extract_name_from_title_match(match)
                    
                    if not candidate or any(blocked in candidate.lower() for blocked in self.blacklist):
                        continue
                    
                    confidence = 0.6  # Höhere Basis-Konfidenz für Titel
                    if confidence > best_confidence:
                        best_name = candidate
                        best_confidence = confidence
                        best_context = match.group(0)
        
        return MLExtractionResult(
            value=best_name,
            confidence=min(1.0, best_confidence),
            method="ner_heuristic",
            context=best_context
        )
    
    def _calculate_confidence(self, name: str, context: str, keyword: str) -> float:
        """Berechnet Konfidenz-Score für extrahierten Namen."""
        confidence = 0.4  # Basis-Konfidenz
        
        # Name hat 2-4 Teile (Vorname + Nachname(n))
        parts = name.split()
        if 2 <= len(parts) <= 4:
            confidence += 0.2
        
        # Keyword ist nah am Namen (innerhalb 30 Zeichen)
        keyword_pos = context.lower().find(keyword)
        name_pos = context.find(name)
        if keyword_pos != -1 and name_pos != -1:
            distance = abs(keyword_pos - name_pos)
            if distance < 30:
                confidence += 0.3
            elif distance < 60:
                confidence += 0.15
        
        # Name folgt direkt nach Doppelpunkt
        if f": {name}" in context or f":\n{name}" in context:
            confidence += 0.2
        
        return min(1.0, confidence)


class MLPhoneExtractor:
    """
    Machine Learning-unterstützte Telefonnummer-Extraktion.
    
    Ergänzt Regex-Patterns mit Kontext-Analyse:
    - Bewertet Telefonnummern basierend auf Kontext
    - Unterscheidet zwischen persönlichen und Firmen-Nummern
    - Filtert Hotlines und Service-Nummern
    """
    
    def __init__(self):
        self.positive_context = [
            'mobil', 'handy', 'mobile', 'erreichbar', 'direkt',
            'persönlich', 'ansprechpartner', 'kontakt', 'whatsapp',
            'tel:', 'tel.', 'telefon', 'phone', 'rückruf', 'melden',
        ]
        
        self.negative_context = [
            'zentrale', 'sekretariat', 'hotline', 'service',
            'kundenservice', 'support', 'fax', 'firma', 'büro',
            'impressum', 'allgemeine', 'geschäftszeiten',
        ]
    
    def score_phone(self, phone: str, raw_match: str, context: str) -> float:
        """
        Bewertet eine extrahierte Telefonnummer basierend auf Kontext.
        
        Args:
            phone: Normalisierte Telefonnummer
            raw_match: Original-Match
            context: Umgebender Text
            
        Returns:
            Konfidenz-Score zwischen 0.0 und 1.0
        """
        confidence = 0.5  # Basis-Konfidenz
        
        context_lower = context.lower()
        
        # Finde Position der Nummer im Kontext
        match_pos = context_lower.find(raw_match.lower())
        if match_pos == -1:
            match_pos = len(context_lower) // 2
        
        # Extrahiere lokalen Kontext (100 Zeichen vor/nach)
        start = max(0, match_pos - 100)
        end = min(len(context_lower), match_pos + len(raw_match) + 100)
        local_context = context_lower[start:end]
        
        # Positive Signale
        positive_count = sum(1 for kw in self.positive_context if kw in local_context)
        confidence += min(0.3, positive_count * 0.1)
        
        # Negative Signale
        negative_count = sum(1 for kw in self.negative_context if kw in local_context)
        confidence -= min(0.4, negative_count * 0.15)
        
        # Mobilnummer-Bonus
        if phone.startswith('+491') or phone.startswith('+4915') or phone.startswith('+4916') or phone.startswith('+4917'):
            confidence += 0.15
        
        # Format-Qualität
        if re.search(r'[\s\-./]', raw_match):
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))


class MLEmailClassifier:
    """
    ML-basierter E-Mail-Klassifikator.
    
    Klassifiziert E-Mail-Adressen in Kategorien:
    - Personal (vorname.nachname@...)
    - Generic (info@, kontakt@, ...)
    - Portal (stepstone.de, indeed.com, ...)
    - Corporate (firmen-domain)
    - Free (gmail.com, web.de, ...)
    """
    
    def __init__(self):
        self.generic_locals = {
            'info', 'kontakt', 'contact', 'office', 'support', 'service',
            'sales', 'vertrieb', 'jobs', 'karriere', 'hr', 'bewerbung',
            'noreply', 'no-reply', 'donotreply', 'privacy', 'datenschutz',
        }
        
        self.portal_domains = {
            'stepstone.de', 'indeed.com', 'heyjobs.co', 'heyjobs.de',
            'arbeitsagentur.de', 'softgarden.io', 'join.com', 'jobware.de',
            'monster.de', 'kununu.com', 'xing.com', 'linkedin.com',
        }
        
        self.free_providers = {
            'gmail.com', 'googlemail.com', 'outlook.com', 'hotmail.com',
            'yahoo.com', 'yahoo.de', 'gmx.de', 'gmx.net', 'web.de', 't-online.de',
        }
    
    def classify(self, email: str) -> Dict[str, Any]:
        """
        Klassifiziert E-Mail-Adresse und gibt Metadaten zurück.
        
        Args:
            email: E-Mail-Adresse
            
        Returns:
            Dict mit category, confidence, score_modifier
        """
        email = email.lower().strip()
        if '@' not in email:
            return {'category': 'invalid', 'confidence': 0.0, 'score_modifier': -1.0}
        
        local, domain = email.split('@', 1)
        
        # Portal-Check (höchste Priorität)
        if domain in self.portal_domains:
            return {
                'category': 'portal',
                'confidence': 1.0,
                'score_modifier': -0.3,
                'quality': 'very_low'
            }
        
        # Generic-Check
        if local in self.generic_locals:
            return {
                'category': 'generic',
                'confidence': 0.9,
                'score_modifier': -0.1,
                'quality': 'low'
            }
        
        # Free Provider-Check
        if domain in self.free_providers:
            # Bei Free-Mail: Prüfe ob persönlicher Name
            is_personal = self._is_personal_pattern(local)
            if is_personal:
                return {
                    'category': 'free_personal',
                    'confidence': 0.8,
                    'score_modifier': 0.1,
                    'quality': 'medium'
                }
            else:
                return {
                    'category': 'free_generic',
                    'confidence': 0.7,
                    'score_modifier': 0.0,
                    'quality': 'medium'
                }
        
        # Corporate E-Mail
        is_personal = self._is_personal_pattern(local)
        if is_personal:
            return {
                'category': 'corporate_personal',
                'confidence': 0.9,
                'score_modifier': 0.3,
                'quality': 'high'
            }
        else:
            return {
                'category': 'corporate_generic',
                'confidence': 0.7,
                'score_modifier': 0.1,
                'quality': 'medium'
            }
    
    def _is_personal_pattern(self, local: str) -> bool:
        """Prüft ob E-Mail-Local-Part einem persönlichen Muster entspricht."""
        # Muster: vorname.nachname, v.nachname, vorname_nachname, etc.
        personal_patterns = [
            r'^[a-z]+\.[a-z]+$',  # max.mustermann
            r'^[a-z]\.[a-z]+$',   # m.mustermann
            r'^[a-z]+_[a-z]+$',   # max_mustermann
            r'^[a-z]+\-[a-z]+$',  # max-mustermann
        ]
        
        for pattern in personal_patterns:
            if re.match(pattern, local):
                return True
        
        # Long concatenated name (e.g., maxmustermann) only if >10 chars
        if len(local) > 10 and local.isalpha():
            return True
        
        return False


class MLIndustryClassifier:
    """
    Machine Learning-basierte Branchen-Klassifikation.
    
    Lernt aus Feedback und klassifiziert Leads in Branchen:
    - Versicherung
    - Energie
    - Telekom
    - Bau
    - E-Commerce
    - Haushalt
    - etc.
    """
    
    # Keyword frequency threshold for learning
    LEARNING_THRESHOLD = 3  # Keyword must appear 3+ times to be added
    
    def __init__(self):
        # Branchen-Keywords (wird durch Feedback erweitert)
        self.industry_keywords = {
            'versicherung': [
                'versicherung', 'insurance', 'makler', 'broker', 'assekuranz',
                'allianz', 'axa', 'ergo', 'gothaer', 'huk', 'devk',
            ],
            'energie': [
                'energie', 'strom', 'gas', 'elektrizität', 'energy',
                'stadtwerke', 'energieversorger', 'eon', 'rwe', 'vattenfall',
            ],
            'telekom': [
                'telekom', 'telco', 'mobilfunk', 'internet', 'telefon',
                'vodafone', 'o2', 'telefonica', 'provider', 'glasfaser',
            ],
            'bau': [
                'bau', 'construction', 'bauunternehmen', 'immobilien',
                'hausbau', 'sanierung', 'renovation', 'architekt',
            ],
            'ecommerce': [
                'online shop', 'e-commerce', 'ecommerce', 'onlineshop',
                'versandhandel', 'webshop', 'shop', 'amazon', 'ebay',
            ],
            'household': [
                'haushalt', 'household', 'haushaltsware', 'tupperware',
                'vorwerk', 'thermomix', 'direktvertrieb', 'home party',
            ],
            'recruiter': [
                'recruiting', 'recruiter', 'personalberatung', 'headhunter',
                'zeitarbeit', 'arbeitnehmerüberlassung', 'staffing', 'adecco',
                'randstad', 'manpower', 'personaldienstleister',
            ],
        }
        
        self.learning_data = {}  # Speichert Feedback für Learning
    
    def classify(self, text: str, url: str = "", company: str = "") -> Tuple[Optional[str], float]:
        """
        Klassifiziert einen Lead in eine Branche.
        
        Args:
            text: Lead-Text
            url: Lead-URL
            company: Firmenname
            
        Returns:
            Tuple[industry, confidence]
        """
        combined = f"{text} {url} {company}".lower()
        
        scores = {}
        for industry, keywords in self.industry_keywords.items():
            score = sum(combined.count(kw) for kw in keywords)
            if score > 0:
                scores[industry] = score
        
        if not scores:
            return None, 0.0
        
        # Beste Branche
        best_industry = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = min(1.0, scores[best_industry] / max(1, total_score))
        
        # Erhöhe Konfidenz wenn mehrere Keywords matchen
        if scores[best_industry] >= 3:
            confidence = min(1.0, confidence + 0.2)
        
        return best_industry, confidence
    
    def learn_from_feedback(self, text: str, correct_industry: str):
        """
        Lernt aus Feedback und erweitert Keywords.
        
        Args:
            text: Lead-Text
            correct_industry: Korrekte Branche (User-Feedback)
        """
        # Extrahiere potentielle neue Keywords
        words = re.findall(r'\b[a-zäöü]{4,}\b', text.lower())
        
        # Füge häufige Wörter zu Branchen-Keywords hinzu
        if correct_industry not in self.learning_data:
            self.learning_data[correct_industry] = {}
        
        for word in words:
            if word not in self.learning_data[correct_industry]:
                self.learning_data[correct_industry][word] = 0
            self.learning_data[correct_industry][word] += 1
        
        # Füge Keywords mit Häufigkeit >= LEARNING_THRESHOLD zu permanenten Keywords hinzu
        for word, count in self.learning_data[correct_industry].items():
            if count >= self.LEARNING_THRESHOLD and word not in self.industry_keywords.get(correct_industry, []):
                if correct_industry not in self.industry_keywords:
                    self.industry_keywords[correct_industry] = []
                self.industry_keywords[correct_industry].append(word)
                logger.info(f"Learned new keyword '{word}' for industry '{correct_industry}' (count: {count})")


# Singleton-Instanzen
_name_extractor = None
_phone_extractor = None
_email_classifier = None
_industry_classifier = None


def get_name_extractor() -> SimpleNERNameExtractor:
    """Gibt Singleton-Instanz des Name-Extractors zurück."""
    global _name_extractor
    if _name_extractor is None:
        _name_extractor = SimpleNERNameExtractor()
    return _name_extractor


def get_phone_extractor() -> MLPhoneExtractor:
    """Gibt Singleton-Instanz des Phone-Extractors zurück."""
    global _phone_extractor
    if _phone_extractor is None:
        _phone_extractor = MLPhoneExtractor()
    return _phone_extractor


def get_email_classifier() -> MLEmailClassifier:
    """Gibt Singleton-Instanz des Email-Classifiers zurück."""
    global _email_classifier
    if _email_classifier is None:
        _email_classifier = MLEmailClassifier()
    return _email_classifier


def get_industry_classifier() -> MLIndustryClassifier:
    """Gibt Singleton-Instanz des Industry-Classifiers zurück."""
    global _industry_classifier
    if _industry_classifier is None:
        _industry_classifier = MLIndustryClassifier()
    return _industry_classifier


__all__ = [
    'MLExtractionResult',
    'SimpleNERNameExtractor',
    'MLPhoneExtractor',
    'MLEmailClassifier',
    'MLIndustryClassifier',
    'get_name_extractor',
    'get_phone_extractor',
    'get_email_classifier',
    'get_industry_classifier',
]
