# Sourcing-Roadmap: Vertriebskandidaten in NRW/Deutschland

## Übersicht

Diese Roadmap beschreibt **18 neue Quellentypen** für die Lead-Generierung von Vertriebskandidaten in Deutschland mit Fokus auf NRW. Die Zielgruppe umfasst:

- **Handelsvertreter, Außendienstler, Vertriebsmitarbeiter**
- **Unzufriedene Angestellte, Quereinsteiger** (suchen "mehr Geld"/Provision)
- **Aktive Arbeitsuchende**, die eigene Stellengesuche veröffentlichen

> **Nicht abgedeckt**: eBay Kleinanzeigen (bereits vorhanden), klassische Jobboards (Indeed, Stepstone, Jooble, HeyJobs)

---

## Priorisierte Quellentypen (Impact × Umsetzbarkeit)

### 🏆 TOP 5 PRIORITÄT (Sofort umsetzen)

---

### 1. 📋 CDH Handelsvertreter-Verzeichnis & Regionalverbände

**Warum relevant:**
Der CDH (Centralvereinigung Deutscher Wirtschaftsverbände für Handelsvermittlung und Vertrieb) ist die zentrale Anlaufstelle für selbstständige Handelsvertreter. Diese Personen sind bereits im Vertrieb aktiv, provisionsgetrieben und oft offen für neue Vertretungen oder Karrierewechsel.

**Konkrete Domains:**
- `cdh.de` - Bundesverband mit Handelsvertretersuche
- `cdh-nrw.de` - Landesverband NRW
- `cdh-wirtschaftsdienst.de` - Vermittlungsportal

**Suchstrategien:**
```
# Google Dork: Handelsvertreterprofile finden
site:cdh.de "Handelsvertreter" "NRW" (kontakt OR telefon OR email)
site:cdh.de inurl:mitglieder "Vertrieb"

# Sitemap-Discovery
site:cdh.de filetype:xml sitemap
```

**Umsetzung:** ⭐⭐⭐⭐⭐ (strukturierte Profile, öffentlich zugänglich)  
**Impact:** ⭐⭐⭐⭐⭐ (direkte Zielgruppe)

---

### 2. 🏭 IHK-Firmendatenbanken & Mitgliederverzeichnisse

**Warum relevant:**
Die IHKs in NRW pflegen umfangreiche Firmendatenbanken mit Ansprechpartnern. Vertriebsleiter und Vertriebsmitarbeiter sind oft namentlich genannt. Diese Kontakte sind verifiziert und qualitativ hochwertig.

**Konkrete Domains:**
- `ihk-koeln.de/firmensuche`
- `ihk-duesseldorf.de/firmen`
- `ihk-dortmund.de/mitglieder`
- `ihk-nrw.de` (Dachverband)

**Suchstrategien:**
```
# Vertriebsansprechpartner in IHK-Datenbanken
site:ihk-koeln.de "Vertriebsleiter" (telefon OR email)
site:ihk-duesseldorf.de inurl:firmen "Ansprechpartner" "Vertrieb"

# Branchenspezifisch
site:ihk.de "Maschinenbau" "Vertrieb" "NRW" kontakt
```

**Umsetzung:** ⭐⭐⭐⭐⭐ (gut strukturiert, viele regionale Varianten)  
**Impact:** ⭐⭐⭐⭐⭐ (verifizierte B2B-Kontakte)

---

### 3. 💼 Regionale Stellengesuche-Portale (nicht klassische Jobboards)

**Warum relevant:**
Neben den großen Jobboards gibt es regionale Portale, wo Kandidaten SELBST Stellengesuche schreiben ("Ich suche...", "Vertriebsprofi bietet an"). Diese Kandidaten sind proaktiv und motiviert.

**Konkrete Domains:**
- `meinestadt.de/stellengesuche` - Regionale Gesuche
- `markt.de/stellengesuche` - Klassifizierte Anzeigen
- `quoka.de/stellengesuche` - Kleinanzeigenportal
- `kalaydo.de` - Rheinland-Portal (Köln-basiert)

