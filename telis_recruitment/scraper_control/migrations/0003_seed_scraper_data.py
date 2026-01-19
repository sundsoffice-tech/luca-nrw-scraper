# Generated migration for seeding scraper data

from django.db import migrations
from django.utils.text import slugify


def seed_regions(apps, schema_editor):
    """Seed NRW cities as SearchRegion."""
    SearchRegion = apps.get_model('scraper_control', 'SearchRegion')
    
    # NRW_CITIES - base cities
    base_cities = [
        "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg",
        "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
        "Gelsenkirchen", "Aachen", "Mönchengladbach"
    ]
    
    # METROPOLIS - big cities with more queries
    metropolis_cities = [
        "Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", 
        "Bochum", "Bonn", "Münster"
    ]
    
    # NRW_CITIES_EXTENDED - additional cities
    extended_cities = [
        "Krefeld", "Oberhausen", "Hagen", "Hamm", "Mülheim an der Ruhr", 
        "Leverkusen", "Solingen", "Neuss", "Paderborn", "Recklinghausen", 
        "Remscheid", "Moers", "Siegen", "Witten", "Iserlohn", 
        "Bergisch Gladbach", "Herne"
    ]
    
    # Create regions
    for city in base_cities:
        is_metro = city in metropolis_cities
        SearchRegion.objects.get_or_create(
            name=city,
            defaults={
                'slug': slugify(city),
                'is_active': True,
                'is_metropolis': is_metro,
                'priority': 100 if is_metro else 50,
            }
        )
    
    for city in extended_cities:
        if city not in base_cities:
            SearchRegion.objects.get_or_create(
                name=city,
                defaults={
                    'slug': slugify(city),
                    'is_active': True,
                    'is_metropolis': False,
                    'priority': 10,
                }
            )


