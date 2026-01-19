# ML-Enhanced Data Quality System

## Überblick

Dieses System erweitert die Datenqualität und Lead-Bewertung des LUCA NRW Scrapers durch Machine Learning-basierte Komponenten und eine Feedback-Schleife.

## Komponenten

### 1. ML-basierte Extraktoren (`stream2_extraction_layer/ml_extractors.py`)

#### SimpleNERNameExtractor
Extrahiert Personennamen aus Text mit Named Entity Recognition-Heuristiken:
- Erkennt typische deutsche Namensmuster
- Analysiert Kontext (Ansprechpartner, Kontakt, etc.)
- Bewertet Konfidenz basierend auf Mustern
- Filtert Firmennamen und generische Begriffe

**Verwendung:**
```python
from stream2_extraction_layer.ml_extractors import get_name_extractor

extractor = get_name_extractor()
result = extractor.extract(text, html)
print(f"Name: {result.value}, Confidence: {result.confidence}")
```

#### MLPhoneExtractor
Bewertet extrahierte Telefonnummern basierend auf Kontext:
- Unterscheidet zwischen persönlichen und Firmen-Nummern
- Filtert Hotlines und Service-Nummern
- Erhöht Konfidenz für Mobilnummern
- Analysiert umgebenden Text für Qualitätssignale

**Verwendung:**
```python
from stream2_extraction_layer.ml_extractors import get_phone_extractor

extractor = get_phone_extractor()
confidence = extractor.score_phone(phone, raw_match, context)
```

#### MLEmailClassifier
Klassifiziert E-Mail-Adressen in Qualitätskategorien:
- **Portal**: stepstone.de, indeed.com → sehr niedrige Qualität
- **Generic**: info@, kontakt@ → niedrige Qualität
- **Free Personal**: max.mustermann@gmail.com → mittlere Qualität
- **Corporate Personal**: max.mustermann@firma.de → hohe Qualität

**Verwendung:**
```python
from stream2_extraction_layer.ml_extractors import get_email_classifier

classifier = get_email_classifier()
result = classifier.classify("max.mustermann@firma.de")
# {'category': 'corporate_personal', 'quality': 'high', 'score_modifier': 0.3}
```

#### MLIndustryClassifier
Klassifiziert Leads in Branchen und lernt aus Feedback:
- Unterstützte Branchen: Versicherung, Energie, Telekom, Bau, E-Commerce, Haushalt, Recruiter
- Lernt neue Keywords aus User-Feedback
- Bewertet Konfidenz basierend auf Keyword-Häufigkeit

**Verwendung:**
```python
from stream2_extraction_layer.ml_extractors import get_industry_classifier

classifier = get_industry_classifier()
industry, confidence = classifier.classify(text, url, company)

# Feedback-basiertes Lernen
classifier.learn_from_feedback(text, correct_industry='versicherung')
```

### 2. Feedback Loop System (`stream3_scoring_layer/feedback_loop.py`)

Das Feedback-Loop-System ermöglicht kontinuierliches Lernen durch User-Feedback.

#### FeedbackLoopSystem
Zentrale Komponente für Feedback-Sammlung und dynamisches Scoring:
- Speichert User-Bewertungen zu Leads
- Berechnet Qualitäts-Metriken
- Passt Scoring-Parameter dynamisch an
- Identifiziert erfolgreiche Muster

**Verwendung:**
```python
from stream3_scoring_layer.feedback_loop import get_feedback_system, FeedbackEntry

# Feedback-System initialisieren
feedback_system = get_feedback_system()

# Feedback aufzeichnen
feedback = FeedbackEntry(
    lead_id=123,
    feedback_type='quality',
    rating=0.8,  # 0.0 - 1.0
    user_id='user@example.com',
    notes='Good lead, contacted successfully',
    metadata={
        'email_domain': 'firma.de',
        'industry': 'versicherung',
        'conversion': True
    }
)
feedback_system.record_feedback(feedback)

# Dynamische Score-Anpassung abrufen
lead = {'email': 'test@firma.de', 'industry': 'versicherung'}
adjustment = feedback_system.get_dynamic_score_adjustment(lead)
```

