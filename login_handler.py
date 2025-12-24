#!/usr/bin/env python3
"""
Human-in-the-Loop Login Handler
Öffnet Browser für manuellen Login und speichert Session-Cookies
"""

import os
import json
import time
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import sqlite3

# Versuche selenium zu importieren (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Session-Speicherort
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

# Login-Erkennungs-Patterns
LOGIN_INDICATORS = [
    # Text-Patterns (case-insensitive)
    "bitte anmelden",
    "bitte einloggen", 
    "login required",
    "anmeldung erforderlich",
    "please log in",
    "please sign in",
    "zugang verweigert",
    "access denied",
    "nicht berechtigt",
    "captcha",
    "sind sie ein roboter",
    "are you a robot",
    "unusual traffic",
    "too many requests",
]

# Portal-spezifische Login-URLs
PORTAL_LOGIN_URLS = {
    "kleinanzeigen": "https://www.kleinanzeigen.de/m-einloggen.html",
    "linkedin": "https://www.linkedin.com/login",
    "xing": "https://login.xing.com/",
    "indeed": "https://secure.indeed.com/account/login",
    "facebook": "https://www.facebook.com/login",
    "stepstone": "https://www.stepstone.de/login",
    "monster": "https://www.monster.de/login",
    "quoka": "https://www.quoka.de/",  # Kein separater Login
    "markt_de": "https://www.markt.de/",  # Kein separater Login
}


