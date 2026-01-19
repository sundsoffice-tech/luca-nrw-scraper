# -*- coding: utf-8 -*-
"""
Feedback Loop System für Datenqualität und dynamisches Scoring.

Dieses Modul implementiert:
- Feedback-Sammlung von Lead-Qualität (User-Bewertungen)
- Dynamische Score-Anpassung basierend auf historischem Feedback
- Qualitäts-Metriken und Lern-Pipeline
- Datenspeicherung für kontinuierliches Lernen
"""

from __future__ import annotations

import sqlite3
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeedbackEntry:
    """Ein einzelnes Feedback zu einem Lead."""
    lead_id: int
    feedback_type: str  # 'quality', 'conversion', 'extraction_error'
    rating: float  # 0.0 - 1.0
    user_id: Optional[str] = None
    notes: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return asdict(self)


@dataclass
class QualityMetrics:
    """Qualitäts-Metriken für einen Zeitraum."""
    avg_rating: float = 0.0
    total_feedback: int = 0
    positive_rate: float = 0.0  # Rating >= 0.7
    conversion_rate: float = 0.0  # Erfolgreiche Kontaktaufnahmen
    extraction_accuracy: float = 0.0  # Korrekte Extraktionen
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return asdict(self)


class FeedbackLoopSystem:
    """
    System für Feedback-Sammlung und dynamisches Scoring.
    
    Funktionen:
    - Speichert User-Feedback zu Leads
    - Berechnet Qualitäts-Metriken
    - Passt Scoring-Parameter dynamisch an
    - Identifiziert Muster in erfolgreichen/erfolglosen Leads
    """
    
    def __init__(self, db_path: str = "scraper.db"):
        self.db_path = db_path
        self._init_feedback_tables()
        self._load_scoring_adjustments()
    
    def _init_feedback_tables(self):
        """Initialisiert Datenbank-Tabellen für Feedback-System."""
        with sqlite3.connect(self.db_path) as conn:
            # Lead Feedback
            conn.execute('''CREATE TABLE IF NOT EXISTS lead_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                feedback_type TEXT NOT NULL,
                rating REAL NOT NULL,
                user_id TEXT,
                notes TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )''')
            
            # Scoring Adjustments (gelernte Anpassungen)
            conn.execute('''CREATE TABLE IF NOT EXISTS scoring_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adjustment_key TEXT UNIQUE NOT NULL,
                adjustment_value REAL NOT NULL,
                confidence REAL DEFAULT 0.5,
                sample_size INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )''')
            
            # Extraction Accuracy Tracking
            conn.execute('''CREATE TABLE IF NOT EXISTS extraction_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                extracted_value TEXT,
                correct_value TEXT,
                is_correct INTEGER DEFAULT 0,
                confidence REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Quality Patterns (erfolgreiche Muster)
            conn.execute('''CREATE TABLE IF NOT EXISTS quality_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            conn.commit()
    
    def _load_scoring_adjustments(self):
        """Lädt gelernte Scoring-Anpassungen beim Start."""
        self.adjustments = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT adjustment_key, adjustment_value, confidence 
                    FROM scoring_adjustments 
                    WHERE confidence >= 0.6
                ''')
                for row in cursor.fetchall():
                    self.adjustments[row[0]] = {
                        'value': row[1],
                        'confidence': row[2]
                    }
        except Exception as e:
            logger.warning(f"Could not load scoring adjustments: {e}")
    
    # ==================== FEEDBACK COLLECTION ====================
    
    def record_feedback(self, feedback: FeedbackEntry) -> bool:
        """
        Speichert Feedback zu einem Lead.
        
        Args:
            feedback: FeedbackEntry-Objekt
            
        Returns:
            True bei Erfolg
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                metadata_json = json.dumps(feedback.metadata) if feedback.metadata else None
                conn.execute('''
                    INSERT INTO lead_feedback 
                    (lead_id, feedback_type, rating, user_id, notes, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    feedback.lead_id,
                    feedback.feedback_type,
                    feedback.rating,
                    feedback.user_id,
                    feedback.notes,
                    metadata_json
                ))
                conn.commit()
            
            # Aktualisiere Scoring-Adjustments basierend auf neuem Feedback
            self._update_scoring_adjustments(feedback)
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False
    
    def record_extraction_accuracy(
        self,
        lead_id: int,
        field_name: str,
        extracted: str,
        correct: str,
        confidence: float
    ) -> bool:
        """
        Speichert Genauigkeit einer Extraktion.
        
        Args:
            lead_id: ID des Leads
            field_name: Name des Feldes (email, phone, name, etc.)
            extracted: Extrahierter Wert
            correct: Korrekter Wert (User-korrigiert)
            confidence: Konfidenz der Extraktion
            
        Returns:
            True bei Erfolg
        """
        is_correct = 1 if extracted == correct else 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO extraction_accuracy
                    (lead_id, field_name, extracted_value, correct_value, is_correct, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (lead_id, field_name, extracted, correct, is_correct, confidence))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording extraction accuracy: {e}")
            return False
    
    # ==================== QUALITY METRICS ====================
    
    def get_quality_metrics(self, days: int = 7) -> QualityMetrics:
        """
        Berechnet Qualitäts-Metriken für einen Zeitraum.
        
        Args:
            days: Anzahl Tage zurück
            
        Returns:
            QualityMetrics-Objekt
        """
        metrics = QualityMetrics()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Overall feedback metrics
                cursor = conn.execute('''
                    SELECT AVG(rating), COUNT(*), 
                           SUM(CASE WHEN rating >= 0.7 THEN 1 ELSE 0 END)
                    FROM lead_feedback
                    WHERE timestamp > datetime('now', '-' || ? || ' days')
                ''', (days,))
                row = cursor.fetchone()
                
                if row and row[1] > 0:
                    metrics.avg_rating = row[0] or 0.0
                    metrics.total_feedback = row[1]
                    metrics.positive_rate = (row[2] or 0) / row[1]
                
                # Conversion rate
                cursor = conn.execute('''
                    SELECT COUNT(*) 
                    FROM lead_feedback
                    WHERE feedback_type = 'conversion' 
                      AND rating >= 0.7
                      AND timestamp > datetime('now', '-' || ? || ' days')
                ''', (days,))
                conversions = cursor.fetchone()[0] or 0
                metrics.conversion_rate = conversions / max(1, metrics.total_feedback)
                
                # Extraction accuracy
                cursor = conn.execute('''
                    SELECT AVG(is_correct) 
                    FROM extraction_accuracy
                    WHERE timestamp > datetime('now', '-' || ? || ' days')
                ''', (days,))
                row = cursor.fetchone()
                if row and row[0] is not None:
                    metrics.extraction_accuracy = row[0]
        
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
        
        return metrics
    
    def get_field_accuracy(self, field_name: str, days: int = 30) -> float:
        """
        Gibt Extractions-Genauigkeit für ein bestimmtes Feld zurück.
        
        Args:
            field_name: Name des Feldes (email, phone, name)
            days: Anzahl Tage zurück
            
        Returns:
            Genauigkeit (0.0 - 1.0)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT AVG(is_correct), COUNT(*)
                    FROM extraction_accuracy
                    WHERE field_name = ?
                      AND timestamp > datetime('now', '-' || ? || ' days')
                ''', (field_name, days))
                row = cursor.fetchone()
                
                if row and row[1] > 0:
                    return row[0] or 0.0
        except Exception:
            pass
        
        return 0.0
    
    # ==================== DYNAMIC SCORING ====================
    
    def _update_scoring_adjustments(self, feedback: FeedbackEntry):
        """
        Aktualisiert Scoring-Parameter basierend auf Feedback.
        
        Analysiert Feedback und passt Score-Gewichtungen an:
        - Positive Leads -> erhöhe Gewicht der Merkmale
        - Negative Leads -> reduziere Gewicht der Merkmale
        """
        # Diese Methode würde in einer vollständigen Implementierung
        # komplexe Muster-Erkennung durchführen
        # Hier eine vereinfachte Version:
        
        if feedback.metadata:
            lead_features = feedback.metadata
            
            # Beispiel: E-Mail-Provider-Gewichtung anpassen
            if 'email_domain' in lead_features:
                domain = lead_features['email_domain']
                key = f"email_domain:{domain}"
                
                # Positives Feedback -> erhöhe Score
                adjustment = 0.05 if feedback.rating >= 0.7 else -0.03
                
                self._update_adjustment(key, adjustment, feedback.rating)
            
            # Beispiel: Branchen-Gewichtung anpassen
            if 'industry' in lead_features:
                industry = lead_features['industry']
                key = f"industry:{industry}"
                
                adjustment = 0.08 if feedback.rating >= 0.7 else -0.05
                self._update_adjustment(key, adjustment, feedback.rating)
    
    def _update_adjustment(self, key: str, adjustment: float, confidence: float):
        """Aktualisiert eine einzelne Scoring-Anpassung."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Hole existierenden Wert
                cursor = conn.execute('''
                    SELECT adjustment_value, sample_size 
                    FROM scoring_adjustments 
                    WHERE adjustment_key = ?
                ''', (key,))
                row = cursor.fetchone()
                
                if row:
                    # Aktualisiere mit gleitendem Durchschnitt
                    old_value, sample_size = row
                    new_sample_size = sample_size + 1
                    new_value = (old_value * sample_size + adjustment) / new_sample_size
                    new_confidence = min(1.0, confidence * (new_sample_size / 10))
                    
                    conn.execute('''
                        UPDATE scoring_adjustments
                        SET adjustment_value = ?,
                            confidence = ?,
                            sample_size = ?,
                            last_updated = datetime('now')
                        WHERE adjustment_key = ?
                    ''', (new_value, new_confidence, new_sample_size, key))
                else:
                    # Erstelle neuen Eintrag
                    conn.execute('''
                        INSERT INTO scoring_adjustments
                        (adjustment_key, adjustment_value, confidence, sample_size)
                        VALUES (?, ?, ?, 1)
                    ''', (key, adjustment, confidence * 0.3))
                
                conn.commit()
                
                # Update in-memory cache
                self.adjustments[key] = {
                    'value': adjustment if not row else new_value,
                    'confidence': confidence * 0.3 if not row else new_confidence
                }
        
        except Exception as e:
            logger.error(f"Error updating adjustment for {key}: {e}")
    
    def get_dynamic_score_adjustment(self, lead: Dict[str, Any]) -> float:
        """
        Berechnet dynamische Score-Anpassung basierend auf gelernten Mustern.
        
        Args:
            lead: Lead-Dictionary mit Features
            
        Returns:
            Score-Anpassung (kann positiv oder negativ sein)
        """
        total_adjustment = 0.0
        
        # E-Mail-Domain-Adjustment
        email = lead.get('email', '')
        if '@' in email:
            domain = email.split('@')[1]
            key = f"email_domain:{domain}"
            if key in self.adjustments:
                adj = self.adjustments[key]
                total_adjustment += adj['value'] * adj['confidence']
        
        # Branchen-Adjustment
        industry = lead.get('industry', '')
        if industry:
            key = f"industry:{industry}"
            if key in self.adjustments:
                adj = self.adjustments[key]
                total_adjustment += adj['value'] * adj['confidence']
        
        # Region-Adjustment
        region = lead.get('region', '')
        if region:
            key = f"region:{region}"
            if key in self.adjustments:
                adj = self.adjustments[key]
                total_adjustment += adj['value'] * adj['confidence']
        
        return total_adjustment
    
    # ==================== PATTERN RECOGNITION ====================
    
    def record_quality_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        was_successful: bool
    ):
        """
        Speichert ein Qualitäts-Muster (erfolgreich oder nicht).
        
        Args:
            pattern_type: Art des Musters (z.B. 'email_format', 'phone_context')
            pattern_data: Muster-Daten als Dict
            was_successful: Ob Lead erfolgreich war
        """
        pattern_json = json.dumps(pattern_data, sort_keys=True)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT id, success_count, failure_count 
                    FROM quality_patterns
                    WHERE pattern_type = ? AND pattern_data = ?
                ''', (pattern_type, pattern_json))
                row = cursor.fetchone()
                
                if row:
                    pattern_id, success_count, failure_count = row
                    if was_successful:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    total = success_count + failure_count
                    success_rate = success_count / total if total > 0 else 0.0
                    
                    conn.execute('''
                        UPDATE quality_patterns
                        SET success_count = ?,
                            failure_count = ?,
                            success_rate = ?,
                            last_seen = datetime('now')
                        WHERE id = ?
                    ''', (success_count, failure_count, success_rate, pattern_id))
                else:
                    success_count = 1 if was_successful else 0
                    failure_count = 0 if was_successful else 1
                    success_rate = 1.0 if was_successful else 0.0
                    
                    conn.execute('''
                        INSERT INTO quality_patterns
                        (pattern_type, pattern_data, success_count, failure_count, success_rate)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (pattern_type, pattern_json, success_count, failure_count, success_rate))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error recording quality pattern: {e}")
    
    def get_best_patterns(
        self,
        pattern_type: str,
        min_samples: int = 5,
        limit: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Gibt die besten (erfolgreichsten) Muster zurück.
        
        Args:
            pattern_type: Art des Musters
            min_samples: Mindest-Anzahl an Samples
            limit: Max. Anzahl Ergebnisse
            
        Returns:
            Liste von (pattern_data, success_rate) Tupeln
        """
        patterns = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT pattern_data, success_rate
                    FROM quality_patterns
                    WHERE pattern_type = ?
                      AND (success_count + failure_count) >= ?
                    ORDER BY success_rate DESC, success_count DESC
                    LIMIT ?
                ''', (pattern_type, min_samples, limit))
                
                for row in cursor.fetchall():
                    try:
                        pattern_data = json.loads(row[0])
                        patterns.append((pattern_data, row[1]))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error getting best patterns: {e}")
        
        return patterns
    
    # ==================== REPORTING ====================
    
    def get_feedback_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Gibt Zusammenfassung des Feedback-Systems zurück.
        
        Args:
            days: Anzahl Tage zurück
            
        Returns:
            Dict mit Summary-Daten
        """
        metrics = self.get_quality_metrics(days)
        
        # Top Adjustments
        top_adjustments = sorted(
            self.adjustments.items(),
            key=lambda x: abs(x[1]['value']) * x[1]['confidence'],
            reverse=True
        )[:10]
        
        return {
            'quality_metrics': metrics.to_dict(),
            'active_adjustments': len(self.adjustments),
            'top_adjustments': [
                {
                    'key': key,
                    'value': adj['value'],
                    'confidence': adj['confidence']
                }
                for key, adj in top_adjustments
            ],
            'field_accuracy': {
                'email': self.get_field_accuracy('email', days),
                'phone': self.get_field_accuracy('phone', days),
                'name': self.get_field_accuracy('name', days),
            }
        }


# Singleton-Instanz
_feedback_system = None


def get_feedback_system(db_path: str = "scraper.db") -> FeedbackLoopSystem:
    """Gibt Singleton-Instanz des Feedback-Systems zurück."""
    global _feedback_system
    if _feedback_system is None or _feedback_system.db_path != db_path:
        _feedback_system = FeedbackLoopSystem(db_path)
    return _feedback_system


__all__ = [
    'FeedbackEntry',
    'QualityMetrics',
    'FeedbackLoopSystem',
    'get_feedback_system',
]
