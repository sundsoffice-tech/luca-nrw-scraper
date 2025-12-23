# -*- coding: utf-8 -*-
"""
Intelligente Lead-Deduplizierung

Dieses Modul verhindert doppelte Leads durch:
- Telefonnummern-Index
- Name+Stadt Fuzzy-Matching
- E-Mail-Index
"""

import re
import sqlite3
from typing import Optional, Dict, Tuple
from difflib import SequenceMatcher


class LeadDeduplicator:
    """Verhindert doppelte Leads durch intelligente Deduplizierung"""
    
    def __init__(self, db_path: str = "scraper.db"):
        """
        Initialisiert den Deduplicator
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Erstellt Deduplizierungs-Tabellen"""
        with sqlite3.connect(self.db_path) as conn:
            # Telefon-Index
            conn.execute('''CREATE TABLE IF NOT EXISTS dedup_phones (
                phone TEXT PRIMARY KEY,
                lead_id INTEGER,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Name+Stadt Index
            conn.execute('''CREATE TABLE IF NOT EXISTS dedup_name_city (
                hash TEXT PRIMARY KEY,
                lead_id INTEGER,
                name TEXT,
                city TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # E-Mail Index
            conn.execute('''CREATE TABLE IF NOT EXISTS dedup_emails (
                email TEXT PRIMARY KEY,
                lead_id INTEGER,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Erstelle Indizes für bessere Performance
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_dedup_phones_lead 
                         ON dedup_phones(lead_id)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_dedup_name_city_lead 
                         ON dedup_name_city(lead_id)''')
            conn.execute('''CREATE INDEX IF NOT EXISTS idx_dedup_emails_lead 
                         ON dedup_emails(lead_id)''')
            
            conn.commit()
    
    def is_duplicate(self, lead: Dict) -> Tuple[bool, str]:
        """
        Prüft ob Lead ein Duplikat ist
        
        Args:
            lead: Lead-Dictionary mit name, telefon, email, stadt
        
        Returns:
            Tupel: (is_duplicate, reason)
        """
        phone = lead.get('telefon', '') or lead.get('phone', '')
        email = lead.get('email', '')
        name = lead.get('name', '')
        city = lead.get('stadt', '') or lead.get('city', '') or lead.get('region', '')
        
        with sqlite3.connect(self.db_path) as conn:
            # 1. Telefon-Check (exakt)
            if phone:
                normalized = self._normalize_phone(phone)
                if normalized:
                    cursor = conn.execute(
                        'SELECT lead_id FROM dedup_phones WHERE phone = ?',
                        (normalized,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return True, f"Telefon bereits vorhanden: {phone} (Lead #{row[0]})"
            
            # 2. E-Mail-Check (exakt)
            if email:
                normalized_email = email.lower().strip()
                cursor = conn.execute(
                    'SELECT lead_id FROM dedup_emails WHERE email = ?',
                    (normalized_email,)
                )
                row = cursor.fetchone()
                if row:
                    return True, f"E-Mail bereits vorhanden: {email} (Lead #{row[0]})"
            
            # 3. Name+Stadt Check (fuzzy)
            if name and city:
                existing = self._find_similar_name_city(conn, name, city)
                if existing:
                    return True, f"Ähnlicher Name in Stadt: {existing[0]} in {existing[1]} (Lead #{existing[2]})"
        
        return False, ""
    
    def register_lead(self, lead: Dict, lead_id: int):
        """
        Registriert Lead für Deduplizierung
        
        Args:
            lead: Lead-Dictionary
            lead_id: ID des Leads in der Datenbank
        """
        phone = lead.get('telefon', '') or lead.get('phone', '')
        email = lead.get('email', '')
        name = lead.get('name', '')
        city = lead.get('stadt', '') or lead.get('city', '') or lead.get('region', '')
        
        with sqlite3.connect(self.db_path) as conn:
            # Telefon registrieren
            if phone:
                normalized = self._normalize_phone(phone)
                if normalized:
                    conn.execute('''
                        INSERT OR REPLACE INTO dedup_phones (phone, lead_id, last_seen)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (normalized, lead_id))
            
            # E-Mail registrieren
            if email:
                normalized_email = email.lower().strip()
                conn.execute('''
                    INSERT OR REPLACE INTO dedup_emails (email, lead_id, last_seen)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (normalized_email, lead_id))
            
            # Name+Stadt registrieren
            if name and city:
                hash_key = self._hash_name_city(name, city)
                conn.execute('''
                    INSERT OR REPLACE INTO dedup_name_city 
                    (hash, lead_id, name, city, last_seen)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (hash_key, lead_id, name, city))
            
            conn.commit()
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalisiert Telefonnummer für Vergleich
        
        Args:
            phone: Rohe Telefonnummer
        
        Returns:
            Normalisierte Nummer (letzte 10 Ziffern)
        """
        # Entferne alles außer Ziffern
        digits = re.sub(r'\D', '', phone)
        
        # Nehme letzte 10 Ziffern (ohne Ländervorwahl)
        if len(digits) >= 10:
            return digits[-10:]
        
        return ""
    
    def _hash_name_city(self, name: str, city: str) -> str:
        """
        Erstellt Hash aus Name und Stadt
        
        Args:
            name: Name der Person
            city: Stadt
        
        Returns:
            Hash-String
        """
        name_clean = re.sub(r'\s+', '', name.lower())
        city_clean = re.sub(r'\s+', '', city.lower())
        return f"{name_clean[:15]}_{city_clean[:15]}"
    
    def _find_similar_name_city(self, conn, name: str, city: str) -> Optional[Tuple[str, str, int]]:
        """
        Findet ähnliche Name+Stadt Kombinationen
        
        Args:
            conn: SQLite Connection
            name: Name zum Suchen
            city: Stadt zum Suchen
        
        Returns:
            Tupel (name, city, lead_id) oder None
        """
        # Suche nach ähnlichen Städten (Teilstring-Match)
        city_pattern = f'%{city[:5]}%'
        cursor = conn.execute(
            'SELECT name, city, lead_id FROM dedup_name_city WHERE city LIKE ?',
            (city_pattern,)
        )
        
        name_lower = name.lower()
        for row in cursor:
            existing_name = row[0]
            existing_city = row[1]
            existing_lead_id = row[2]
            
            # Berechne Ähnlichkeit der Namen
            similarity = SequenceMatcher(None, name_lower, existing_name.lower()).ratio()
            
            # Wenn Namen sehr ähnlich sind (> 85%), ist es wahrscheinlich ein Duplikat
            if similarity > 0.85:
                return (existing_name, existing_city, existing_lead_id)
        
        return None
    
    def get_stats(self) -> Dict:
        """
        Gibt Deduplizierungs-Statistiken zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        with sqlite3.connect(self.db_path) as conn:
            phones = conn.execute('SELECT COUNT(*) FROM dedup_phones').fetchone()[0]
            emails = conn.execute('SELECT COUNT(*) FROM dedup_emails').fetchone()[0]
            names = conn.execute('SELECT COUNT(*) FROM dedup_name_city').fetchone()[0]
        
        return {
            'unique_phones': phones,
            'unique_emails': emails,
            'unique_name_city': names,
            'total_unique': max(phones, emails, names),  # Approximation
        }
    
    def cleanup_old_entries(self, days: int = 90):
        """
        Entfernt alte Einträge aus der Deduplizierungs-Datenbank
        
        Args:
            days: Alter in Tagen, ab dem Einträge gelöscht werden
        """
        with sqlite3.connect(self.db_path) as conn:
            # Lösche alte Telefonnummern
            conn.execute('''
                DELETE FROM dedup_phones 
                WHERE last_seen < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            # Lösche alte E-Mails
            conn.execute('''
                DELETE FROM dedup_emails 
                WHERE last_seen < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            # Lösche alte Name+Stadt Kombinationen
            conn.execute('''
                DELETE FROM dedup_name_city 
                WHERE last_seen < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            conn.commit()
    
    def reset(self):
        """Setzt die Deduplizierungs-Datenbank zurück (löscht alle Einträge)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM dedup_phones')
            conn.execute('DELETE FROM dedup_emails')
            conn.execute('DELETE FROM dedup_name_city')
            conn.commit()
    
    def get_duplicate_count(self) -> int:
        """
        Schätzt die Anzahl der verhinderten Duplikate
        
        Returns:
            Geschätzte Anzahl verhinderter Duplikate
        """
        stats = self.get_stats()
        # Einfache Schätzung: Summe aller eindeutigen Einträge
        return stats['unique_phones'] + stats['unique_emails'] + stats['unique_name_city']


# Globale Instanz (wird von scriptname.py initialisiert)
_global_deduplicator: Optional[LeadDeduplicator] = None


def get_deduplicator(db_path: str = "scraper.db") -> LeadDeduplicator:
    """
    Gibt die globale Deduplicator-Instanz zurück (Singleton)
    
    Args:
        db_path: Pfad zur Datenbank
    
    Returns:
        LeadDeduplicator Instanz
    """
    global _global_deduplicator
    
    if _global_deduplicator is None:
        _global_deduplicator = LeadDeduplicator(db_path)
    
    return _global_deduplicator
