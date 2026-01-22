# -*- coding: utf-8 -*-
"""
Optimierte Dork-Konfiguration für erweiterte Lead-Quellen

Diese Datei enthält eine neue Sammlung von Google/DDG-Dorks, die gezielt auf
Vertriebskandidaten in Deutschland (Fokus NRW) abzielen – OHNE eBay Kleinanzeigen.

Zielgruppe:
- Menschen in Deutschland (Fokus NRW), die offen sind für Vertrieb/Außendienst/Handelsvertretung
- Typen: unzufriedene Angestellte, Quereinsteiger, Leute die „mehr Geld" wollen, Arbeitsuchende
- Benötigt: Name + Telefonnummer oder E-Mail (mindestens eins)

Struktur:
- Jede Kategorie enthält 3-5 konkrete Dorks
- Alle Dorks schließen Jobboards aus (-stepstone -indeed etc.)
- NRW-Bezug über Städte, Region oder PLZ (40xxx-59xxx)
"""

from typing import Dict, List, Any

# =============================================================================
# JOBBOARD EXCLUSION STRING
# Wird an relevante Dorks angehängt, um Jobportale auszuschließen
# =============================================================================
JOB_BOARD_EXCLUSIONS = (
    '-site:stepstone.de -site:indeed.com -site:indeed.de -site:monster.de '
    '-site:jooble.org -site:heyjobs.co -site:heyjobs.de -site:stellenanzeigen.de '
    '-site:jobware.de -site:kimeta.de -site:xing.com/jobs -site:linkedin.com/jobs '
    '-site:glassdoor.de -site:kununu.com -site:absolventa.de -site:yourfirm.de '
    '-site:karriere.de -site:jobvector.de -site:connecticum.de -site:hokify.de'
)

# NRW PLZ-Bereiche (40xxx bis 59xxx) - vollständige Abdeckung
# 40-48: Düsseldorf, Mönchengladbach, Krefeld, Wuppertal, Solingen, Essen, Mülheim, Oberhausen, Duisburg, Bochum, Gelsenkirchen, Münster
# 50-53: Köln, Leverkusen, Bergisch Gladbach, Bonn, Siegburg
# 54-56: Teils Rheinland-Pfalz, aber inkludiert für Grenzregionen
# 57-59: Siegen, Hagen, Dortmund, Hamm, Lünen, Unna
NRW_PLZ_PATTERN = '("40" OR "41" OR "42" OR "43" OR "44" OR "45" OR "46" OR "47" OR "48" OR "49" OR "50" OR "51" OR "52" OR "53" OR "54" OR "55" OR "56" OR "57" OR "58" OR "59")'

# Deutsche Mobilfunknummern-Präfixe (für Lebenslauf-Suchen)
MOBILE_PHONE_PREFIXES = '("0151" OR "0152" OR "0155" OR "0157" OR "0159" OR "0160" OR "0162" OR "0163" OR "0170" OR "0171" OR "0172" OR "0173" OR "0174" OR "0175" OR "0176" OR "0177" OR "0178" OR "0179")'

# NRW Großstädte für gezielte Suchen
NRW_CITIES_SEARCH = '(Düsseldorf OR Köln OR Dortmund OR Essen OR Duisburg OR Bochum OR Wuppertal OR Bielefeld OR Bonn OR Münster OR Aachen OR Mönchengladbach OR Krefeld)'

# =============================================================================
# OPTIMIZED_DORKS - Hauptkonfiguration
# =============================================================================

