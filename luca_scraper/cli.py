"""
LUCA NRW Scraper - CLI Interface
=================================
Command-line argument parsing and configuration validation.
Extracted from scriptname.py in Phase 3 refactoring.
"""

import argparse
import os
from typing import Any, Optional, Callable

# Import config from centralized location
from .config import (
    OPENAI_API_KEY,
    GCS_API_KEY,
    GCS_CX,
    GCS_KEYS,
    GCS_CXS,
)


def validate_config(log_func: Optional[Callable] = None) -> None:
    """
    Validate configuration settings (API keys, etc.).
    
    Args:
        log_func: Optional logging function with signature log(level, message, **kwargs).
                  If None, prints warnings to stdout.
    
    Validates:
        - OPENAI_API_KEY length
        - GCS_KEYS/GCS_CXS consistency (both must be set or both empty)
        - GCS_API_KEY/GCS_CX consistency for legacy single-config
    """
    errs = []
    
    # Validate OpenAI API Key
    if not OPENAI_API_KEY or len(OPENAI_API_KEY) < 40:
        errs.append("OPENAI_API_KEY zu kurz/leer (für KI-Extraktion). Regex-Fallback läuft dennoch.")
    
    # Validate Google Custom Search configuration (list-based)
    if (GCS_KEYS and not GCS_CXS) or (GCS_CXS and not GCS_KEYS):
        errs.append("GCS_KEYS/GCS_CXS unvollständig (beide listenbasiert setzen oder deaktivieren).")
    
    # Validate legacy single Google Custom Search configuration
    # Only check legacy config if list-based config is not set
    has_list_config = bool(GCS_KEYS and GCS_CXS)
    has_legacy_api_key = bool(GCS_API_KEY and not GCS_CX)
    if not has_list_config and has_legacy_api_key:
        errs.append("GCS_CX fehlt trotz GCS_API_KEY (Legacy-Single-Config).")
    
    # Report errors
    if errs:
        if log_func:
            log_func("warn", "Konfiguration Hinweise", errors=errs)
        else:
            print(f"⚠️ Konfiguration Hinweise: {'; '.join(errs)}")


def parse_args() -> Any:
    """
    Parse command-line arguments for the scraper.
    
    Returns:
        Parsed arguments namespace
    """
    # Complete industry list synchronized with ScraperConfig.INDUSTRY_CHOICES
    # CRITICAL: This list MUST match ScraperConfig.INDUSTRY_CHOICES in telis_recruitment/scraper_control/models.py
    ALL_INDUSTRIES = [
        "all", "recruiter", "candidates", "talent_hunt", "handelsvertreter",
        "nrw", "social", "solar", "telekom", "versicherung",
        "bau", "ecom", "household", "d2d", "callcenter"
    ]
    
    ap = argparse.ArgumentParser(description="NRW Vertrieb-Leads Scraper (inkrementell + UI)")
    
    # UI and execution modes
    ap.add_argument("--ui", action="store_true", 
                    help="Web-UI starten (Start/Stop/Logs)")
    ap.add_argument("--once", action="store_true", 
                    help="Einmaliger Lauf im CLI")
    ap.add_argument("--interval", type=int, default=0, 
                    help="Pause in Sekunden zwischen den Durchläufen im Loop-Modus")
    
    # Control flags
    ap.add_argument("--force", action="store_true", 
                    help="Ignoriere History (queries_done)")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="Test-Modus ohne tatsächliche Ausführung (keine DB-Änderungen)")
    ap.add_argument("--tor", action="store_true", 
                    help="Leite Traffic über Tor (SOCKS5 127.0.0.1:9050)")
    ap.add_argument("--reset", action="store_true", 
                    help="Lösche queries_done und urls_seen vor dem Lauf")
    
    # Industry and query configuration
    ap.add_argument("--industry", 
                    choices=ALL_INDUSTRIES,
                    default=os.getenv("INDUSTRY", "all"),
                    help="Branche/Modus für diesen Run")
    ap.add_argument("--qpi", type=int, 
                    default=int(os.getenv("QPI", "6")),
                    help="Queries pro Branche in diesem Run (Standard: 6)")
    ap.add_argument("--daterestrict", type=str, 
                    default=os.getenv("DATE_RESTRICT", ""),
                    help="Google CSE dateRestrict, z.B. d30, w8, m3")
    
    # AI and search modes
    ap.add_argument("--smart", action="store_true", 
                    help="AI-generierte Dorks (selbstlernend) aktivieren")
    ap.add_argument("--no-google", action="store_true", 
                    help="Google CSE deaktivieren")
    ap.add_argument("--mode",
                    choices=["standard", "learning", "aggressive", "snippet_only"],
                    default="standard",
                    help="Betriebsmodus: standard, learning (lernt aus Erfolgen), aggressive (mehr Requests), snippet_only (nur Snippets)")
    
    # Login management
    ap.add_argument("--login", type=str, 
                    help="Manuell einloggen bei Portal (z.B. --login linkedin)")
    ap.add_argument("--clear-sessions", action="store_true", 
                    help="Alle gespeicherten Sessions löschen")
    ap.add_argument("--list-sessions", action="store_true", 
                    help="Alle Sessions anzeigen")
    
    return ap.parse_args()


def print_banner() -> None:
    """Print startup banner with version info."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                LUCA NRW SCRAPER v2.3                          ║
    ║         Leads-Scraper für Vertrieb/Callcenter/D2D            ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help() -> None:
    """Print usage help."""
    help_text = """
    Verwendung:
        python scriptname.py [OPTIONS]
        
    Modi:
        --ui               Web-Interface starten
        --once             Einmaliger Lauf (CLI)
        --mode MODE        Betriebsmodus: standard, learning, aggressive, snippet_only
        
    Branchen:
        --industry MODE    Industry/Mode: all, candidates, talent_hunt, recruiter
        --qpi N            Queries pro Branche (Standard: 6)
        
    Steuerung:
        --force            Historie ignorieren
        --reset            Historie löschen vor Lauf
        --smart            KI-generierte Dorks
        
    Login:
        --login PORTAL     Manuell einloggen (linkedin, xing, etc.)
        --list-sessions    Sessions anzeigen
        --clear-sessions   Alle Sessions löschen
        
    Beispiele:
        python scriptname.py --ui
        python scriptname.py --once --industry candidates --qpi 10
        python scriptname.py --once --industry talent_hunt --mode learning
    """
    print(help_text)