def seed_dorks(apps, schema_editor):
    """Seed default search dorks."""
    SearchDork = apps.get_model('scraper_control', 'SearchDork')
    
    # Default queries from manager.py
    default_queries = [
        # Agency & Partner Lists (B2B)
        ('site:de "Unsere Vertriebspartner" "PLZ" "Mobil" -jobs', 'default', 'Vertriebspartner Listen'),
        ('site:de "Unsere Vertretungen" "Industrievertretung" "Kontakt"', 'default', 'Vertretungen'),
        ('site:de "Vertriebsnetz" "Handelsvertretung" "Ansprechpartner"', 'default', 'Vertriebsnetz'),
        ('site:de "Gebietsvertretung" "PLZ" "Telefon" -stepstone -indeed', 'default', 'Gebietsvertretung'),
        ('site:de "Vertragshändler" "Maschinenbau" "Ansprechpartner"', 'default', 'Vertragshändler'),
        ('filetype:pdf "Vertreterliste" "Mobil" "PLZ" -bewerbung', 'default', 'Vertreterliste PDF'),
        ('filetype:pdf "Preisliste" "Industrievertretung" "Kontakt"', 'default', 'Preisliste PDF'),
        ('filetype:xlsx "Händlerverzeichnis" "Ansprechpartner" "Mobil"', 'default', 'Händlerverzeichnis Excel'),
        ('"Inhaltlich Verantwortlicher" "Handelsvertretung" "Mobil" -GmbH -UG', 'default', 'Impressum Handelsvertretung'),
        ('"Angaben gemäß § 5 TMG" "Handelsvertretung" "Inhaber" "Mobil"', 'default', 'TMG Handelsvertretung'),
        ('inurl:impressum "Handelsvertretung" "powered by WordPress" "Mobil"', 'default', 'WordPress Handelsvertretung'),
        ('site:cdh.de "Mitglied" "Kontakt"', 'default', 'CDH Mitglieder'),
    ]
    
    # Candidates queries
    candidates_queries = [
        # Kleinanzeigen.de
        ('site:kleinanzeigen.de/s-stellengesuche "vertrieb" "NRW"', 'candidates', 'Kleinanzeigen Vertrieb NRW'),
        ('site:kleinanzeigen.de/s-stellengesuche "sales" "nordrhein-westfalen"', 'candidates', 'Kleinanzeigen Sales NRW'),
        ('site:kleinanzeigen.de/s-stellengesuche "außendienst" "erfahrung"', 'candidates', 'Kleinanzeigen Außendienst'),
        ('site:kleinanzeigen.de/s-stellengesuche "key account" "suche"', 'candidates', 'Kleinanzeigen Key Account'),
        ('site:kleinanzeigen.de/s-stellengesuche "handelsvertreter" "freiberuflich"', 'candidates', 'Kleinanzeigen Handelsvertreter'),
        
        # Markt.de
        ('site:markt.de/stellengesuche "vertrieb"', 'candidates', 'Markt.de Vertrieb'),
        ('site:markt.de/stellengesuche "sales manager"', 'candidates', 'Markt.de Sales Manager'),
        
        # Quoka
        ('site:quoka.de/stellengesuche "vertrieb"', 'candidates', 'Quoka Vertrieb'),
        ('site:quoka.de/stellengesuche "verkauf" "erfahrung"', 'candidates', 'Quoka Verkauf'),
        
        # Xing
        ('site:xing.com/profile "offen für angebote" "vertrieb" "NRW"', 'candidates', 'Xing offen für Angebote'),
        ('site:xing.com/profile "auf jobsuche" "sales"', 'candidates', 'Xing auf Jobsuche'),
        ('site:xing.com/profile "suche neue herausforderung" "key account"', 'candidates', 'Xing neue Herausforderung'),
        
        # LinkedIn
        ('site:linkedin.com/in "open to work" "sales" "germany"', 'candidates', 'LinkedIn Open to Work'),
        ('site:linkedin.com/in "offen für" "vertrieb" "NRW"', 'candidates', 'LinkedIn offen für Vertrieb'),
        ('site:linkedin.com/in "#opentowork" "vertrieb"', 'candidates', 'LinkedIn #opentowork'),
    ]
    
    # Social media queries
    social_queries = [
        ('site:facebook.com "suche neue herausforderung" "vertrieb"', 'social', 'Facebook Jobsuche'),
        ('site:facebook.com "suche arbeit" "sales" "NRW"', 'social', 'Facebook Arbeit suchen'),
        ('site:instagram.com "open for work" "sales"', 'social', 'Instagram Open for Work'),
        ('site:tiktok.com "jobsuche" "vertrieb"', 'social', 'TikTok Jobsuche'),
    ]
    
    # Portal-specific queries
    portal_queries = [
        ('site:freelancermap.de "vertrieb" "verfügbar"', 'portal', 'Freelancermap Vertrieb'),
        ('site:freelance.de "vertriebsexperte" "profil"', 'portal', 'Freelance.de Experte'),
        ('site:gulp.de "sales" "verfügbar"', 'portal', 'Gulp Sales'),
    ]
    
    # Recruiter queries
    recruiter_queries = [
        ('site:de "Personalvermittlung" "Vertrieb" "NRW" "Kontakt"', 'recruiter', 'Personalvermittlung Vertrieb'),
        ('site:de "Headhunter" "Sales" "Spezialist" "Telefon"', 'recruiter', 'Headhunter Sales'),
        ('site:de "Recruiter" "B2B Vertrieb" "NRW"', 'recruiter', 'Recruiter B2B'),
    ]
    
    # Combine all queries
    all_queries = (
        default_queries + 
        candidates_queries + 
        social_queries + 
        portal_queries + 
        recruiter_queries
    )
    
    # Create dorks
    for query, category, description in all_queries:
        SearchDork.objects.get_or_create(
            query=query,
            defaults={
                'category': category,
                'description': description,
                'is_active': True,
                'priority': 50 if category == 'default' else 30,
            }
        )