**Suchstrategien:**
```
# Stellengesuche von Vertrieblern
site:meinestadt.de/*/stellengesuche "Vertrieb" (NRW OR Köln OR Düsseldorf)
site:markt.de "suche Stelle" "Vertrieb" OR "Außendienst"
site:kalaydo.de "biete" "Vertriebserfahrung"

# Proaktive Kandidaten
site:quoka.de "Handelsvertreter" "suche" OR "biete" kontakt
```

**Umsetzung:** ⭐⭐⭐⭐⭐ (einfaches HTML-Scraping)  
**Impact:** ⭐⭐⭐⭐⭐ (proaktive Kandidaten mit Eigenmotivation)

---

### 4. 🎪 Messe-Ausstellerverzeichnisse (NRW-Fokus)

**Warum relevant:**
Messeaussteller haben fast immer Vertriebsteams. Die Ausstellerverzeichnisse enthalten Kontaktdaten, oft mit direkten Ansprechpartnern. Messebau-/Vertriebspersonal ist oft provisionsaffin und wechselwillig.

**Konkrete Domains:**
- `messe-duesseldorf.de` - Größte Messe in NRW
- `koelnmesse.de` - Köln Messe
- `westfalenhallen.de` - Dortmund
- `messe-essen.de` - Essen
- `auma.de` - AUMA Messeverzeichnis (bundesweit)

**Suchstrategien:**
```
# Aussteller mit Vertriebskontakten
site:messe-duesseldorf.de inurl:aussteller "Vertrieb" kontakt
site:koelnmesse.de "Ausstellerverzeichnis" telefon

# Branchenmessen finden
site:auma.de "Messe" "NRW" "Vertrieb" OR "Sales"

# Direkt über Messekataloge
site:messe-duesseldorf.de filetype:pdf "Aussteller" "Ansprechpartner"
```

**Umsetzung:** ⭐⭐⭐⭐ (gut strukturierte Ausstellerlisten)  
**Impact:** ⭐⭐⭐⭐⭐ (direkte B2B-Kontakte mit Vertriebsbezug)

---

### 5. 📱 Xing/LinkedIn Gruppen & Community-Diskussionen

**Warum relevant:**
In Business-Netzwerk-Gruppen diskutieren Vertriebsprofis über Gehalt, Provision, Jobwechsel. Personen, die dort aktiv sind, signalisieren Unzufriedenheit oder Interesse an Veränderung. Direkter Zugang zu "unzufriedenen Angestellten".

**Konkrete Domains:**
- `xing.com/communities` - Xing Gruppen
- `linkedin.com/groups` - LinkedIn Gruppen
- `xing.com/profile` - Profile mit Kontaktangaben

**Suchstrategien:**
```
# Xing-Gruppen zum Thema Vertrieb/Karriere
site:xing.com/communities "Vertrieb" "Gehalt" OR "Provision" OR "Karriere"
site:xing.com/communities "Handelsvertreter" "NRW"

# Profile mit Wechselwunsch-Signalen
site:xing.com/profile "Vertrieb" "offen für" NRW
site:linkedin.com/in "Sales" "looking for" "Germany" -#opentowork

# Diskussionen über Unzufriedenheit
site:xing.com "Vertrieb" "mehr verdienen" OR "bessere Provision"
```

**Umsetzung:** ⭐⭐⭐⭐ (Anti-Scraping-Maßnahmen beachten)  
**Impact:** ⭐⭐⭐⭐⭐ (direkte Signale für Wechselbereitschaft)

---

### 🔵 MITTLERE PRIORITÄT (Nächste Phase)

---

### 6. 🏢 Branchenverbände mit Mitgliederlisten

**Warum relevant:**
Branchenverbände veröffentlichen oft Mitgliederlisten mit Ansprechpartnern. Diese sind branchenspezifisch und qualitativ hochwertig. Besonders relevant: Verbände mit provisionsbasierten Branchen.