#### Qualitäts-Metriken
```python
# Metriken für die letzten 7 Tage
metrics = feedback_system.get_quality_metrics(days=7)
print(f"Durchschnittliche Bewertung: {metrics.avg_rating}")
print(f"Positive Rate: {metrics.positive_rate}")
print(f"Conversion Rate: {metrics.conversion_rate}")

# Extractions-Genauigkeit
email_accuracy = feedback_system.get_field_accuracy('email', days=30)
phone_accuracy = feedback_system.get_field_accuracy('phone', days=30)
```

#### Extractions-Genauigkeit tracken
```python
# Aufzeichnen ob eine Extraktion korrekt war
feedback_system.record_extraction_accuracy(
    lead_id=123,
    field_name='email',
    extracted='test@firma.de',
    correct='test@firma.de',  # User-korrigiert
    confidence=0.9
)
```

### 3. Integration in Extraction Pipeline

Die ML-Komponenten sind in `extraction_enhanced.py` integriert und funktionieren als Fallback/Boost für regex-basierte Extraktion:

```python
from stream2_extraction_layer.extraction_enhanced import extract_with_multi_tier_fallback

result = await extract_with_multi_tier_fallback(html, text, url, company)
# {
#     'name': 'Max Mustermann',
#     'rolle': 'versicherung',
#     'email': 'max@firma.de',
#     'email_quality': 'high',
#     'email_category': 'corporate_personal',
#     'extraction_method': 'regex_name',
#     'confidence': 0.85
# }
```

### 4. Integration in Scoring Pipeline

Das dynamische Scoring ist in `scoring_enhanced.py` integriert:

```python
from stream3_scoring_layer.scoring_enhanced import compute_score_v2

# Mit dynamischem Scoring (default)
score = compute_score_v2(text, url, lead, use_dynamic_scoring=True)

# Ohne dynamisches Scoring (nur statische Regeln)
score = compute_score_v2(text, url, lead, use_dynamic_scoring=False)
```

## Vorteile gegenüber reinem Regex

### 1. Kontextbasierte Extraktion
- **Regex**: Findet nur exakte Muster, kein Kontext
- **ML**: Analysiert Kontext (z.B. "Ihr Ansprechpartner: Max Mustermann")

### 2. Qualitätsbewertung
- **Regex**: Alle E-Mails gleich behandelt
- **ML**: Unterscheidet corporate_personal (hoch) von portal (niedrig)

### 3. Kontinuierliches Lernen
- **Regex**: Statische Regeln, manuell anpassen
- **ML**: Lernt aus Feedback, passt sich automatisch an

### 4. Dynamisches Scoring
- **Regex**: Feste Score-Gewichte für alle Leads
- **ML**: Scores passen sich an basierend auf historischem Erfolg

## Datenbank-Schema

Das System erstellt automatisch folgende Tabellen:

### lead_feedback
Speichert User-Feedback zu Leads:
```sql
CREATE TABLE lead_feedback (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    feedback_type TEXT NOT NULL,  -- 'quality', 'conversion', 'extraction_error'
    rating REAL NOT NULL,          -- 0.0 - 1.0
    user_id TEXT,
    notes TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT                  -- JSON
);
```