def seed_portals(apps, schema_editor):
    """Seed portal sources."""
    PortalSource = apps.get_model('scraper_control', 'PortalSource')
    
    portals = [
        {
            'name': 'kleinanzeigen',
            'display_name': 'Kleinanzeigen.de',
            'base_url': 'https://www.kleinanzeigen.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/vertrieb/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/nordrhein-westfalen/sales/k0c107l929",
                "https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/k0c107",
            ]
        },
        {
            'name': 'markt_de',
            'display_name': 'Markt.de',
            'base_url': 'https://www.markt.de',
            'rate_limit_seconds': 4.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.markt.de/stellengesuche/nordrhein-westfalen/vertrieb/",
                "https://www.markt.de/stellengesuche/nordrhein-westfalen/sales/",
            ]
        },
        {
            'name': 'quoka',
            'display_name': 'Quoka.de',
            'base_url': 'https://www.quoka.de',
            'rate_limit_seconds': 6.0,
            'max_results': 20,
            'difficulty': 'high',
            'urls': [
                "https://www.quoka.de/stellengesuche/duesseldorf/",
                "https://www.quoka.de/stellengesuche/koeln/",
                "https://www.quoka.de/stellengesuche/dortmund/",
            ]
        },
        {
            'name': 'dhd24',
            'display_name': 'DHD24.com',
            'base_url': 'https://www.dhd24.com',
            'rate_limit_seconds': 4.0,
            'max_results': 20,
            'difficulty': 'medium',
            'urls': [
                "https://www.dhd24.com/kleinanzeigen/stellengesuche.html",
                "https://www.dhd24.com/kleinanzeigen/jobs/stellengesuche-vertrieb.html",
            ]
        },
        {
            'name': 'freelancermap',
            'display_name': 'Freelancermap.de',
            'base_url': 'https://www.freelancermap.de',
            'rate_limit_seconds': 3.0,
            'max_results': 20,
            'difficulty': 'low',
            'urls': [
                "https://www.freelancermap.de/freelancer-verzeichnis/sales.html",
                "https://www.freelancermap.de/freelancer-verzeichnis/vertrieb.html",
            ]
        },
    ]
    
    for portal_data in portals:
        PortalSource.objects.get_or_create(
            name=portal_data['name'],
            defaults=portal_data
        )


def seed_blacklist(apps, schema_editor):
    """Seed blacklist entries."""
    BlacklistEntry = apps.get_model('scraper_control', 'BlacklistEntry')
    
    # Domain blacklist
    blacklist_domains = [
        'stepstone.de', 'indeed.com', 'heyjobs.co', 'heyjobs.de',
        'softgarden.io', 'jobijoba.de', 'jobware.de', 'monster.de',
        'kununu.com', 'linkedin.com', 'xing.com', 'arbeitsagentur.de',
        'meinestadt.de', 'kimeta.de', 'stellenanzeigen.de',
        'bewerbung.net', 'freelancermap.de', 'reddit.com',
        'kleinanzeigen.de', 'lexware.de', 'qonto.com', 'sevdesk.de',
    ]
    
    for domain in blacklist_domains:
        BlacklistEntry.objects.get_or_create(
            entry_type='domain',
            value=domain,
            defaults={
                'reason': 'Job portal / aggregator',
                'is_active': True,
            }
        )
    
    # Path pattern blacklist
    path_patterns = [
        'lebenslauf', 'vorlage', 'muster', 'sitemap', 'seminar',
        'academy', 'weiterbildung', 'job', 'stellenangebot',
        'news', 'blog', 'ratgeber', 'portal'
    ]
    
    for pattern in path_patterns:
        BlacklistEntry.objects.get_or_create(
            entry_type='path_pattern',
            value=pattern,
            defaults={
                'reason': 'Generic content pattern',
                'is_active': True,
            }
        )
    
    # Mailbox prefix blacklist
    mailbox_prefixes = [
        'info', 'kontakt', 'contact', 'support', 'service',
        'privacy', 'datenschutz', 'noreply', 'no-reply',
        'donotreply', 'do-not-reply', 'jobs', 'karriere',
    ]
    
    for prefix in mailbox_prefixes:
        BlacklistEntry.objects.get_or_create(
            entry_type='mailbox_prefix',
            value=prefix,
            defaults={
                'reason': 'Generic email address',
                'is_active': True,
            }
        )


def reverse_seed(apps, schema_editor):
    """Remove seeded data."""
    SearchRegion = apps.get_model('scraper_control', 'SearchRegion')
    SearchDork = apps.get_model('scraper_control', 'SearchDork')
    PortalSource = apps.get_model('scraper_control', 'PortalSource')
    BlacklistEntry = apps.get_model('scraper_control', 'BlacklistEntry')
    
    SearchRegion.objects.all().delete()
    SearchDork.objects.all().delete()
    PortalSource.objects.all().delete()
    BlacklistEntry.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0002_portalsource_searchdork_searchregion_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_regions, reverse_seed),
        migrations.RunPython(seed_dorks, reverse_seed),
        migrations.RunPython(seed_portals, reverse_seed),
        migrations.RunPython(seed_blacklist, reverse_seed),
    ]