**Konkrete Domains:**
- `bvmw.de` - Bundesverband mittelständische Wirtschaft
- `bdvb.de` - Bundesverband Deutscher Volks- und Betriebswirte
- `vdma.org` - Verband Deutscher Maschinen- und Anlagenbau
- `bvoh.de` - Bundesverband Onlinehandel
- `bdi.eu` - Bundesverband der Deutschen Industrie

**Suchstrategien:**
```
# Mitgliederlisten durchsuchen
site:bvmw.de "Mitglieder" "NRW" "Vertrieb" kontakt
site:vdma.org "Mitgliedsunternehmen" "Ansprechpartner" telefon

# Veranstaltungen/Netzwerktreffen
site:bvmw.de "Veranstaltung" "Vertrieb" "NRW"
```

**Umsetzung:** ⭐⭐⭐⭐ (strukturierte Mitgliederlisten)  
**Impact:** ⭐⭐⭐⭐ (qualifizierte B2B-Kontakte)

---

### 7. 🚗 Automotive-Vertrieb (Autohäuser, Händler)

**Warum relevant:**
Autoverkäufer sind klassische Provisionsempfänger und oft wechselwillig. Branche mit hoher Fluktuation und klarer Leistungsorientierung. Viele suchen nach besseren Verdienstmöglichkeiten.

**Konkrete Domains:**
- `mobile.de/haendler` - Händlerverzeichnis
- `autoscout24.de/haendler` - Händlerprofile
- `kfz-betrieb.vogel.de` - Branchenportal
- `autohaus.de` - Fachmagazin mit Branchenkontakten

**Suchstrategien:**
```
# Autohaus-Verkäufer finden
site:mobile.de/haendler "NRW" "Verkaufsberater" OR "Verkäufer"
site:autoscout24.de "Autohaus" "NRW" kontakt "Verkauf"

# Branchenspezifisch
site:autohaus.de "Verkaufsleiter" "NRW" telefon
"Automobilverkäufer" "suche neue Herausforderung" NRW
```

**Umsetzung:** ⭐⭐⭐⭐ (strukturierte Händlerverzeichnisse)  
**Impact:** ⭐⭐⭐⭐ (provisionsaffine Zielgruppe)

---

### 8. 🏠 Immobilien-Vertrieb (Makler, Berater)

**Warum relevant:**
Immobilienmakler arbeiten fast ausschließlich auf Provisionsbasis. Hohe Fluktuation, viele Quereinsteiger, klarer Fokus auf Verdienst. IVD-Mitgliederlisten sind goldwert.

**Konkrete Domains:**
- `immobilienscout24.de/maklersuche` - Maklerverzeichnis
- `immowelt.de/makler` - Maklerprofile
- `ivd.net` - Immobilienverband Deutschland (Mitgliederliste)
- `immobilien-zeitung.de` - Branchenportal

**Suchstrategien:**
```
# Makler mit Kontaktdaten
site:immobilienscout24.de "Makler" "NRW" telefon
site:ivd.net "Mitglied" "NRW" "Immobilienmakler" kontakt

# Wechselwillige Makler
"Immobilienmakler" "suche" "neue Herausforderung" NRW
site:xing.com/profile "Immobilienmakler" "offen für" NRW
```

**Umsetzung:** ⭐⭐⭐⭐ (gut strukturierte Verzeichnisse)  
**Impact:** ⭐⭐⭐⭐ (100% provisionsbasierte Zielgruppe)

---

### 9. 📞 Versicherungs- & Finanzvertrieb

**Warum relevant:**
Versicherungsvertreter und Finanzberater sind klassische Provisionsempfänger. Hohe Fluktuation, strukturierte Vermittlerregister, oft unzufrieden mit Konditionen.

**Konkrete Domains:**
- `vermittlerregister.info` - Offizielles Vermittlerregister
- `bvk.de` - Bundesverband Deutscher Versicherungskaufleute
- `afz.de` - AllFinanzZeitung
- `procontra.de` - Branchenportal

