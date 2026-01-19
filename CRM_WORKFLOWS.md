# CRM-Workflows: Produktreife UX

Dieses Dokument beschreibt die drei Kern-Workflows des TELIS CRM-Systems.

## Übersicht

Das CRM wurde von "funktioniert" zu "arbeitet für mich" weiterentwickelt mit einem Fokus auf:
- ✅ Schnelle, übersichtliche Bedienung
- ✅ Geführte Workflows für typische Aufgaben
- ✅ Batch-Operationen für Effizienz
- ✅ Entscheidungsunterstützung durch Qualitätsmetriken

---

## Workflow 1: Leads prüfen & qualifizieren

### Ziel
Eingehende Leads schnell bewerten und für die weitere Bearbeitung vorbereiten.

### Schritte

#### 1. Dashboard aufrufen
- URL: `/crm/`
- Übersicht über neue Leads heute/Woche/Monat
- Hot Leads (Score ≥ 80) werden hervorgehoben
- Top-Quellen und Fehlergründe sind sofort sichtbar

#### 2. Lead-Liste filtern
- URL: `/crm/leads/`
- **Filter-Optionen:**
  - Status (Neu, Kontaktiert, etc.)
  - Quelle (Scraper, Landing Page, etc.)
  - Quality Score (Hot ≥80, Medium 50-79, Low <50)
  - Volltext-Suche (Name, Email, Telefon, Firma)

#### 3. Lead-Details prüfen
- Lead anklicken für Detailansicht
- **"Was wurde gefunden?"** - Sektion zeigt:
  - ✅/❌ Telefon vorhanden
  - ✅/❌ E-Mail vorhanden
  - ✅/❌ Firma bekannt
  - ✅/❌ Standort verfügbar

- **"Wie sicher ist das?"** - Sektion zeigt:
  - Quality Score (0-100)
  - AI Confidence Score
  - Datenqualität-Prozentsatz
  - Datenvollständigkeit-Check

#### 4. Entscheidung treffen
- **Action-Buttons rechts:**
  - ✅ **Freigeben** - Lead für Follow-up freigeben
  - ❌ **Ablehnen** - Lead als ungültig markieren
  - 🔍 **Nachrecherchieren** - Mehr Informationen sammeln
  - 📞 **Anrufen** - Sofort kontaktieren
  - ✉️ **E-Mail senden** - Email-Workflow starten

#### 5. Notizen und Tags hinzufügen
- **Notizen** für interne Kommunikation
- **Tags** für Kategorisierung (z.B. "NRW", "mobile", "high-priority")

### Batch-Qualifizierung
Für mehrere Leads gleichzeitig:
1. Leads in Liste auswählen (Checkbox)
2. Batch-Aktionen oben erscheinen
3. **Optionen:**
   - Status ändern (mehrere auf einmal)
   - Tags hinzufügen
   - Zuweisen an Mitarbeiter
   - Löschen

---

## Workflow 2: Follow-up vorbereiten

### Ziel
Qualifizierte Leads für Telefonteam oder E-Mail-Kampagnen exportieren.

### Schritte

#### 1. Filter anwenden
- Lead-Liste mit gewünschten Kriterien filtern
- Beispiel: "Callcenter NRW, mobile only, Score > 70"

#### 2. Filter speichern (optional)
- Button "Gespeicherte Filter" → "Filter speichern"
- Name vergeben (z.B. "Callcenter NRW High Quality")
- Optional: Mit Team teilen
- **Vorteil:** Wiederverwendbar für zukünftige Exporte

#### 3. Leads auswählen
- **Option A:** Alle Leads auf aktueller Seite
- **Option B:** Einzelne Leads per Checkbox
- **Option C:** Gespeicherten Filter anwenden

#### 4. Export durchführen
- Button "Export CSV"
- **CSV enthält:**
  - Name, E-Mail, Telefon
  - Status, Quality Score
  - Firma, Standort
  - Tags, Notizen
  - Letzter Kontakt

#### 5. In Callcenter-System importieren
- CSV in Telefonie-Software laden
- Alternativ: In E-Mail-Marketing-Tool importieren