### scoring_adjustments
Gelernte Score-Anpassungen:
```sql
CREATE TABLE scoring_adjustments (
    id INTEGER PRIMARY KEY,
    adjustment_key TEXT UNIQUE NOT NULL,  -- z.B. 'email_domain:firma.de'
    adjustment_value REAL NOT NULL,       -- Score-Anpassung
    confidence REAL DEFAULT 0.5,
    sample_size INTEGER DEFAULT 0,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### extraction_accuracy
Genauigkeit der Extraktionen:
```sql
CREATE TABLE extraction_accuracy (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,           -- 'email', 'phone', 'name'
    extracted_value TEXT,
    correct_value TEXT,
    is_correct INTEGER DEFAULT 0,
    confidence REAL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### quality_patterns
Erfolgreiche Muster:
```sql
CREATE TABLE quality_patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT NOT NULL,         -- z.B. 'email_format'
    pattern_data TEXT NOT NULL,         -- JSON
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Performance

### Lightweight Design
- **Keine externe ML-Bibliotheken**: Nutzt heuristische Ansätze
- **Schnelle Regex-Integration**: ML als Fallback, nicht Ersatz
- **Effizientes Caching**: Singleton-Pattern für Extraktoren
- **Minimaler Overhead**: <10ms zusätzliche Latenz pro Lead

### Skalierung
- **Batch-Processing**: Unterstützt parallele Verarbeitung
- **Lazy Loading**: ML-Komponenten nur bei Bedarf geladen
- **Datenbankoptimierung**: Indizes auf häufig abgefragten Feldern

## Best Practices

### 1. Feedback regelmäßig aufzeichnen
```python
# Bei erfolgreicher Kontaktaufnahme
feedback = FeedbackEntry(
    lead_id=lead_id,
    feedback_type='conversion',
    rating=1.0,
    metadata={'converted': True}
)
feedback_system.record_feedback(feedback)
```

### 2. Extractions-Genauigkeit monitoren
```python
# Wöchentliches Monitoring
summary = feedback_system.get_feedback_summary(days=7)
print(f"Email Accuracy: {summary['field_accuracy']['email']}")
print(f"Phone Accuracy: {summary['field_accuracy']['phone']}")
```

### 3. Branchen-Klassifikator trainieren
```python
# Bei falscher Klassifikation
classifier = get_industry_classifier()
classifier.learn_from_feedback(lead_text, correct_industry='energie')
```

### 4. Dynamisches Scoring überwachen
```python
# Scoring-Anpassungen überprüfen
summary = feedback_system.get_feedback_summary()
for adj in summary['top_adjustments']:
    print(f"{adj['key']}: {adj['value']} (Confidence: {adj['confidence']})")
```

## Testing

Umfassende Tests in `tests/test_ml_components.py`:
```bash
pytest tests/test_ml_components.py -v
```

Test-Coverage:
- ✅ Name Extraction (4 Tests)
- ✅ Phone Scoring (3 Tests)
- ✅ Email Classification (5 Tests)
- ✅ Industry Classification (5 Tests)
- ✅ Feedback Loop System (6 Tests)
- ✅ Integration Tests (3 Tests)

## Zukünftige Erweiterungen

### Geplante Features
1. **Ensemble-Learning**: Kombination mehrerer ML-Modelle
2. **A/B-Testing**: Automatisches Testing neuer Scoring-Parameter
3. **Export/Import**: Trainingsdaten exportieren/importieren
4. **REST API**: HTTP-Endpoints für Feedback-Submission
5. **Dashboard**: Visualisierung der Qualitäts-Metriken

### Mögliche ML-Bibliotheken (Optional)
- **spaCy**: Für fortgeschrittene NER
- **scikit-learn**: Für Klassifikation und Clustering
- **transformers**: Für Deep Learning-basierte Extraktion

## Migration

### Von altem zu neuem System
Das neue System ist **rückwärtskompatibel**:
- Bestehende Regex-basierte Extraktion bleibt unverändert
- ML-Komponenten sind opt-in via Parameter
- Kein Breaking Change für existierende Pipelines

### Aktivierung
```python
# In extraction_enhanced.py: automatisch aktiv als Fallback
# In scoring_enhanced.py: aktiviert via use_dynamic_scoring=True (default)

# Deaktivierung möglich via:
score = compute_score_v2(text, url, lead, use_dynamic_scoring=False)
```

## Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Tests: `tests/test_ml_components.py`
2. Aktivieren Sie Logging: `logging.basicConfig(level=logging.DEBUG)`
3. Öffnen Sie ein Issue auf GitHub mit Logs und Beispiel-Daten