**Suchstrategien:**
```
# Vermittlerregister durchsuchen
site:vermittlerregister.info "NRW" "Versicherungsvermittler"
site:bvk.de "Mitglied" "NRW" kontakt

# Unzufriedene Vertreter
"Versicherungsvertreter" "suche" "bessere Konditionen" OR "neue Gesellschaft"
site:xing.com/profile "Versicherungskaufmann" "offen für"
```

**Umsetzung:** ⭐⭐⭐⭐ (reguliertes Register = strukturierte Daten)  
**Impact:** ⭐⭐⭐⭐ (provisionsaffine Zielgruppe)

---

### 10. 🏋️ MLM/Network-Marketing Communities

**Warum relevant:**
Personen im Network-Marketing sind extrem provisionsgetrieben und oft unzufrieden mit ihrem aktuellen "Upline". Sie suchen aktiv nach besseren Verdienstmöglichkeiten und sind offen für Vertriebsjobs.

**Konkrete Domains:**
- `network-marketing.de` - Community-Portal
- `mlm-community.de` - Diskussionsforum
- `networkmarketingmagazin.com` - Branchenmagazin
- `mlm-erfahrungen.de` - Erfahrungsberichte

**Suchstrategien:**
```
# Unzufriedene MLM-Vertriebler
site:network-marketing.de "suche" "bessere Vergütung" OR "neues Unternehmen"
"Network Marketing" "aufhören" OR "wechseln" NRW

# Forum-Diskussionen
site:mlm-community.de "Erfahrungen" "Provision" "unzufrieden"
```

**Umsetzung:** ⭐⭐⭐ (Foren-Scraping komplexer)  
**Impact:** ⭐⭐⭐⭐⭐ (höchste Provisionsaffinität)

---

### 11. 💻 IT-Sales & SaaS-Vertrieb

**Warum relevant:**
IT-Vertrieb ist ein wachsender Bereich mit hohen Provisionen. Viele Quereinsteiger, hohe Fluktuation, aktive Community. Sales Development Representatives (SDRs) sind oft wechselwillig.

**Konkrete Domains:**
- `t3n.de/jobs` - Tech-Jobportal mit Stellengesuchen
- `it-talents.de` - IT-Karriereportal
- `gruenderszene.de` - Startup-Szene
- `saas-mag.com` - SaaS-Branchenportal

**Suchstrategien:**
```
# IT-Sales Profile
site:xing.com/profile "Sales Development" OR "Account Executive" "SaaS"
site:linkedin.com/in "IT Sales" "Germany" -#opentowork

# Tech-Sales Community
site:t3n.de "Sales" "suche" OR "biete"
site:gruenderszene.de "Vertrieb" "Startup" NRW
```

**Umsetzung:** ⭐⭐⭐⭐ (gut vernetzte Community)  
**Impact:** ⭐⭐⭐⭐ (wachsender, provisionsstarker Bereich)

---

### 12. 🛒 E-Commerce & Amazon-Händler

**Warum relevant:**
E-Commerce-Händler suchen oft Vertriebsunterstützung. Viele haben Kontaktdaten auf ihren Shops. Amazon-Händler (FBA-Seller) sind oft selbstständig und offen für neue Möglichkeiten.

**Konkrete Domains:**
- `amazon.de/sp` - Amazon Händlerprofile
- `shopware.com/de/partner` - Shopware-Partner
- `ecommerce-news.de` - Branchenportal
- `wortfilter.de` - Amazon-Händler-Community

**Suchstrategien:**
```
# Amazon-Händler
site:amazon.de/sp "NRW" OR "Nordrhein-Westfalen" kontakt
site:wortfilter.de "Händler" "suche" "Vertrieb"

# E-Commerce Dienstleister
site:shopware.com/de/partner "NRW" kontakt
```

