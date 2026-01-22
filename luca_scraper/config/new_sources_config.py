# -*- coding: utf-8 -*-
"""
LUCA NRW Scraper - New Sources Configuration
=============================================
NEU: Erweiterte Quellen-Konfiguration für Handelsvertreter und B2B-Portale.

Diese Konfiguration ermöglicht:
- Prioritätsbasierte Dork-Auswahl (höhere Priorität → mehr CPU-Zeit)
- always_crawl: True → Titel-Guard/Garbage Context überspringen
- Strukturierte Quellen-Kategorien mit Domain-Listen
"""

from typing import Dict, List, Set, Any


# =========================
# NEW_SOURCES_CONFIG - Erweiterte Quellen für dork_set="new_sources"
# =========================

NEW_SOURCES_CONFIG: Dict[str, Dict[str, Any]] = {
    "handelsvertreter_portale": {
        "domains": ["handelsvertreter.de", "cdh.de", "handelsvertreter-netzwerk.de"],
        "dorks": [
            'site:handelsvertreter.de (NRW OR Köln OR Düsseldorf OR Essen) (Telefon OR Mobil OR @)',
            'site:cdh.de (Institutionen OR Mitglieder OR Partner) (NRW OR Ruhrgebiet) (Telefon OR Kontakt)',
            'site:handelsvertreter-netzwerk.de (NRW OR Köln) (Profil OR Kontakt)'
        ],
        "priority": 5,
        "always_crawl": True
    },
    "b2b_verzeichnisse": {
        "domains": ["gelbeseiten.de", "dasoertliche.de", "11880.com"],
        "dorks": [
            'site:gelbeseiten.de (Handelsvertreter OR Außendienst) ("40000" OR "50000") (Telefon OR Mobil)',
            'site:dasoertliche.de (Vertrieb OR Gebietsvertreter) (Köln OR Düsseldorf) Telefon',
            'site:11880.com (Außendienst OR Vertrieb) NRW (Telefon OR Kontakt)'
        ],
        "priority": 4,
        "always_crawl": True
    },
    "firmenlisten": {
        "domains": ["listflix.de", "adressbar.de", "firmendatenbanken.de", "datenparty.com"],
        "dorks": [
            'site:listflix.de handelsvertreter (NRW OR Köln OR Düsseldorf)',
            'site:adressbar.de Handelsvertreter (Nordrhein-Westfalen OR Ruhrgebiet)',
            'site:firmendatenbanken.de/firmen/liste/handelsvertreter NRW',
            'site:datenparty.com handelsvertreter (Telefon OR E-Mail)'
        ],
        "priority": 4,
        "always_crawl": False
    },
    "lokale_nrw": {
        "domains": ["koeln.business", "it.nrw"],
        "dorks": [
            'site:koeln.business (Vertrieb OR Außendienst) (Telefon OR Kontakt)',
            'site:it.nrw/thema/unternehmensregister (Vertrieb OR Handelsvertreter) (Köln OR Düsseldorf)'
        ],
        "priority": 3,
        "always_crawl": False
    },
    "verbaende": {
        "domains": ["direktvertrieb.de", "vertriebsoffice.de"],
        "dorks": [
            'site:direktvertrieb.de (Kooperationspartner OR Mitglieder) (Telefon OR Kontakt)',
            'site:vertriebsoffice.de/branchenbuch/Direktvertrieb (NRW OR Köln)'
        ],
        "priority": 3,
        "always_crawl": False
    }
}


# =========================
# HELPER FUNCTIONS
# =========================

def get_new_sources_dorks() -> List[str]:
    """
    NEU: Lädt alle Dorks aus NEW_SOURCES_CONFIG.
    
    Returns:
        Liste aller Dorks aus allen Kategorien
    """
    all_dorks: List[str] = []
    for category, config in NEW_SOURCES_CONFIG.items():
        all_dorks.extend(config.get("dorks", []))
    return all_dorks


