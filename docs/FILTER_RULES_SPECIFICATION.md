# Filter-Regeln Spezifikation für Job-Seeker Leads

## Problem-Analyse

Das Scraping-System filtert fälschlicherweise echte Stellengesuche / Kandidatenanzeigen heraus. 
Die folgenden Filter-Ebenen verursachen False Positives:

1. **Titel-Guard** - erkennt Job-Ad Marker wie "Wir suchen", "Minijob", "m/w/d"
2. **Garbage Context** - filtert mit reason: "job_ad" oder "shop_product"  
3. **AI-FILTER** - labelt als "IRRELEVANT (recruiting)" oder "N/A"
4. **Kein Kandidatenprofil - skip** - Heuristik für Seiten ohne klaren Kandidaten

## Zielzustand

- Job-Angebote (Firmen suchen Mitarbeiter) → BLOCKEN
- Job-Gesuche (Personen suchen Arbeit) → DURCHLASSEN, wenn:
  - Es gibt eine Telefonnummer im Text, ODER
  - Es gibt eine E-Mail-Adresse, ODER
  - Es gibt starke Kandidaten-Indikatoren + Bezug zu Vertrieb/Verkauf

---

## Pseudocode-IF-Regeln

### Regel 1: Stellengesuch-Erkennung (PRIORITÄT HOCH)

```
WENN (
    Titel ENTHÄLT "Stellengesuch" ODER
    Titel ENTHÄLT "Job gesucht" ODER  
    Titel ENTHÄLT "Arbeit gesucht" ODER
    URL ENTHÄLT "/s-stellengesuche/" ODER
    URL ENTHÄLT "/stellengesuche/"
)
DANN:
    SETZE is_candidate_profile = TRUE
    NIEMALS als job_ad markieren
    DURCHLASSEN unabhängig von anderen Filtern
```

### Regel 2: "Ich suche" Kontext-Analyse

```
WENN Text ENTHÄLT "ich suche" DANN:
    
    // Positiv: Kandidat sucht Job
    WENN danach_folgt(
        "job", "arbeit", "stelle", "beschäftigung", 
        "neue herausforderung", "tätigkeit", "anstellung"
    ) DANN:
        SETZE is_candidate = TRUE
        NIEMALS als job_ad markieren
    
    // Negativ: Firma sucht (aber mit "ich" → selten, prüfen auf Kontext)
    WENN Text AUCH ENTHÄLT "(m/w/d)" UND "wir bieten" DANN:
        // Könnte Stellenangebot sein - weitere Prüfung nötig
        PRÜFE ob Kontaktdaten (Tel/Email) vorhanden
        WENN ja: DURCHLASSEN als "manuell prüfen"
```

### Regel 3: "Wir suchen" Kontext-Analyse

```
WENN Text ENTHÄLT "wir suchen" DANN:

    // BLOCKEN: Klares Jobangebot
    WENN (
        Text ENTHÄLT "(m/w/d)" ODER "(w/m/d)" ODER "(gn)" UND
        Text ENTHÄLT ("ihre aufgaben" ODER "wir bieten" ODER "benefits")
    ) DANN:
        SETZE is_job_ad = TRUE
        BLOCKEN
    
    // DURCHLASSEN: Handelsvertreter/Freelancer sucht Aufträge
    WENN (
        Text ENTHÄLT "wir suchen aufträge" ODER
        Text ENTHÄLT "wir suchen kunden" ODER
        Text ENTHÄLT "wir suchen partner" ODER
        Text ENTHÄLT "wir als handelsvertretung suchen" ODER
        Text ENTHÄLT "wir als freelancer suchen"
    ) DANN:
        SETZE is_candidate = TRUE
        DURCHLASSEN
```

### Regel 4: Titel-Guard Exceptions

```
// DURCHLASSEN wenn Stellengesuch im Titel
WENN Titel ENTHÄLT (
    "Stellengesuch", "suche Job", "suche Arbeit", 
    "Job gesucht", "Arbeit gesucht", "auf Jobsuche"
) DANN:
    IGNORIERE alle job_ad Marker
    SETZE is_candidate = TRUE

// BLOCKEN wenn klares Jobangebot im Titel  
WENN Titel ENTHÄLT (
    "(m/w/d)" UND ("gesucht" ODER "Mitarbeiter" ODER "Team")
) DANN:
    SETZE is_job_ad = TRUE
    BLOCKEN
```

### Regel 5: Kontaktdaten als Override-Bedingung