**Umsetzung:** ⭐⭐⭐ (Amazon-Scraping schwieriger)  
**Impact:** ⭐⭐⭐⭐ (wachsende Branche)

---

### 🔹 NIEDRIGERE PRIORITÄT (Langfristig)

---

### 13. 📚 Karriere-Foren & Diskussionsplattformen

**Warum relevant:**
In Karriereforen diskutieren Menschen über Jobwechsel, Gehalt und Unzufriedenheit. Direkter Zugang zu Personen, die über Veränderung nachdenken.

**Konkrete Domains:**
- `gutefrage.net` - Q&A-Plattform
- `reddit.com/r/de_jobs` - Reddit Jobs Deutschland
- `getsafe.de/blog` - Finanz-Community
- `financescout24.de/forum` - Finanzen/Karriere

**Suchstrategien:**
```
# Karrierefragen
site:gutefrage.net "Vertrieb" "mehr verdienen" OR "Jobwechsel"
site:reddit.com/r/de "Vertrieb" "Gehalt" OR "Provision"

# Unzufriedenheit
site:gutefrage.net "unzufrieden" "Vertrieb" OR "Verkauf"
```

**Umsetzung:** ⭐⭐⭐ (Foren-Struktur variiert)  
**Impact:** ⭐⭐⭐ (indirekte Signale)

---

### 14. 🎓 IHK-Weiterbildung & Vertriebszertifikate

**Warum relevant:**
Personen, die Vertriebsweiterbildungen machen (Verkaufsleiter IHK, Handelsfachwirt), sind karriereorientiert und suchen nach Aufstieg oder Wechsel.

**Konkrete Domains:**
- `ihk-akademie-muenchen.de` - IHK Akademien
- `dihk-bildung.de` - DIHK Weiterbildung
- `salesjob.de` - Vertriebskarriere

**Suchstrategien:**
```
# Weiterbildungsteilnehmer
site:ihk.de "Weiterbildung" "Vertrieb" "Teilnehmer" NRW
"Verkaufsleiter IHK" "suche" OR "biete"

# Karriereorientierte Profile
site:xing.com/profile "Handelsfachwirt" "suche" NRW
```

**Umsetzung:** ⭐⭐⭐ (weniger direkte Kontaktdaten)  
**Impact:** ⭐⭐⭐ (karriereorientierte Personen)

---

### 15. 🏗️ Handwerk & Bauwesen (Vertriebsaußendienst)

**Warum relevant:**
Handwerksbetriebe und Bauzulieferer haben oft Außendienstmitarbeiter. Die Handwerkskammern führen Verzeichnisse. Provisionsmodelle sind üblich.

**Konkrete Domains:**
- `hwk-koeln.de` - Handwerkskammer Köln
- `hwk-duesseldorf.de` - Handwerkskammer Düsseldorf
- `baulinks.de` - Baubranche
- `dachdecker.org` - Branchenverband

**Suchstrategien:**
```
# Handwerksbetriebe mit Vertrieb
site:hwk-koeln.de "Betrieb" "Vertrieb" OR "Außendienst" kontakt
site:baulinks.de "Hersteller" "Vertrieb" NRW telefon
```

**Umsetzung:** ⭐⭐⭐⭐ (strukturierte Verzeichnisse)  
**Impact:** ⭐⭐⭐ (spezialisierter Bereich)

---

### 16. 🎯 Direktvertrieb-Verbände (BDD)

**Warum relevant:**
Der Bundesverband Direktvertrieb Deutschland (BDD) vereint Unternehmen im Direktvertrieb. Deren Vertriebspartner sind per Definition provisionsgetrieben.

**Konkrete Domains:**
- `direktvertrieb.de` - Bundesverband
- `bdd.de` - BDD Verband
- `vorwerk.de/karriere` - Direktvertrieb-Beispiel