def get_new_sources_dorks_by_priority() -> List[Dict[str, Any]]:
    """
    NEU: Lädt alle Dorks mit Metadaten, sortiert nach Priorität (absteigend).
    
    Höhere Priorität → mehr CPU-Zeit / bevorzugte Verarbeitung.
    
    Returns:
        Liste von Dicts mit keys: dork, category, priority, always_crawl, domains
    """
    dorks_with_meta: List[Dict[str, Any]] = []
    
    for category, config in NEW_SOURCES_CONFIG.items():
        priority = config.get("priority", 1)
        always_crawl = config.get("always_crawl", False)
        domains = config.get("domains", [])
        
        for dork in config.get("dorks", []):
            dorks_with_meta.append({
                "dork": dork,
                "category": category,
                "priority": priority,
                "always_crawl": always_crawl,
                "domains": domains,
            })
    
    # NEU: Sortiere nach Priorität (höchste zuerst)
    dorks_with_meta.sort(key=lambda x: x["priority"], reverse=True)
    return dorks_with_meta


def get_always_crawl_domains() -> Set[str]:
    """
    NEU: Gibt alle Domains zurück, die always_crawl: True haben.
    
    Diese Domains umgehen Titel-Guard und Garbage Context Filter.
    
    Returns:
        Set von Domains mit always_crawl: True
    """
    always_crawl_domains: Set[str] = set()
    
    for category, config in NEW_SOURCES_CONFIG.items():
        if config.get("always_crawl", False):
            for domain in config.get("domains", []):
                always_crawl_domains.add(domain.lower())
    
    return always_crawl_domains


def get_source_category_for_url(url: str) -> str:
    """
    NEU: Bestimmt die Quellen-Kategorie für eine URL.
    
    Args:
        url: Die zu prüfende URL
        
    Returns:
        Kategorie-Name oder "unknown"
    """
    url_lower = url.lower()
    
    for category, config in NEW_SOURCES_CONFIG.items():
        for domain in config.get("domains", []):
            if domain.lower() in url_lower:
                return category
    
    return "unknown"


def get_source_priority_for_url(url: str) -> int:
    """
    NEU: Bestimmt die Quellen-Priorität für eine URL.
    
    Args:
        url: Die zu prüfende URL
        
    Returns:
        Priorität (1-5) oder 0 für unbekannte Quellen
    """
    url_lower = url.lower()
    
    for category, config in NEW_SOURCES_CONFIG.items():
        for domain in config.get("domains", []):
            if domain.lower() in url_lower:
                return config.get("priority", 1)
    
    return 0


def is_always_crawl_url(url: str) -> bool:
    """
    NEU: Prüft ob eine URL zu einer always_crawl Domain gehört.
    
    Args:
        url: Die zu prüfende URL
        
    Returns:
        True wenn always_crawl, sonst False
    """
    always_crawl_domains = get_always_crawl_domains()
    url_lower = url.lower()
    
    for domain in always_crawl_domains:
        if domain in url_lower:
            return True
    
    return False


def get_dork_metadata(dork: str) -> Dict[str, Any]:
    """
    NEU: Findet Metadaten für einen spezifischen Dork.
    
    Args:
        dork: Der Dork-String
        
    Returns:
        Dict mit category, priority, always_crawl, domains oder leeres Dict
    """
    for category, config in NEW_SOURCES_CONFIG.items():
        if dork in config.get("dorks", []):
            return {
                "category": category,
                "priority": config.get("priority", 1),
                "always_crawl": config.get("always_crawl", False),
                "domains": config.get("domains", []),
            }
    
    return {}


# =========================
# EXPORTS
# =========================

__all__ = [
    "NEW_SOURCES_CONFIG",
    "get_new_sources_dorks",
    "get_new_sources_dorks_by_priority",
    "get_always_crawl_domains",
    "get_source_category_for_url",
    "get_source_priority_for_url",
    "is_always_crawl_url",
    "get_dork_metadata",
]