OPTIMIZED_DORKS: Dict[str, Dict[str, Any]] = {
    
    # =========================================================================
    # KATEGORIE 1: ÖFFENTLICHE BRANCHENVERZEICHNISSE & DATENBANKEN
    # =========================================================================
    # Warum gut: Offizielle Verzeichnisse mit verifizierten Kontaktdaten,
    # hohe Datenqualität, strukturierte Einträge mit Telefon/E-Mail
    
    "branchenverzeichnisse": {
        "beschreibung": "Gelbe Seiten, Das Örtliche, 11880 und lokale Firmenverzeichnisse - verifizierte Geschäftskontakte mit direkten Telefonnummern",
        "dorks": [
            # Gelbe Seiten - Handelsvertreter und Vertriebspartner
            # Grund: Direkte Einträge mit Telefonnummern von selbstständigen Vertriebsmenschen
            f'site:gelbeseiten.de "Handelsvertretung" ("NRW" OR "Nordrhein-Westfalen") telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Das Örtliche - Vertriebsdienstleister regional
            # Grund: Lokale Verzeichnisse haben oft Mobilnummern der Inhaber
            f'site:dasoertliche.de "Vertriebsservice" {NRW_CITIES_SEARCH} {JOB_BOARD_EXCLUSIONS}',
            
            # 11880 - Gewerbeeinträge mit Kontaktdaten
            # Grund: Detaillierte Firmendaten inkl. Ansprechpartner-Namen
            f'site:11880.com "Außendienst" OR "Handelsvertreter" NRW telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Cylex - regionales Branchenbuch
            # Grund: Oft mit persönlichen Ansprechpartnern und Mobilnummern
            f'site:cylex.de "Vertriebspartner" ("Düsseldorf" OR "Köln" OR "Dortmund") kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # WLW (Wer liefert was) - B2B-Verzeichnis
            # Grund: Geschäftskontakte mit Entscheidern, oft persönliche E-Mails
            f'site:wlw.de "Vertrieb" "Nordrhein-Westfalen" ("Ansprechpartner" OR "kontakt") {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 2: IHK & HANDELSREGISTER-QUELLEN
    # =========================================================================
    # Warum gut: Offizielle Registrierungen, Handelsvertreterregister,
    # verifizierte Geschäftsdaten mit Pflichtangaben (Impressum)
    
    "ihk_handelsregister": {
        "beschreibung": "IHK-Firmendatenbanken, Handelsvertreterregister und offizielle Wirtschaftsverzeichnisse - höchste Datenqualität",
        "dorks": [
            # IHK Firmendatenbanken NRW
            # Grund: Mitgliedsunternehmen mit verifizierten Kontaktdaten
            f'site:ihk.de "Handelsvertreter" ("NRW" OR "Düsseldorf" OR "Köln") kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # CDH - Centralvereinigung Deutscher Handelsvertreter
            # Grund: Offizielles Register selbstständiger Handelsvertreter
            f'site:cdh.de "Handelsvertretung" ("Nordrhein-Westfalen" OR "NRW") telefon {JOB_BOARD_EXCLUSIONS}',
            
            # IHK Mitgliedersuche regional
            # Grund: Regionale IHKs haben Firmendatenbanken mit Ansprechpartnern
            f'site:ihk-koeln.de OR site:ihk-duesseldorf.de OR site:ihk-dortmund.de "Vertrieb" kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # Northdata - Handelsregister Recherche
            # Grund: Geschäftsführerdaten mit oft privaten Kontaktinfos
            f'site:northdata.de "Vertriebsleitung" OR "Handelsvertretung" NRW {JOB_BOARD_EXCLUSIONS}',
            
            # BVMW - Bundesverband mittelständische Wirtschaft
            # Grund: Mitgliederverzeichnis mit Unternehmern, die vertriebsoffen sind
            f'site:bvmw.de "Mitglied" ("NRW" OR "Nordrhein-Westfalen") "Vertrieb" kontakt {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 3: FIRMENWEBSEITEN MIT VERTRIEBSTEAMS
    # =========================================================================
    # Warum gut: Direkte Namen und Kontaktdaten von aktiven Vertrieblern,
    # oft mit Mobilnummern für Außendienst
    
    "firmen_teamseiten": {
        "beschreibung": "Unternehmenswebseiten mit Team-Seiten, Außendienst-Kontakten und Gebietsvertreter-Verzeichnissen",
        "dorks": [
            # Team-Seiten mit Vertriebsmitarbeitern
            # Grund: Unternehmen listen ihre Außendienstler oft mit direkten Kontakten
            f'intitle:"Unser Team" OR intitle:"Team" "Außendienst" OR "Vertriebsmitarbeiter" telefon NRW {JOB_BOARD_EXCLUSIONS}',
            
            # Gebietsvertreter-Verzeichnisse
            # Grund: Regionale Vertreter haben Mobilnummern als direkten Draht
            f'inurl:gebietsvertreter OR inurl:aussendienst ("Nordrhein-Westfalen" OR {NRW_CITIES_SEARCH}) telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Ansprechpartner-Seiten mit Sales-Kontext
            # Grund: Direkte Kontaktdaten inkl. E-Mail und Durchwahl
            f'inurl:ansprechpartner OR inurl:kontakt "Vertriebsleiter" OR "Sales Manager" NRW telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Impressum mit Vertriebskontakt
            # Grund: Pflichtangaben im Impressum enthalten oft Inhaberdaten
            f'inurl:impressum "Vertrieb" OR "Handelsvertretung" NRW ("mobil" OR "telefon" OR "@") {JOB_BOARD_EXCLUSIONS}',
            
            # "Ihre Ansprechpartner" Seiten
            # Grund: Strukturierte Kontaktlisten mit Namen und Telefon
            f'"Ihr Ansprechpartner" OR "Ihre Ansprechpartner" "Vertrieb" OR "Außendienst" {NRW_CITIES_SEARCH} {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 4: FOREN & COMMUNITIES FÜR JOBSUCHENDE/QUEREINSTEIGER
    # =========================================================================
    # Warum gut: Menschen, die aktiv nach Veränderung suchen,
    # "Ich suche Job", "neue Herausforderung", "Quereinstieg"
    
    "foren_communities": {
        "beschreibung": "Fachforen, Gruppen und Communities wo Menschen nach neuen Herausforderungen suchen - direkte Kontakte zu Wechselwilligen",
        "dorks": [
            # Reddit - Deutschsprachige Karriere-Communities
            # Grund: Offene Diskussionen über Jobwechsel, oft mit Kontaktangebot
            f'site:reddit.com/r/de OR site:reddit.com/r/arbeitsleben "suche neue Herausforderung" OR "Quereinstieg Vertrieb" {JOB_BOARD_EXCLUSIONS}',
            
            # Gutefrage - Karriere und Jobwechsel Fragen
            # Grund: Personen mit Karrierefragen sind oft wechselbereit
            f'site:gutefrage.net "Vertrieb" "Quereinstieg" OR "neue Herausforderung" OR "berufliche Veränderung" {JOB_BOARD_EXCLUSIONS}',
            
            # Facebook Gruppen - Stellengesuche und Karriere
            # Grund: Persönliche Posts mit Kontaktdaten
            f'site:facebook.com/groups "suche Job" OR "suche Stelle" "Vertrieb" OR "Verkauf" NRW {JOB_BOARD_EXCLUSIONS}',
            
            # Wiwi-Treff - BWL/Wirtschaftsforum
            # Grund: Absolventen und Berufswechsler mit Interesse an Sales
            f'site:wiwi-treff.de "Vertrieb" "Einstieg" OR "Quereinstieg" OR "suche Stelle" {JOB_BOARD_EXCLUSIONS}',
            
            # Diverse Fachforen mit Jobsuche-Kontext
            # Grund: Nischen-Communities haben engagierte Mitglieder
            f'inurl:forum "suche Job" OR "biete Arbeitskraft" ("Vertrieb" OR "Sales" OR "Verkauf") NRW kontakt {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 5: FREIBERUFLER & SELBSTSTÄNDIGE PORTALE
    # =========================================================================
    # Warum gut: Selbstständige Vertriebler, Handelsvertreter auf Projektsuche,
    # professionelle Profile mit Kontaktdaten
    
    "freiberufler_portale": {
        "beschreibung": "Freelancer-Plattformen und Selbstständigen-Verzeichnisse - Profis mit direkten Kontaktdaten auf Auftragssuche",
        "dorks": [
            # Freelancermap - Vertriebsprofis
            # Grund: Detaillierte Profile mit Verfügbarkeit und Kontakt
            f'site:freelancermap.de "Vertrieb" OR "Sales" "verfügbar" NRW kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # Freelance.de - Selbstständige im Vertriebsbereich
            # Grund: Aktive Projektsuche bedeutet Offenheit für neue Aufträge
            f'site:freelance.de "Handelsvertreter" OR "Vertriebsprofi" "freiberuflich" kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # GULP - IT-naher Vertrieb
            # Grund: Tech-Sales Profis mit hoher Qualifikation
            f'site:gulp.de "Sales" OR "Business Development" NRW verfügbar telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Twago - Projektmarktplatz
            # Grund: Freiberufler mit aktueller Verfügbarkeit
            f'site:twago.de "Vertrieb" OR "Account Management" "freiberuflich" kontakt {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 6: SOCIAL MEDIA PROFILE (NICHT JOBS-FEEDS)
    # =========================================================================
    # Warum gut: Öffentliche Profile mit Karriere-Signalen,
    # "suche neue Herausforderung", "offen für Angebote"
    
    "social_profiles": {
        "beschreibung": "LinkedIn und XING Profile mit Wechselsignalen - keine Job-Feeds, sondern individuelle Profile",
        "dorks": [
            # LinkedIn Profile - Wechselwillige Vertriebler
            # Grund: "Offen für Angebote" signalisiert aktive Jobsuche
            f'site:linkedin.com/in "offen für Angebote" OR "open to work" "Vertrieb" OR "Sales" {NRW_CITIES_SEARCH} {JOB_BOARD_EXCLUSIONS}',
            
            # XING Profile - Karrierewechsel Signale
            # Grund: Status "Auf Jobsuche" zeigt konkrete Wechselbereitschaft
            f'site:xing.com/profile "auf Jobsuche" OR "neue Herausforderung" "Vertrieb" OR "Sales" NRW {JOB_BOARD_EXCLUSIONS}',
            
            # LinkedIn - Spezifische Vertriebs-Rollen mit Kontakt
            # Grund: Außendienstler haben oft Mobilnummern im Profil
            f'site:linkedin.com/in "Außendienst" OR "Gebietsverkaufsleiter" ("Nordrhein-Westfalen" OR "NRW") {JOB_BOARD_EXCLUSIONS}',
            
            # XING - Handelsvertreter Profile
            # Grund: Selbstständige Handelsvertreter mit Kontaktfreudigkeit
            f'site:xing.com/profile "Handelsvertreter" OR "Freier Handelsvertreter" NRW kontakt {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 7: MESSE- UND EVENT-AUSSTELLER
    # =========================================================================
    # Warum gut: Aktive Vertriebsunternehmen mit Außendienst-Teams,
    # Kontakte aus Ausstellerverzeichnissen
    
    "messe_aussteller": {
        "beschreibung": "Ausstellerverzeichnisse von Fachmessen - Unternehmen mit aktivem Vertrieb und Ansprechpartnern",
        "dorks": [
            # Messe Düsseldorf - Ausstellerprofile
            # Grund: B2B-Messen haben Vertriebsteams vor Ort, Kontaktlisten öffentlich
            f'site:messe-duesseldorf.de "Aussteller" "Ansprechpartner" kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # Messe Köln - Vertriebskontakte
            # Grund: Großmessen mit strukturierten Ausstellerdaten
            f'site:koelnmesse.de "Ausstellerprofil" "Vertrieb" OR "Sales" telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Messe Essen - Industrieaussteller
            # Grund: Industrie-Messen haben technische Vertriebler als Kontakte
            f'site:messe-essen.de "Aussteller" "Ansprechpartner" kontakt telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Allgemeine Messekataloge
            # Grund: Branchenübergreifende Suche nach Vertriebskontakten
            f'"Messekatalog" OR "Ausstellerverzeichnis" "Vertrieb" OR "Sales" NRW kontakt telefon {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 8: SPEZIFISCHE BRANCHEN MIT VERTRIEBSFOKUS
    # =========================================================================
    # Warum gut: Branchen mit starkem Außendienst (Versicherung, Finanz, Immobilien),
    # Menschen mit Vertriebserfahrung und Wechselbereitschaft
    
    "branchen_vertrieb": {
        "beschreibung": "Branchen mit starkem Außendienst - Versicherung, Finanz, Immobilien, Automobil - erfahrene Vertriebler",
        "dorks": [
            # Versicherungsvertreter/Makler
            # Grund: Provisionsbasierte Arbeit macht wechselbereit, oft selbstständig
            f'"Versicherungsvertreter" OR "Versicherungsmakler" NRW ("suche" OR "biete" OR kontakt) {JOB_BOARD_EXCLUSIONS}',
            
            # Immobilienmakler
            # Grund: Selbstständige mit Vertriebserfahrung und direktem Kundenkontakt
            f'site:ivd.net OR "Immobilienmakler" NRW ("Ansprechpartner" OR kontakt OR telefon) {JOB_BOARD_EXCLUSIONS}',
            
            # Finanzberater/Vermögensberater
            # Grund: Strukturvertrieb-Erfahrung, oft wechselwillig
            f'"Finanzberater" OR "Vermögensberater" NRW ("freiberuflich" OR "selbstständig") kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # Automobilverkäufer
            # Grund: Erfahrene Verkäufer mit Abschlussstärke
            f'"Autohaus" OR "KFZ-Verkäufer" "Verkaufsberater" NRW kontakt telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Pharma-Außendienst
            # Grund: Hochqualifizierte Vertriebler mit B2B-Erfahrung
            f'"Pharmareferent" OR "Pharmaberater" NRW ("wechsel" OR "neue Herausforderung" OR kontakt) {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 9: CV/LEBENSLAUF-DATENBANKEN (NICHT JOBBOARDS)
    # =========================================================================
    # Warum gut: PDFs mit kompletten Kontaktdaten,
    # direkte Bewerberdaten mit Telefon und E-Mail
    
    "cv_datenbanken": {
        "beschreibung": "Öffentlich zugängliche Lebensläufe und CV-Datenbanken - vollständige Kontaktdaten von Bewerbern",
        "dorks": [
            # PDF-Lebensläufe mit Vertriebserfahrung
            # Grund: Komplette Kontaktdaten im Dokument
            f'filetype:pdf "Lebenslauf" OR "Curriculum Vitae" ("Vertrieb" OR "Sales Manager" OR "Außendienst") NRW {JOB_BOARD_EXCLUSIONS}',
            
            # PDF-CVs mit Telefonnummern-Muster
            # Grund: Mobilnummern im Lebenslauf garantieren Erreichbarkeit
            f'filetype:pdf ("Vertriebsleiter" OR "Account Manager") {MOBILE_PHONE_PREFIXES} NRW {JOB_BOARD_EXCLUSIONS}',
            
            # Word-Dokumente als alternative Formate
            # Grund: Manche Bewerber nutzen .doc/.docx
            f'filetype:doc OR filetype:docx "Bewerbung" "Vertrieb" OR "Sales" NRW kontakt {JOB_BOARD_EXCLUSIONS}',
            
            # Bewerberprofile auf Uni-/Hochschul-Seiten
            # Grund: Alumni-Datenbanken mit Karriereinteresse
            f'site:*.uni-*.de OR site:*.fh-*.de "Alumni" "Vertrieb" OR "Sales" NRW kontakt {JOB_BOARD_EXCLUSIONS}',
        ]
    },
    
    # =========================================================================
    # KATEGORIE 10: PLZ-BASIERTE SUCHEN (40xxx-59xxx = NRW)
    # =========================================================================
    # Warum gut: Präzise regionale Eingrenzung über Postleitzahlen,
    # filtert andere Bundesländer aus
    
    "plz_basiert": {
        "beschreibung": "Postleitzahl-basierte Suchen für NRW (40000-59999) - präzise regionale Eingrenzung",
        "dorks": [
            # PLZ 40xxx-41xxx (Düsseldorf Region)
            # Grund: Wirtschaftszentrum mit hoher Vertriebsdichte
            f'"40" OR "41" "Vertrieb" OR "Außendienst" ("suche Job" OR "suche Stelle" OR kontakt) telefon {JOB_BOARD_EXCLUSIONS}',
            
            # PLZ 44xxx-45xxx (Ruhrgebiet)
            # Grund: Industrieregion mit vielen Vertriebsstrukturen
            f'"44" OR "45" "Sales Manager" OR "Handelsvertreter" kontakt telefon {JOB_BOARD_EXCLUSIONS}',
            
            # PLZ 50xxx-51xxx (Köln Region)
            # Grund: Medienzentrum mit Marketing/Sales-Schwerpunkt
            f'"50" OR "51" "Vertrieb" OR "Key Account" kontakt OR telefon OR email {JOB_BOARD_EXCLUSIONS}',
            
            # PLZ 48xxx (Münsterland)
            # Grund: Mittelständische Wirtschaft mit Vertriebsbedarf
            f'"48" "Handelsvertretung" OR "Außendienst" kontakt telefon {JOB_BOARD_EXCLUSIONS}',
            
            # Kombination aller NRW PLZ
            # Grund: Breite regionale Abdeckung
            f'{NRW_PLZ_PATTERN} "Vertriebsmitarbeiter" OR "Sales Representative" ("suche" OR kontakt) {JOB_BOARD_EXCLUSIONS}',
        ]
    },
}

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def get_optimized_dorks() -> Dict[str, Dict[str, Any]]:
    """
    Gibt die komplette OPTIMIZED_DORKS Konfiguration zurück.
    
    Returns:
        Dictionary mit allen Dork-Kategorien und ihren Dorks
    """
    return OPTIMIZED_DORKS


def get_dorks_by_category(category: str) -> List[str]:
    """
    Gibt die Dorks einer bestimmten Kategorie zurück.
    
    Args:
        category: Name der Kategorie (z.B. "branchenverzeichnisse")
    
    Returns:
        Liste der Dorks dieser Kategorie oder leere Liste
    """
    if category in OPTIMIZED_DORKS:
        return OPTIMIZED_DORKS[category].get("dorks", [])
    return []


def get_all_optimized_dorks() -> List[str]:
    """
    Gibt alle Dorks aus allen Kategorien als flache Liste zurück.
    
    Returns:
        Liste aller optimierten Dorks
    """
    all_dorks = []
    for category_data in OPTIMIZED_DORKS.values():
        all_dorks.extend(category_data.get("dorks", []))
    return all_dorks


def get_category_descriptions() -> Dict[str, str]:
    """
    Gibt die Beschreibungen aller Kategorien zurück.
    
    Returns:
        Dictionary mit Kategorie-Namen und Beschreibungen
    """
    return {
        category: data.get("beschreibung", "")
        for category, data in OPTIMIZED_DORKS.items()
    }


def get_dork_count_per_category() -> Dict[str, int]:
    """
    Gibt die Anzahl der Dorks pro Kategorie zurück.
    
    Returns:
        Dictionary mit Kategorie-Namen und Anzahl der Dorks
    """
    return {
        category: len(data.get("dorks", []))
        for category, data in OPTIMIZED_DORKS.items()
    }


def get_total_dork_count() -> int:
    """
    Gibt die Gesamtzahl aller optimierten Dorks zurück.
    
    Returns:
        Anzahl aller Dorks
    """
    return sum(get_dork_count_per_category().values())


# =============================================================================
# ZUSAMMENFASSUNG DER QUELLENKATEGORIEN
# =============================================================================
"""
ZUSAMMENFASSUNG DER 10 NEUEN QUELLENTYPEN (ohne eBay Kleinanzeigen):

1. BRANCHENVERZEICHNISSE (5 Dorks)
   - Gelbe Seiten, Das Örtliche, 11880, Cylex, WLW
   - Verifizierte Geschäftskontakte mit Telefonnummern
   - Selbstständige Handelsvertreter und Vertriebspartner

2. IHK & HANDELSREGISTER (5 Dorks)
   - IHK-Firmendatenbanken, CDH-Handelsvertreterregister
   - Northdata, BVMW-Mitgliederverzeichnis
   - Höchste Datenqualität durch offizielle Quellen

3. FIRMEN-TEAMSEITEN (5 Dorks)
   - "Unser Team", "Gebietsvertreter", "Ansprechpartner"
   - Impressum-Seiten mit Pflichtangaben
   - Direkte Kontaktdaten von aktiven Vertrieblern

4. FOREN & COMMUNITIES (5 Dorks)
   - Reddit (r/de, r/arbeitsleben), Gutefrage, Facebook Groups
   - Wiwi-Treff (BWL/Wirtschaft)
   - Wechselwillige und Quereinsteiger

5. FREIBERUFLER-PORTALE (4 Dorks)
   - Freelancermap, Freelance.de, GULP, Twago
   - Selbstständige Vertriebler auf Auftragssuche

6. SOCIAL MEDIA PROFILE (4 Dorks)
   - LinkedIn/XING Profile (keine Job-Feeds)
   - "Open to work", "Offen für Angebote"
   - Wechselsignale in Profilen

7. MESSE-AUSSTELLER (4 Dorks)
   - Messe Düsseldorf, Köln, Essen
   - Ausstellerverzeichnisse mit Vertriebskontakten

8. BRANCHEN-VERTRIEB (5 Dorks)
   - Versicherung, Immobilien, Finanz, Automobil, Pharma
   - Erfahrene Vertriebler aus provisionsbasierten Branchen

9. CV-DATENBANKEN (4 Dorks)
   - PDF-Lebensläufe mit kompletten Kontaktdaten
   - Word-Dokumente, Uni-Alumni-Verzeichnisse

10. PLZ-BASIERTE SUCHEN (5 Dorks)
    - 40xxx-59xxx = NRW-Region
    - Präzise regionale Eingrenzung

GESAMT: 46 optimierte Dorks in 10 Kategorien
ALLE mit Jobboard-Ausschlüssen (-stepstone -indeed etc.)
ALLE mit NRW-Bezug (Städte, PLZ, Region)
"""