**Suchstrategien:**
```
# Direktvertrieb-Unternehmen
site:direktvertrieb.de "Mitglied" "Vertriebspartner" kontakt
site:bdd.de "Unternehmen" "Partner" NRW

# Vertriebspartner suchen
"Direktvertrieb" "suche neue Herausforderung" NRW
```

**Umsetzung:** ⭐⭐⭐⭐ (offizielle Verbandslisten)  
**Impact:** ⭐⭐⭐ (spezialisiert auf Direktvertrieb)

---

### 17. 📰 Branchennewsletter & Fachmagazine

**Warum relevant:**
Fachmagazine für Vertrieb haben oft Autoren, Experten und Leser, die im Vertrieb tätig sind. Gastbeiträge und Interviewpartner sind direkte Kontakte.

**Konkrete Domains:**
- `vertriebszeitung.de` - Vertriebsfachmagazin
- `salesbusiness.de` - Sales-Magazin
- `acquisa.de` - Vertrieb & Marketing
- `handelsblatt.com/karriere` - Karriere-Sektion

**Suchstrategien:**
```
# Autoren und Experten
site:vertriebszeitung.de "Autor" "Vertriebsleiter" kontakt
site:salesbusiness.de "Interview" "Sales Manager" NRW

# Karriere-Artikel
site:handelsblatt.com "Vertrieb" "Gehalt" OR "Karriere"
```

**Umsetzung:** ⭐⭐⭐ (weniger strukturierte Daten)  
**Impact:** ⭐⭐⭐ (Experten, aber weniger Masse)

---

### 18. 🌐 Lokale Business-Netzwerke & BNI

**Warum relevant:**
Business Network International (BNI) und lokale Unternehmerkreise haben Mitgliederlisten mit Selbstständigen und Vertrieblern. Persönliche Netzwerke mit hoher Kontaktqualität.

**Konkrete Domains:**
- `bni.de/de-de/regionen` - BNI Deutschland
- `unternehmernetzwerk.de` - Lokale Netzwerke
- `wirtschaftsjunioren.de` - Junge Unternehmer
- `rotary.de` - Rotary Clubs (Geschäftsleute)

**Suchstrategien:**
```
# BNI-Mitglieder
site:bni.de "Chapter" "NRW" "Vertrieb" OR "Sales"
site:bni.de/de-de/regionen "Düsseldorf" OR "Köln" "Mitglieder"

# Lokale Netzwerke
site:wirtschaftsjunioren.de "NRW" "Mitglieder" kontakt
```

**Umsetzung:** ⭐⭐⭐ (Mitgliederbereiche oft geschützt)  
**Impact:** ⭐⭐⭐ (hochqualitativ, aber weniger Volumen)

---

## Zusammenfassung: Implementierungs-Roadmap

### Phase 1: Quick Wins (Woche 1-2)
| # | Quellentyp | Impact | Aufwand | URLs |
|---|------------|--------|---------|------|
| 1 | CDH Handelsvertreter | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | cdh.de, cdh-nrw.de |
| 2 | IHK-Firmendatenbanken | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ihk-*.de |
| 3 | Regionale Stellengesuche | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | meinestadt.de, markt.de, kalaydo.de |
| 4 | Messe-Ausstellerverzeichnisse | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | messe-duesseldorf.de, koelnmesse.de |
| 5 | Xing/LinkedIn Gruppen | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | xing.com/communities |

### Phase 2: Branchenspezifisch (Woche 3-4)
| # | Quellentyp | Impact | Aufwand | URLs |
|---|------------|--------|---------|------|
| 6 | Branchenverbände | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | bvmw.de, vdma.org |
| 7 | Automotive-Vertrieb | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | mobile.de/haendler |
| 8 | Immobilien-Vertrieb | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ivd.net, immobilienscout24.de |
| 9 | Versicherungsvertrieb | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | vermittlerregister.info |
| 10 | MLM/Network-Marketing | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | mlm-community.de |

