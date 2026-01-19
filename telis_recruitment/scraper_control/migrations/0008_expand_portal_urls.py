# Generated migration for expanding PortalSource URLs
# Migrates hardcoded URLs from config.py to database

from django.db import migrations


def expand_portal_urls(apps, schema_editor):
    """
    Expand PortalSource records with complete URL lists from config.py.
    This migration adds all hardcoded URLs to the PortalSource.urls JSONField
    so they can be managed via the database without code changes.
    """
    PortalSource = apps.get_model('scraper_control', 'PortalSource')
    
    # Complete URL lists from luca_scraper/config.py
    PORTAL_URL_DATA = {
        'kleinanzeigen': {
            'display_name': 'Kleinanzeigen.de',
            'base_url': 'https://www.kleinanzeigen.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                # Stellengesuche NRW - Vertrieb/Sales
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/vertrieb/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/sales/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/verkauf/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/aussendienst/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/kundenberater/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/handelsvertreter/k0c107l929",
                # Bundesweit (mehr Volumen)
                "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/k0c107",
                "https://www.kleinanzeigen.de/s-stellengesuche/sales/k0c107",
                "https://www.kleinanzeigen.de/s-stellengesuche/verkauf/k0c107",
                "https://www.kleinanzeigen.de/s-stellengesuche/handelsvertreter/k0c107",
                "https://www.kleinanzeigen.de/s-stellengesuche/akquise/k0c107",
                "https://www.kleinanzeigen.de/s-stellengesuche/telesales/k0c107",
                "https://www.kleinanzeigen.de/s-stellengesuche/call-center/k0c107",
                # Alle großen NRW-Städte
                # Köln
                "https://www.kleinanzeigen.de/s-stellengesuche/koeln/vertrieb/k0c107l945",
                "https://www.kleinanzeigen.de/s-stellengesuche/koeln/sales/k0c107l945",
                "https://www.kleinanzeigen.de/s-stellengesuche/koeln/verkauf/k0c107l945",
                # Dortmund
                "https://www.kleinanzeigen.de/s-stellengesuche/dortmund/vertrieb/k0c107l947",
                "https://www.kleinanzeigen.de/s-stellengesuche/dortmund/sales/k0c107l947",
                # Essen
                "https://www.kleinanzeigen.de/s-stellengesuche/essen/vertrieb/k0c107l939",
                "https://www.kleinanzeigen.de/s-stellengesuche/essen/sales/k0c107l939",
                # Duisburg
                "https://www.kleinanzeigen.de/s-stellengesuche/duisburg/vertrieb/k0c107l940",
                # Bochum
                "https://www.kleinanzeigen.de/s-stellengesuche/bochum/vertrieb/k0c107l941",
                # Wuppertal
                "https://www.kleinanzeigen.de/s-stellengesuche/wuppertal/vertrieb/k0c107l942",
                # Bielefeld
                "https://www.kleinanzeigen.de/s-stellengesuche/bielefeld/vertrieb/k0c107l943",
                # Bonn
                "https://www.kleinanzeigen.de/s-stellengesuche/bonn/vertrieb/k0c107l944",
                # Münster
                "https://www.kleinanzeigen.de/s-stellengesuche/muenster/vertrieb/k0c107l946",
                # Gelsenkirchen
                "https://www.kleinanzeigen.de/s-stellengesuche/gelsenkirchen/vertrieb/k0c107l948",
                # Mönchengladbach
                "https://www.kleinanzeigen.de/s-stellengesuche/moenchengladbach/vertrieb/k0c107l949",
                # Aachen
                "https://www.kleinanzeigen.de/s-stellengesuche/aachen/vertrieb/k0c107l950",
                # Krefeld
                "https://www.kleinanzeigen.de/s-stellengesuche/krefeld/vertrieb/k0c107l951",
                # Oberhausen
                "https://www.kleinanzeigen.de/s-stellengesuche/oberhausen/vertrieb/k0c107l952",
                # Hagen
                "https://www.kleinanzeigen.de/s-stellengesuche/hagen/vertrieb/k0c107l953",
                # Hamm
                "https://www.kleinanzeigen.de/s-stellengesuche/hamm/vertrieb/k0c107l954",
                # Zusätzliche Berufsfelder NRW
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/kundenservice/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/call-center/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/promotion/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/telefonverkauf/k0c107l929",
            ]
        },
        'markt_de': {
            'display_name': 'Markt.de',
            'base_url': 'https://www.markt.de',
            'rate_limit_seconds': 4.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                # NRW
                "https://www.markt.de/stellengesuche/nordrhein-westfalen/vertrieb/",
                "https://www.markt.de/stellengesuche/nordrhein-westfalen/sales/",
                "https://www.markt.de/stellengesuche/nordrhein-westfalen/verkauf/",
                "https://www.markt.de/stellengesuche/nordrhein-westfalen/kundenberater/",
                # Bundesweit
                "https://www.markt.de/stellengesuche/vertrieb/",
                "https://www.markt.de/stellengesuche/sales/",
                "https://www.markt.de/stellengesuche/handelsvertreter/",
            ]
        },
        'quoka': {
            'display_name': 'Quoka.de',
            'base_url': 'https://www.quoka.de',
            'rate_limit_seconds': 6.0,
            'max_results': 20,
            'difficulty': 'high',
            'urls': [
                # NRW Städte
                "https://www.quoka.de/stellengesuche/duesseldorf/",
                "https://www.quoka.de/stellengesuche/koeln/",
                "https://www.quoka.de/stellengesuche/dortmund/",
                "https://www.quoka.de/stellengesuche/essen/",
                "https://www.quoka.de/stellengesuche/duisburg/",
                "https://www.quoka.de/stellengesuche/bochum/",
                "https://www.quoka.de/stellengesuche/wuppertal/",
                "https://www.quoka.de/stellengesuche/bielefeld/",
                "https://www.quoka.de/stellengesuche/bonn/",
                "https://www.quoka.de/stellengesuche/muenster/",
                "https://www.quoka.de/stellengesuche/gelsenkirchen/",
                "https://www.quoka.de/stellengesuche/moenchengladbach/",
                "https://www.quoka.de/stellengesuche/aachen/",
                # Kategorien
                "https://www.quoka.de/stellengesuche/vertrieb-verkauf/",
                "https://www.quoka.de/stellengesuche/kundenservice/",
            ]
        },
        'kalaydo': {
            'display_name': 'Kalaydo.de',
            'base_url': 'https://www.kalaydo.de',
            'rate_limit_seconds': 4.0,
            'max_results': 20,
            'difficulty': 'high',
            'is_active': False,  # Deaktiviert - blockiert Requests
            'urls': [
                "https://www.kalaydo.de/stellengesuche/nordrhein-westfalen/",
                "https://www.kalaydo.de/stellengesuche/koeln/",
                "https://www.kalaydo.de/stellengesuche/duesseldorf/",
                "https://www.kalaydo.de/stellengesuche/bonn/",
                "https://www.kalaydo.de/stellengesuche/aachen/",
            ]
        },
        'meinestadt': {
            'display_name': 'Meinestadt.de',
            'base_url': 'https://www.meinestadt.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.meinestadt.de/duesseldorf/stellengesuche",
                "https://www.meinestadt.de/koeln/stellengesuche",
                "https://www.meinestadt.de/dortmund/stellengesuche",
                "https://www.meinestadt.de/essen/stellengesuche",
                "https://www.meinestadt.de/duisburg/stellengesuche",
                "https://www.meinestadt.de/bochum/stellengesuche",
                "https://www.meinestadt.de/wuppertal/stellengesuche",
                "https://www.meinestadt.de/bielefeld/stellengesuche",
                "https://www.meinestadt.de/bonn/stellengesuche",
                "https://www.meinestadt.de/muenster/stellengesuche",
                "https://www.meinestadt.de/gelsenkirchen/stellengesuche",
                "https://www.meinestadt.de/moenchengladbach/stellengesuche",
                "https://www.meinestadt.de/aachen/stellengesuche",
                "https://www.meinestadt.de/krefeld/stellengesuche",
                "https://www.meinestadt.de/oberhausen/stellengesuche",
            ]
        },
        'dhd24': {
            'display_name': 'DHD24.com',
            'base_url': 'https://www.dhd24.com',
            'rate_limit_seconds': 4.0,
            'max_results': 20,
            'difficulty': 'medium',
            'is_active': False,  # Deaktiviert - oft blockiert
            'urls': [
                "https://www.dhd24.com/kleinanzeigen/stellengesuche.html",
                "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-vertrieb.html",
                "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-verkauf.html",
            ]
        },
        'freelancermap': {
            'display_name': 'Freelancermap.de',
            'base_url': 'https://www.freelancermap.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'low',
            'urls': [
                "https://www.freelancermap.de/freelancer-verzeichnis/sales.html",
                "https://www.freelancermap.de/freelancer-verzeichnis/vertrieb.html",
                "https://www.freelancermap.de/freelancer-verzeichnis/business-development.html",
                "https://www.freelancermap.de/freelancer-verzeichnis/account-management.html",
                "https://www.freelancermap.de/freelancer-verzeichnis/key-account-management.html",
                # NRW specific
                "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-vertrieb.html",
                "https://www.freelancermap.de/freelancer-verzeichnis/nordrhein-westfalen-sales.html",
            ]
        },
        'freelance_de': {
            'display_name': 'Freelance.de',
            'base_url': 'https://www.freelance.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'low',
            'urls': [
                "https://www.freelance.de/Freiberufler/Vertrieb/",
                "https://www.freelance.de/Freiberufler/Sales/",
                "https://www.freelance.de/Freiberufler/Key-Account/",
                "https://www.freelance.de/Freiberufler/Business-Development/",
                "https://www.freelance.de/Freiberufler/Account-Manager/",
                # NRW specific
                "https://www.freelance.de/Freiberufler/NRW/Vertrieb/",
                "https://www.freelance.de/Freiberufler/NRW/Sales/",
            ]
        },
        # Additional portals from PORTAL_CONFIGS in scriptname.py
        'indeed': {
            'display_name': 'Indeed Deutschland',
            'base_url': 'https://de.indeed.com',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://de.indeed.com/Jobs?q=stellengesuch&l=Nordrhein-Westfalen",
                "https://de.indeed.com/Jobs?q=suche+arbeit+vertrieb&l=NRW",
                "https://de.indeed.com/Jobs?q=vertrieb+verf%C3%BCgbar&l=D%C3%BCsseldorf",
                "https://de.indeed.com/Jobs?q=sales+offen&l=K%C3%B6ln",
            ]
        },
        'stepstone': {
            'display_name': 'StepStone',
            'base_url': 'https://www.stepstone.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.stepstone.de/jobs/vertrieb/in-nordrhein-westfalen",
                "https://www.stepstone.de/jobs/sales/in-nrw",
                "https://www.stepstone.de/jobs/au%C3%9Fendienst/in-nordrhein-westfalen",
            ]
        },
        'arbeitsagentur': {
            'display_name': 'Bundesagentur für Arbeit',
            'base_url': 'https://www.arbeitsagentur.de',
            'rate_limit_seconds': 2.0,
            'max_results': 20,
            'difficulty': 'low',
            'urls': [
                "https://www.arbeitsagentur.de/jobsuche/suche?was=Vertrieb&wo=Nordrhein-Westfalen",
                "https://www.arbeitsagentur.de/jobsuche/suche?was=Sales&wo=NRW",
            ]
        },
        'monster': {
            'display_name': 'Monster.de',
            'base_url': 'https://www.monster.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.monster.de/jobs/suche/?q=vertrieb&where=nordrhein-westfalen",
                "https://www.monster.de/jobs/suche/?q=sales&where=nrw",
            ]
        },
        'stellenanzeigen': {
            'display_name': 'Stellenanzeigen.de',
            'base_url': 'https://www.stellenanzeigen.de',
            'rate_limit_seconds': 2.5,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.stellenanzeigen.de/jobs-vertrieb-nordrhein-westfalen/",
                "https://www.stellenanzeigen.de/jobs-sales-nrw/",
            ]
        },
    }
    
    # Update or create portal sources with complete URL lists
    for portal_name, portal_data in PORTAL_URL_DATA.items():
        # Get defaults for fields not in portal_data
        defaults = {
            'display_name': portal_data.get('display_name', portal_name.replace('_', ' ').title()),
            'base_url': portal_data.get('base_url', ''),
            'rate_limit_seconds': portal_data.get('rate_limit_seconds', 3.0),
            'max_results': portal_data.get('max_results', 20),
            'difficulty': portal_data.get('difficulty', 'medium'),
            'urls': portal_data.get('urls', []),
            'is_active': portal_data.get('is_active', True),
        }
        
        # Try to update existing record or create new one
        portal, created = PortalSource.objects.get_or_create(
            name=portal_name,
            defaults=defaults
        )
        
        if not created:
            # Update existing portal with complete URL list (if current list is shorter)
            if len(portal.urls or []) < len(defaults['urls']):
                portal.urls = defaults['urls']
                portal.rate_limit_seconds = defaults['rate_limit_seconds']
                portal.max_results = defaults['max_results']
                portal.difficulty = defaults['difficulty']
                portal.save()


def reverse_expand_portal_urls(apps, schema_editor):
    """
    Reverse migration: Remove expanded URLs (set back to minimal list).
    Note: This only removes the extra URLs, doesn't delete the portal records.
    """
    # No-op: We don't want to lose user-modified URLs on rollback
    pass


class Migration(migrations.Migration):

    dependencies = [
        # Both 0007 migrations must be applied before this migration.
        # This is a standard Django pattern for handling branch merges.
        ('scraper_control', '0007_init_config_from_env'),
        ('scraper_control', '0007_observability_enhancements'),
    ]

    operations = [
        migrations.RunPython(expand_portal_urls, reverse_expand_portal_urls),
    ]
