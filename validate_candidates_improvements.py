#!/usr/bin/env python3
"""
Validation script for Candidates Mode Improvements
Demonstrates the new is_candidate_url() function and improved filtering
"""
from typing import Optional


def is_candidate_url(url: str) -> Optional[bool]:
    """
    Prüft ob URL ein Kandidaten-Profil sein könnte.
    Returns: True (candidate), False (definitely not), None (uncertain, needs further analysis)
    """
    if not url:
        return None
    
    url_lower = url.lower()
    
    # NEGATIV - Diese URLs blockieren (Stellenangebote, Firmen-Seiten)
    negative_patterns = [
        '/jobs/',                   # Stellenangebote, nicht Gesuche!
        '/stellenangebote/',        # Firmen-Anzeigen
        '/karriere/',               # Firmen-Karriereseiten
        '/company/',                # Firmen-Profile
        '/impressum',               # Firmen-Impressum (außer mit Kandidaten-Kontext)
        '/kontakt',                 # Firmen-Kontakt (außer mit Kandidaten-Kontext)
        '/about',                   # Über uns Seiten
        'jobboerse',                # Jobbörsen
        'stepstone.de',             # Jobbörsen
        'indeed.com',               # Jobbörsen
        'monster.de',               # Jobbörsen
        'linkedin.com/jobs/',       # Job listings
        'xing.com/jobs/',           # Job listings
    ]
    
    for neg in negative_patterns:
        if neg in url_lower:
            return False
    
    # POSITIV - Diese URLs sind gut für Kandidaten
    positive_patterns = [
        '/s-stellengesuche/',       # Kleinanzeigen Stellengesuche
        '/stellengesuche/',          # Andere Portale Stellengesuche
        'linkedin.com/in/',          # LinkedIn Profile (nicht /jobs/ oder /company/)
        'xing.com/profile/',         # Xing Profile
        '/freelancer/',              # Freelancer Profile
        'facebook.com/groups/',      # Facebook Gruppen
        't.me/',                     # Telegram Gruppen
        'chat.whatsapp.com/',        # WhatsApp Gruppen
        'instagram.com/',            # Instagram Profile (können Job-Sucher sein)
        'reddit.com/r/arbeitsleben', # Reddit Karriere-Threads
        'gutefrage.net',             # Fragen zu Jobsuche
        'freelancermap.de',          # Freelancer Portale
        'freelance.de',              # Freelancer Portale
        'gulp.de',                   # Freelancer Portale
    ]
    
    for pos in positive_patterns:
        if pos in url_lower:
            return True
    
    # Default: Nicht sicher, weitere Prüfung nötig
    return None


def main():
    """Demonstrate the candidate URL filtering improvements"""
    
    print("=" * 80)
    print("CANDIDATES MODE IMPROVEMENTS - VALIDATION SCRIPT")
    print("=" * 80)
    print()
    
    # Test cases showing the improvements
    test_cases = [
        ("GOOD CANDIDATES (Should ALLOW)", [
            "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/nrw",
            "https://www.markt.de/stellengesuche/verkauf-erfahrung",
            "https://www.linkedin.com/in/max-mustermann-sales-nrw",
            "https://www.xing.com/profile/Sarah_Schmidt",
            "https://www.freelancermap.de/freelancer/vertrieb-experte",
            "https://www.facebook.com/groups/vertrieb-jobs-nrw",
            "https://t.me/vertriebler_netzwerk",
            "https://www.reddit.com/r/arbeitsleben/comments/jobsuche",
        ]),
        ("BAD URLS (Should BLOCK)", [
            "https://www.viessmann.de/kontakt",  # ❌ Company contact page
            "https://www.heizung.de/impressum",  # ❌ Company imprint
            "https://www.stepstone.de/jobs/vertrieb",  # ❌ Job board
            "https://de.indeed.com/jobs?q=vertrieb",  # ❌ Job listings
            "https://www.monster.de/jobs/search",  # ❌ Job board
            "https://www.linkedin.com/jobs/view/123456",  # ❌ Job posting
            "https://www.company.de/karriere/stellenangebote",  # ❌ Company career page
        ]),
        ("UNCERTAIN (Need Analysis)", [
            "https://www.example.com/blog/vertrieb-tipps",
            "https://www.somesite.de/article.html",
        ]),
    ]
    
    for category, urls in test_cases:
        print(f"\n📋 {category}")
        print("-" * 80)
        for url in urls:
            result = is_candidate_url(url)
            icon = "✅" if result is True else "❌" if result is False else "⚠️"
            status = "CANDIDATE" if result is True else "BLOCKED" if result is False else "UNCERTAIN"
            print(f"{icon} [{status:9}] {url}")
    
    print()
    print("=" * 80)
    print("SUMMARY OF IMPROVEMENTS")
    print("=" * 80)
    print()
    print("✅ Added is_candidate_url() function with smart filtering")
    print("✅ Blocks job boards (StepStone, Indeed, Monster)")
    print("✅ Blocks company pages (impressum, karriere, stellenangebote)")
    print("✅ Allows Stellengesuche (job seeker ads)")
    print("✅ Allows professional profiles (LinkedIn /in/, Xing /profile/)")
    print("✅ Allows freelancer portals")
    print("✅ Allows social media job search groups")
    print()
    print("🎯 EXPECTED RESULT IN CANDIDATES MODE:")
    print("   Before: [INFO] Filter aktiv: Nur Candidates/Gruppen behalten {\"remaining\": 0}")
    print("   After:  [INFO] Filter aktiv: Nur Candidates/Gruppen behalten {\"remaining\": 12+}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