```
WENN (
    is_candidate_signal_found = TRUE UND
    (hat_telefonnummer = TRUE ODER hat_email = TRUE)
) DANN:
    DURCHLASSEN auch wenn andere Filter "job_ad" vermuten
    MARKIERE als "Lead mit Kontaktdaten - Review empfohlen"

// Telefonnummern-Prüfung
FUNKTION hat_telefonnummer(text):
    RETURN (
        text MATCHES /(?:\+49|0049|0)\s?1[5-7]\d(?:[\s\/\-]?\d){6,10}/ ODER  // Mobil
        text CONTAINS "tel:" ODER
        text CONTAINS "WhatsApp:" ODER
        text MATCHES /wa\.me\/\d+/
    )
```

### Regel 6: Kleinanzeigen-Spezialbehandlung

```
WENN URL ENTHÄLT "kleinanzeigen.de" DANN:

    // Stellengesuche-Kategorie → IMMER Kandidat
    WENN URL ENTHÄLT "/s-stellengesuche/" DANN:
        SETZE is_candidate = TRUE
        DURCHLASSEN
    
    // Stellenangebote-Kategorie → IMMER Jobangebot  
    WENN URL ENTHÄLT "/s-jobs/" DANN:
        SETZE is_job_ad = TRUE
        BLOCKEN
    
    // Text-basierte Erkennung für andere Kategorien
    WENN Text ENTHÄLT ("ich suche" ODER "suche arbeit" ODER "job gesucht") DANN:
        SETZE is_candidate = TRUE
        DURCHLASSEN
```

### Regel 7: Vertrieb/Sales-Kontext Verstärker

```
WENN (
    is_candidate_signal_found = TRUE UND
    Text ENTHÄLT (
        "vertrieb", "verkauf", "sales", "außendienst", "aussendienst",
        "call center", "callcenter", "d2d", "door to door", "akquise"
    )
) DANN:
    ERHÖHE confidence_score += 30
    MARKIERE als "Sales Kandidat - PRIORITÄT"
```

### Regel 8: AI-FILTER Override

```
WENN AI_FILTER sagt "IRRELEVANT" DANN:

    // Prüfe ob starkes Kandidaten-Signal übersehen wurde
    WENN (
        Text ENTHÄLT CANDIDATE_STRONG_SIGNALS UND
        hat_kontaktdaten = TRUE
    ) DANN:
        IGNORIERE AI-Filter Entscheidung
        DURCHLASSEN als "AI Override - Kontaktdaten gefunden"
```

### Regel 9: "Kein Kandidatenprofil" Override

```
// Erweitere CANDIDATE_POS_MARKERS um:
WENN Text ENTHÄLT (
    "ich suche", "suche job", "suche arbeit", "suche stelle",
    "stellengesuch", "job gesucht", "neue herausforderung",
    "mehr geld verdienen", "quereinstieg", "quereinsteiger",
    "ohne ausbildung", "selbstständig machen", "freiberuflich"
) DANN:
    SETZE is_candidate_profile = TRUE
    NIEMALS als "Kein Kandidatenprofil" skippen
```

---

## Positive Phrasen (Kandidatensignale - DURCHLASSEN)

### Stark (Einzelphrase reicht aus)
```python
CANDIDATE_STRONG_SIGNALS = [
    # Direkte Jobsuche
    "stellengesuch",
    "ich suche job",
    "ich suche arbeit", 
    "ich suche stelle",
    "job gesucht",
    "arbeit gesucht",
    "suche neue herausforderung",
    "suche neuen job",
    "suche neue stelle",
    
    # Verfügbarkeit
    "ab sofort verfügbar",
    "sofort verfügbar",
    "verfügbar ab",
    "freigestellt",
    "gekündigt",
    "arbeitslos",
    "arbeitssuchend",
    "auf jobsuche",
    
    # LinkedIn/Social
    "open to work",
    "#opentowork",
    "offen für angebote",
    "offen für neue chancen",
    "offen für neues",
    "looking for opportunities",
    "seeking new opportunities",
    
    # Wechselwilligkeit
    "wechselwillig",
    "wechselbereit",
    "bereit für veränderung",
    "neue wege gehen",
    "neuen wirkungskreis",
    
    # Quereinstieg
    "quereinstieg",
    "quereinsteiger",
    "mehr geld verdienen",
    "bessere verdienstmöglichkeiten",
    "karrierewechsel",
]
```

