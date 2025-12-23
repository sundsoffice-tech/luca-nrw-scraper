# -*- coding: utf-8 -*-
"""
Social Media Lead-Extraktion

Dieses Modul bietet URLs und Dorks für Social Media Plattformen:
- Facebook Gruppen und Posts
- LinkedIn Job-Sucher
- XING Kandidaten
- Telegram Kanäle
"""

from typing import List, Dict
from urllib.parse import quote_plus


class SocialMediaScraper:
    """Scraper-Helfer für Social Media Plattformen"""
    
    def __init__(self):
        pass
    
    # ==================== FACEBOOK ====================
    
    def get_facebook_group_urls(self) -> List[str]:
        """
        Facebook Gruppen für Jobsuche NRW
        
        Returns:
            Liste der Facebook Gruppen URLs
        """
        return [
            "https://www.facebook.com/groups/jobsuche.nrw",
            "https://www.facebook.com/groups/jobs.duesseldorf",
            "https://www.facebook.com/groups/jobs.koeln",
            "https://www.facebook.com/groups/arbeit.nrw",
            "https://www.facebook.com/groups/minijobs.nrw",
            "https://www.facebook.com/groups/stellensuche.nrw",
            "https://www.facebook.com/groups/vertriebsjobs.deutschland",
        ]
    
    def build_facebook_search_urls(self, keywords: List[str]) -> List[str]:
        """
        Erstellt Facebook Suchanfragen
        
        Args:
            keywords: Liste von Suchbegriffen
        
        Returns:
            Liste der Such-URLs
        """
        base = "https://www.facebook.com/search/posts/?q="
        urls = []
        
        for kw in keywords:
            query = quote_plus(f"{kw} suche arbeit NRW telefon")
            urls.append(f"{base}{query}")
        
        return urls
    
    # ==================== LINKEDIN ====================
    
    def build_linkedin_search_urls(self) -> List[str]:
        """
        LinkedIn Job-Sucher URLs
        
        Returns:
            Liste der LinkedIn Such-URLs
        """
        return [
            # NRW ist Geo-URN 101282230
            "https://www.linkedin.com/search/results/people/?keywords=vertrieb%20offen%20f%C3%BCr%20angebote&origin=GLOBAL_SEARCH_HEADER&geoUrn=%5B%22101282230%22%5D",
            "https://www.linkedin.com/search/results/people/?keywords=sales%20open%20to%20work&origin=GLOBAL_SEARCH_HEADER&geoUrn=%5B%22101282230%22%5D",
            "https://www.linkedin.com/search/results/people/?keywords=au%C3%9Fendienst%20suche%20job&origin=GLOBAL_SEARCH_HEADER&geoUrn=%5B%22101282230%22%5D",
            "https://www.linkedin.com/search/results/people/?keywords=key%20account%20manager%20offen&origin=GLOBAL_SEARCH_HEADER&geoUrn=%5B%22101282230%22%5D",
        ]
    
    # ==================== XING ====================
    
    def build_xing_search_urls(self) -> List[str]:
        """
        XING Kandidaten-Suche
        
        Returns:
            Liste der XING Such-URLs
        """
        return [
            "https://www.xing.com/search/members?keywords=vertrieb%20auf%20jobsuche&location=Nordrhein-Westfalen",
            "https://www.xing.com/search/members?keywords=sales%20offen%20f%C3%BCr%20angebote&location=NRW",
            "https://www.xing.com/search/members?keywords=au%C3%9Fendienst%20suche%20position&location=Nordrhein-Westfalen",
            "https://www.xing.com/search/members?keywords=vertriebsmitarbeiter%20verf%C3%BCgbar&location=NRW",
        ]
    
    # ==================== TELEGRAM ====================
    
    def get_telegram_channels(self) -> List[str]:
        """
        Telegram Kanäle für Jobs
        
        Returns:
            Liste der Telegram Kanal-URLs
        """
        return [
            "https://t.me/jobsnrw",
            "https://t.me/arbeit_deutschland",
            "https://t.me/minijobs_de",
            "https://t.me/vertriebsjobs",
            "https://t.me/salesjobs_deutschland",
        ]
    
    # ==================== HELPER METHODS ====================
    
    def get_all_social_urls(self) -> List[str]:
        """
        Gibt alle Social Media URLs zurück
        
        Returns:
            Kombinierte Liste aller URLs
        """
        urls = []
        urls.extend(self.get_facebook_group_urls())
        urls.extend(self.build_linkedin_search_urls())
        urls.extend(self.build_xing_search_urls())
        urls.extend(self.get_telegram_channels())
        return urls