class LoginHandler:
    """Verwaltet Login-Sessions für verschiedene Portale"""
    
    def __init__(self, db_path: str = "scraper.db"):
        self.db_path = db_path
        self.sessions_dir = SESSIONS_DIR
        self._init_db()
        
    def _init_db(self):
        """Erstellt Session-Tabelle"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS login_sessions (
                portal TEXT PRIMARY KEY,
                cookies_json TEXT,
                user_agent TEXT,
                logged_in_at TEXT,
                expires_at TEXT,
                is_valid INTEGER DEFAULT 1
            )''')
            conn.commit()
    
    def detect_login_required(self, response_text: str, status_code: int = 200, url: str = "") -> bool:
        """
        Erkennt ob ein Login erforderlich ist
        Returns: True wenn Login nötig
        """
        # Status-Code Check
        if status_code in [401, 403, 429]:
            return True
        
        # Text-Pattern Check
        text_lower = response_text.lower()
        for pattern in LOGIN_INDICATORS:
            if pattern in text_lower:
                return True
        
        # URL-Pattern Check (Redirect zu Login)
        if any(x in url.lower() for x in ['login', 'signin', 'anmelden', 'einloggen']):
            return True
        
        return False
    
    def get_portal_from_url(self, url: str) -> Optional[str]:
        """Ermittelt Portal-Name aus URL"""
        url_lower = url.lower()
        
        portal_domains = {
            "kleinanzeigen.de": "kleinanzeigen",
            "linkedin.com": "linkedin",
            "xing.com": "xing",
            "indeed.com": "indeed",
            "indeed.de": "indeed",
            "facebook.com": "facebook",
            "stepstone.de": "stepstone",
            "monster.de": "monster",
            "quoka.de": "quoka",
            "markt.de": "markt_de",
        }
        
        for domain, portal in portal_domains.items():
            if domain in url_lower:
                return portal
        
        return None
    
    def has_valid_session(self, portal: str) -> bool:
        """Prüft ob eine gültige Session existiert"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('''
                SELECT is_valid, expires_at FROM login_sessions 
                WHERE portal = ?
            ''', (portal,)).fetchone()
            
            if not result:
                return False
            
            is_valid, expires_at = result
            
            # Prüfe Ablaufdatum
            if expires_at:
                try:
                    exp_date = datetime.fromisoformat(expires_at)
                    if datetime.now() > exp_date:
                        return False
                except (ValueError, TypeError):
                    pass
            
            return bool(is_valid)
    
    def get_session_cookies(self, portal: str) -> Optional[List[Dict]]:
        """Lädt gespeicherte Cookies für Portal"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('''
                SELECT cookies_json FROM login_sessions 
                WHERE portal = ? AND is_valid = 1
            ''', (portal,)).fetchone()
            
            if result and result[0]:
                try:
                    return json.loads(result[0])
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return None
    
    def save_session(self, portal: str, cookies: List[Dict], user_agent: str = ""):
        """Speichert Session-Cookies"""
        cookies_json = json.dumps(cookies)
        
        # Session-Ablauf: 7 Tage
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO login_sessions 
                (portal, cookies_json, user_agent, logged_in_at, expires_at, is_valid)
                VALUES (?, ?, ?, datetime('now'), ?, 1)
            ''', (portal, cookies_json, user_agent, expires_at))
            conn.commit()
        
        # Auch als JSON-Datei speichern (Backup)
        cookie_file = self.sessions_dir / f"{portal}_cookies.json"
        with open(cookie_file, 'w') as f:
            json.dump({
                "portal": portal,
                "cookies": cookies,
                "user_agent": user_agent,
                "saved_at": datetime.now().isoformat()
            }, f, indent=2)
    
    def invalidate_session(self, portal: str):
        """Markiert Session als ungültig"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE login_sessions SET is_valid = 0 WHERE portal = ?
            ''', (portal,))
            conn.commit()
    
    def request_manual_login(self, portal: str, original_url: str = "") -> Optional[List[Dict]]:
        """
        Öffnet Browser für manuellen Login
        Returns: Cookies nach erfolgreichem Login oder None
        """
        login_url = PORTAL_LOGIN_URLS.get(portal, original_url)
        
        print("\n" + "=" * 60)
        print("🔐 LOGIN ERFORDERLICH")
        print("=" * 60)
        print(f"Portal: {portal.upper()}")
        print(f"URL: {login_url}")
        print("-" * 60)
        
        if SELENIUM_AVAILABLE:
            return self._selenium_login(portal, login_url)
        else:
            return self._manual_browser_login(portal, login_url)
    
    def _selenium_login(self, portal: str, login_url: str) -> Optional[List[Dict]]:
        """Login mit Selenium (Chrome wird geöffnet)"""
        print("🌐 Öffne Chrome Browser...")
        print("👉 Bitte logge dich ein und drücke ENTER wenn fertig.")
        print("-" * 60)
        
        try:
            # Chrome-Optionen
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            options.add_argument(f"--user-agent={user_agent}")
            
            # Browser starten
            driver = webdriver.Chrome(options=options)
            driver.get(login_url)
            
            # Warte auf User-Eingabe
            input("\n⏳ Drücke ENTER wenn du eingeloggt bist...")
            
            # Cookies extrahieren
            cookies = driver.get_cookies()
            current_url = driver.current_url
            
            # Browser schließen
            driver.quit()
            
            if cookies:
                print(f"✅ {len(cookies)} Cookies gespeichert!")
                self.save_session(portal, cookies, user_agent)
                return cookies
            else:
                print("❌ Keine Cookies gefunden")
                return None
                
        except Exception as e:
            print(f"❌ Selenium-Fehler: {e}")
            print("Versuche manuellen Browser-Login...")
            return self._manual_browser_login(portal, login_url)
    
    def _manual_browser_login(self, portal: str, login_url: str) -> Optional[List[Dict]]:
        """Fallback: Öffnet Standard-Browser, User muss Cookies manuell exportieren"""
        print("🌐 Öffne Standard-Browser...")
        print("-" * 60)
        print("ANLEITUNG:")
        print("1. Browser öffnet sich automatisch")
        print("2. Logge dich ein")
        print("3. Öffne DevTools (F12) → Application → Cookies")
        print("4. Kopiere die Cookies oder drücke einfach ENTER")
        print("-" * 60)
        
        # Browser öffnen
        self._open_url_in_browser(login_url)
        
        # Warte auf User
        input("\n⏳ Drücke ENTER wenn du eingeloggt bist...")
        
        # Frage nach Cookie-Eingabe (optional)
        print("\nOptional: Füge Cookies ein (JSON-Format) oder drücke ENTER zum Überspringen:")
        cookie_input = input().strip()
        
        if cookie_input:
            try:
                cookies = json.loads(cookie_input)
                self.save_session(portal, cookies)
                print(f"✅ Cookies gespeichert!")
                return cookies
            except json.JSONDecodeError:
                print("⚠️ Ungültiges JSON-Format, überspringe...")
        
        # Speichere leere Session (markiert als "versucht")
        print("ℹ️  Session ohne Cookies gespeichert (Browser-Cache wird verwendet)")
        return []
    
    def _open_url_in_browser(self, url: str):
        """Öffnet URL im Standard-Browser"""
        system = platform.system()
        
        try:
            if system == "Windows":
                os.startfile(url)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", url])
            else:  # Linux
                subprocess.run(["xdg-open", url])
        except Exception as e:
            print(f"⚠️ Konnte Browser nicht öffnen: {e}")
            print(f"Bitte öffne manuell: {url}")
    
    def get_all_sessions(self) -> List[Dict]:
        """Gibt alle gespeicherten Sessions zurück"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT portal, logged_in_at, expires_at, is_valid 
                FROM login_sessions
                ORDER BY logged_in_at DESC
            ''').fetchall()
        
        return [
            {
                "portal": row[0],
                "logged_in_at": row[1],
                "expires_at": row[2],
                "is_valid": bool(row[3])
            }
            for row in rows
        ]


# Globale Instanz
_login_handler = None

def get_login_handler() -> LoginHandler:
    """Gibt globale LoginHandler-Instanz zurück"""
    global _login_handler
    if _login_handler is None:
        _login_handler = LoginHandler()
    return _login_handler


def check_and_handle_login(response_text: str, status_code: int, url: str) -> Optional[List[Dict]]:
    """
    Hauptfunktion: Prüft ob Login nötig und handelt
    
    Aufruf im Scraper:
        cookies = check_and_handle_login(response.text, response.status_code, url)
        if cookies:
            # Retry mit Cookies
    """
    handler = get_login_handler()
    
    # Prüfe ob Login nötig
    if not handler.detect_login_required(response_text, status_code, url):
        return None
    
    # Ermittle Portal
    portal = handler.get_portal_from_url(url)
    if not portal:
        return None
    
    # Prüfe ob gültige Session existiert
    if handler.has_valid_session(portal):
        cookies = handler.get_session_cookies(portal)
        if cookies:
            return cookies
    
    # Kein gültiger Login - User muss einloggen
    return handler.request_manual_login(portal, url)