### Mittel (benötigt Kontext oder Kontaktdaten)
```python
CANDIDATE_MEDIUM_SIGNALS = [
    # Selbstbeschreibung
    "biete meine dienste",
    "biete mich an",
    "stelle mich vor",
    "mein profil",
    "meine erfahrung",
    "meine qualifikation",
    "mein lebenslauf",
    
    # CV/Bewerbung
    "lebenslauf",
    "curriculum vitae",
    "cv",
    "bewerberprofil",
    "qualifikationen",
    
    # Flexibilität
    "flexibel einsetzbar",
    "deutschlandweit",
    "bundesweit",
    "regional flexibel",
    "homeoffice möglich",
    
    # Handelsvertreter
    "handelsvertreter",
    "handelsvertretung", 
    "selbstständiger vertreter",
    "freiberuflicher vertrieb",
    "auf provisionsbasis",
]
```

### Vertrieb-Kontext (verstärkt andere Signale)
```python
SALES_CONTEXT_SIGNALS = [
    "vertrieb",
    "verkauf",
    "sales",
    "außendienst",
    "aussendienst",
    "innendienst",
    "key account",
    "account manager",
    "business development",
    "akquise",
    "neukundengewinnung",
    "kundenbetreuung",
    "call center",
    "callcenter",
    "telesales",
    "telefonverkauf",
    "d2d",
    "door to door",
    "haustür",
    "kaltakquise",
]
```

---

## Negative Phrasen (Arbeitgeber/Jobangebot-Signale - BLOCKEN)

### Stark (Einzelphrase blockt)
```python
EMPLOYER_STRONG_SIGNALS = [
    # Stellenanzeige-Header
    "(m/w/d)",
    "(w/m/d)",
    "(d/m/w)",
    "(m/f/d)",
    "(gn)",
    
    # Firma sucht
    "wir suchen dich",
    "wir suchen sie",
    "wir stellen ein",
    "join our team",
    "verstärkung gesucht",
    "mitarbeiter gesucht",
    "team sucht",
    
    # Jobangebot-Struktur
    "ihre aufgaben",
    "deine aufgaben",
    "wir bieten",
    "wir bieten dir",
    "das bieten wir",
    "your tasks",
    "your responsibilities",
    "benefits:",
    "corporate benefits",
    
    # Bewerbungsaufforderung
    "jetzt bewerben",
    "bewerben sie sich",
    "bewirb dich jetzt",
    "apply now",
    "bewerbung an",
    "sende deine bewerbung",
]
```

### Mittel (benötigt zweites Signal zum Blocken)
```python  
EMPLOYER_MEDIUM_SIGNALS = [
    # Firmenkontext
    "unser team",
    "für unser team",
    "unser unternehmen",
    "unsere firma",
    
    # Anforderungen
    "ihr profil",
    "dein profil",
    "das bringst du mit",
    "das erwarten wir",
    "voraussetzungen",
    
    # Vergütung (Arbeitgebersicht)
    "wir bieten gehalt",
    "attraktive vergütung",
    "fixum plus provision",
    "einstiegsgehalt",
    
    # Arbeitgebermarken
    "karriere bei",
    "jobs bei",
    "stellenangebote bei",
    "arbeiten bei",
]
```

### URL-Patterns (definitiv Jobangebot)
```python
EMPLOYER_URL_PATTERNS = [
    "/s-jobs/",
    "/stellenangebote/",
    "/stellenangebot/",
    "/karriere/",
    "/karriere-",
    "/jobs/",
    "/vacancy/",
    "/vacancies/",
    "/open-positions/",
    "/offene-stellen/",
]
```

---

## Implementierungs-Prioritäten

1. **SOFORT**: `CANDIDATE_STRONG_SIGNALS` Liste erweitern in `luca_scraper/parser/context.py`
2. **SOFORT**: `is_candidate_seeking_job()` Funktion anpassen für Kontaktdaten-Override
3. **HOCH**: Kleinanzeigen URL-Pfad Erkennung in `is_garbage_context()` 
4. **MITTEL**: AI-Filter Override Logik
5. **NIEDRIG**: Score-Boost für Sales-Kontext

---

## Test-Szenarien

### Muss DURCHLASSEN:
1. "Ich suche Job als Verkäufer in NRW - 0176-12345678"
2. "Stellengesuch: Vertriebsmitarbeiter mit Erfahrung"
3. "Quereinstieg gewünscht, suche neue Herausforderung im Sales"
4. Kleinanzeigen URL mit `/s-stellengesuche/`
5. LinkedIn Profil mit "#OpenToWork"
6. Text mit "mehr Geld verdienen" + Telefonnummer

### Muss BLOCKEN:
1. "Wir suchen Vertriebsmitarbeiter (m/w/d)"
2. "Sales Manager gesucht - Ihre Aufgaben: ..."
3. URL enthält `/s-jobs/`
4. Text mit "wir bieten" + "bewerben sie sich"

---

## Changelog

- **v1.0** (2026-01-22): Initiale Spezifikation basierend auf Problem-Analyse