### Vorlagen-System (geplant)
- E-Mail-Vorlagen für verschiedene Lead-Typen
- WhatsApp-Nachrichten-Vorlagen
- SMS-Vorlagen

### Aufgaben-System (geplant)
- Follow-up-Datum setzen
- Erinnerungen für Team
- Automatische Benachrichtigungen

---

## Workflow 3: Quelle & Qualität kontrollieren

### Ziel
Überwachen, welche Lead-Quellen die besten Ergebnisse liefern.

### Schritte

#### 1. Dashboard-Metriken prüfen
- **Top-Quellen nach Qualität:**
  - Conversion Rate pro Quelle
  - Ø Quality Score pro Quelle
  - Anzahl Leads pro Quelle

- **Top-Fehlergründe:**
  - Kein Telefon gefunden
  - Ungültiger Lead
  - Keine E-Mail gefunden

- **Datenqualität-Trend:**
  - Durchschnittlicher Score der letzten 7 Tage
  - Visueller Trend (Graph)

#### 2. Fehleranalyse
- Fehlergründe nach Häufigkeit sortiert
- Identifizierung problematischer Portale
- Entscheidung: Portal deaktivieren oder Scraper anpassen

#### 3. Portal-Performance (in Dashboard integriert)
- **Metriken pro Quelle:**
  - Conversion Rate (%)
  - Durchschnittlicher Quality Score
  - Anzahl erfolgreicher Leads
  - Anzahl invalider Leads

#### 4. Optimierungen einleiten
- Schwache Quellen identifizieren
- Scraper-Konfiguration anpassen
- A/B-Tests mit verschiedenen Suchparametern

---

## Technische Details

### Neue API-Endpunkte

#### Batch-Operationen
- `POST /api/leads/batch_update_status/` - Status für mehrere Leads ändern
- `POST /api/leads/batch_add_tags/` - Tags zu mehreren Leads hinzufügen
- `POST /api/leads/batch_assign/` - Leads zuweisen
- `POST /api/leads/batch_delete/` - Mehrere Leads löschen

#### Gespeicherte Filter
- `GET /crm/api/saved-filters/` - Liste aller Filter
- `POST /crm/api/saved-filters/` - Neuen Filter speichern
- `PUT /crm/api/saved-filters/{id}/` - Filter aktualisieren
- `DELETE /crm/api/saved-filters/{id}/` - Filter löschen

### Datenbank-Modelle

#### SavedFilter
```python
class SavedFilter(models.Model):
    user = ForeignKey(User)
    name = CharField(max_length=100)
    description = TextField(blank=True)
    filter_params = JSONField()  # Speichert Filter-Einstellungen
    is_shared = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

### Dashboard-Erweiterungen

#### Neue KPIs
- Leads heute / Woche / Monat
- Top 5 Quellen nach Conversion Rate
- Top 5 Fehlergründe
- Datenqualität-Trend (7 Tage)

#### Neue Charts
- Quality Trend Chart (Linien-Chart)
- Erweiterte Source Distribution

---

## Best Practices

### Lead-Qualifizierung
1. **Schnell-Check:** Quality Score ≥ 80 = Sofort kontaktieren
2. **Medium-Leads:** Score 50-79 = Nachqualifizierung
3. **Low-Leads:** Score < 50 = Ablehnen oder nachrecherchieren

### Batch-Operationen
- Max. 50 Leads gleichzeitig bearbeiten (Performance)
- Tags konsistent verwenden (z.B. immer Kleinbuchstaben)
- Status-Änderungen dokumentieren in Notizen

### Filter-Management
- Aussagekräftige Namen verwenden
- Beschreibung hinzufügen für Team-Transparenz
- Nicht mehr benötigte Filter löschen
- Wichtige Filter mit Team teilen

---

## Keyboard Shortcuts (geplant)
- `Ctrl+F` - Suche fokussieren
- `Ctrl+E` - Export starten
- `Ctrl+A` - Alle auswählen
- `Space` - Lead-Details öffnen/schließen
- `←/→` - Zwischen Leads navigieren

---

## Support & Feedback
Bei Fragen oder Verbesserungsvorschlägen:
- GitHub Issues erstellen
- Team-Chat nutzen
- Dokumentation unter `/docs/` lesen