### Phase 3: Erweiterung (Woche 5-6)
| # | Quellentyp | Impact | Aufwand | URLs |
|---|------------|--------|---------|------|
| 11 | IT-Sales/SaaS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | t3n.de, gruenderszene.de |
| 12 | E-Commerce/Amazon | ⭐⭐⭐⭐ | ⭐⭐⭐ | amazon.de/sp |
| 13 | Karriere-Foren | ⭐⭐⭐ | ⭐⭐⭐ | gutefrage.net |
| 14 | IHK-Weiterbildung | ⭐⭐⭐ | ⭐⭐⭐ | ihk-akademie*.de |

### Phase 4: Langfristig (Woche 7+)
| # | Quellentyp | Impact | Aufwand | URLs |
|---|------------|--------|---------|------|
| 15 | Handwerk/Bauwesen | ⭐⭐⭐ | ⭐⭐⭐⭐ | hwk-*.de |
| 16 | Direktvertrieb (BDD) | ⭐⭐⭐ | ⭐⭐⭐⭐ | direktvertrieb.de |
| 17 | Branchenmagazine | ⭐⭐⭐ | ⭐⭐⭐ | vertriebszeitung.de |
| 18 | BNI/Business-Netzwerke | ⭐⭐⭐ | ⭐⭐⭐ | bni.de |

---

## Technische Hinweise für die Scraper-Integration

### Neue Dork-Kategorien (für dorks_extended.py)
```python
# Neue Kategorien hinzufügen:
CDH_HANDELSVERTRETER_DORKS = [...]
REGIONAL_STELLENGESUCHE_DORKS = [...]
MESSE_AUSSTELLER_DORKS = [...]
MLM_NETWORK_DORKS = [...]
VERSICHERUNG_FINANZ_DORKS = [...]
AUTOMOTIVE_SALES_DORKS = [...]
IMMOBILIEN_MAKLER_DORKS = [...]
```

### Neue Portal-URLs (für portal_urls.py)
```python
# Neue Portale hinzufügen:
STELLENGESUCHE_PORTALS = {
    'meinestadt': ['https://www.meinestadt.de/{city}/stellengesuche/vertrieb'],
    'markt_de': ['https://www.markt.de/stellengesuche/vertrieb'],
    'kalaydo': ['https://www.kalaydo.de/jobs/stellengesuche/vertrieb']
}

CDH_PORTALS = {
    'cdh_bundesverband': ['https://www.cdh.de/handelsvertreter-suche'],
    'cdh_nrw': ['https://www.cdh-nrw.de/mitglieder']
}
```

### Empfohlene Delays
| Portal-Typ | Delay (Sekunden) | Grund |
|------------|------------------|-------|
| IHK-Datenbanken | 3-5 | Respektvoller Umgang mit öffentlichen Institutionen |
| Xing/LinkedIn | 5-10 | Anti-Scraping-Maßnahmen |
| Messe-Verzeichnisse | 2-3 | Moderate Nutzung |
| Kleinanzeigen-Portale | 2-4 | Standard |
| Branchenverbände | 3-5 | Kleinere Server |

---

## Erwartete Ergebnisse

Nach vollständiger Implementierung aller 18 Quellentypen:

- **Lead-Volumen:** +80-120% (konservativ geschätzt)
- **Lead-Qualität:** +50% durch Fokus auf provisionsaffine Zielgruppen
- **Conversion Rate:** +30% durch proaktive Kandidaten (Stellengesuche)
- **Diversifikation:** Unabhängigkeit von einzelnen Plattformen

---

## Nächste Schritte

1. ✅ Sourcing-Roadmap erstellt
2. ⬜ Phase 1 Dorks implementieren (CDH, IHK, Stellengesuche)
3. ⬜ Portal-URLs für Phase 1 konfigurieren
4. ⬜ Test-Crawls durchführen
5. ⬜ Performance-Metriken erheben
6. ⬜ Phase 2-4 iterativ umsetzen

---

*Erstellt: Januar 2026*  
*Letzte Aktualisierung: Januar 2026*  
*Status: Phase 1 ready for implementation*