# Google Dorks für Social Media
SOCIAL_MEDIA_DORKS = [
    # ==================== FACEBOOK ====================
    'site:facebook.com "suche job" telefon NRW',
    'site:facebook.com "suche arbeit" kontakt Düsseldorf',
    'site:facebook.com/groups "stellengesuch" vertrieb',
    'site:facebook.com "arbeit gesucht" mobil Köln',
    'site:facebook.com "verfügbar ab" kontakt Dortmund',
    'site:facebook.com "suche neue herausforderung" telefon vertrieb',
    'site:facebook.com "job gesucht" mobil NRW',
    
    # ==================== LINKEDIN ====================
    'site:linkedin.com "open to work" vertrieb nordrhein-westfalen',
    'site:linkedin.com "offen für angebote" sales NRW',
    'site:linkedin.com "auf jobsuche" kontakt',
    'site:linkedin.com "suche neue herausforderung" vertrieb',
    'site:linkedin.com/in/ "verfügbar" sales telefon',
    'site:linkedin.com "actively looking" sales germany',
    
    # ==================== XING ====================
    'site:xing.com "auf jobsuche" vertrieb NRW',
    'site:xing.com "suche neue herausforderung" sales',
    'site:xing.com/profile "offen für angebote" kontakt',
    'site:xing.com "verfügbar ab" vertrieb telefon',
    'site:xing.com "suche position" außendienst NRW',
    
    # ==================== EBAY KLEINANZEIGEN (OLD DOMAIN) ====================
    'site:ebay-kleinanzeigen.de stellengesuch telefon NRW',
    'site:ebay-kleinanzeigen.de "suche arbeit" kontakt',
    
    # ==================== REDDIT ====================
    'site:reddit.com/r/germany "looking for job" NRW',
    'site:reddit.com/r/de "suche arbeit" NRW',
    'site:reddit.com "job gesucht" deutschland vertrieb',
    
    # ==================== TWITTER/X ====================
    'site:twitter.com "suche job" NRW telefon',
    'site:twitter.com "#jobgesucht" vertrieb kontakt',
    'site:x.com "looking for job" germany sales',
    
    # ==================== INSTAGRAM ====================
    'site:instagram.com "suche job" telefon',
    'site:instagram.com "#jobgesucht" kontakt',
    
    # ==================== KOMBINIERTE SOCIAL MEDIA ====================
    '(site:facebook.com OR site:linkedin.com OR site:xing.com) "suche job" telefon NRW',
    '(site:facebook.com OR site:linkedin.com) stellengesuch vertrieb kontakt',
]


# Branchen-spezifische Social Media Dorks
INDUSTRY_SOCIAL_DORKS = {
    "vertrieb": [
        'site:linkedin.com "vertriebsmitarbeiter" "offen für angebote" NRW',
        'site:xing.com "key account manager" "suche position" telefon',
        'site:facebook.com "außendienst" "verfügbar" kontakt NRW',
    ],
    "callcenter": [
        'site:linkedin.com "call center agent" "looking for" germany',
        'site:facebook.com "callcenter" "suche job" telefon',
        'site:xing.com "kundenservice" "auf jobsuche" NRW',
    ],
    "d2d": [
        'site:facebook.com "door to door" "suche job" telefon',
        'site:linkedin.com "field sales" "available" germany',
        'site:xing.com "außendienst" "verfügbar" kontakt',
    ],
}


def get_social_dorks_for_industry(industry: str) -> List[str]:
    """
    Gibt Social Media Dorks für eine spezifische Branche zurück
    
    Args:
        industry: Branche (vertrieb, callcenter, d2d)
    
    Returns:
        Liste der branchen-spezifischen Dorks
    """
    return INDUSTRY_SOCIAL_DORKS.get(industry.lower(), [])


def get_all_social_dorks() -> List[str]:
    """
    Gibt alle Social Media Dorks zurück
    
    Returns:
        Kombinierte Liste aller Social Media Dorks
    """
    all_dorks = SOCIAL_MEDIA_DORKS.copy()
    
    # Füge branchen-spezifische Dorks hinzu
    for dorks in INDUSTRY_SOCIAL_DORKS.values():
        all_dorks.extend(dorks)
    
    return all_dorks


# Platform-spezifische Konfiguration
PLATFORM_CONFIG = {
    "facebook": {
        "rate_limit": 2.0,  # Sekunden zwischen Requests
        "requires_login": True,
        "difficulty": "high",  # Schwierig zu scrapen
    },
    "linkedin": {
        "rate_limit": 3.0,
        "requires_login": True,
        "difficulty": "very_high",  # Sehr schwierig
    },
    "xing": {
        "rate_limit": 2.5,
        "requires_login": True,
        "difficulty": "high",
    },
    "telegram": {
        "rate_limit": 1.0,
        "requires_login": False,
        "difficulty": "medium",
    },
    "reddit": {
        "rate_limit": 1.5,
        "requires_login": False,
        "difficulty": "low",  # Relativ einfach
    },
}


def get_platform_config(platform: str) -> Dict:
    """
    Gibt Konfiguration für eine Plattform zurück
    
    Args:
        platform: Plattform-Name (facebook, linkedin, xing, etc.)
    
    Returns:
        Konfigurations-Dictionary
    """
    return PLATFORM_CONFIG.get(platform.lower(), {
        "rate_limit": 2.0,
        "requires_login": False,
        "difficulty": "medium",
    })
