[1mdiff --git a/scriptname.py b/scriptname.py[m
[1mindex d592f8d..80eee36 100644[m
[1m--- a/scriptname.py[m
[1m+++ b/scriptname.py[m
[36m@@ -1,14 +1,14 @@[m
[31m-# -*- coding: utf-8 -*-[m
[32m+[m[32m﻿# -*- coding: utf-8 -*-[m
 """[m
[31m-Leads-Scraper (NRW Vertrieb/Callcenter/D2D) — robust + inkrementell + UI[m
[32m+[m[32mLeads-Scraper (NRW Vertrieb/Callcenter/D2D) â€” robust + inkrementell + UI[m
 [m
 Features:[m
 - Suche: Google CSE (Key/CX-Rotation, Backoff, Pagination) + Fallback Bing + Seed-URLs[m
 - Fetch: Retries, SSL-Verify mit Fallback (Flag), robots tolerant (Cache)[m
[31m-- Filter: Harter Domain-Block (News/Behörden/Verbände), Pfad-Whitelist, Content-Validation tolerant[m
[32m+[m[32m- Filter: Harter Domain-Block (News/BehÃ¶rden/VerbÃ¤nde), Pfad-Whitelist, Content-Validation tolerant[m
 - Extraktion: OpenAI (JSON) oder Regex (E-Mail/Tel/WhatsApp/wa.me + Namensheuristik); Kleinanzeigen-Extractor[m
 - Scoring: Kontakt-/Branchen-Signale, starker WhatsApp/Telefon/E-Mail-Boost, URL-Hints, dynamischer Schwellenwert[m
[31m-- Enrichment: Firma/Größe/Branche/Region/Frische + Confidence/DataQuality realistisch[m
[32m+[m[32m- Enrichment: Firma/GrÃ¶ÃŸe/Branche/Region/Frische + Confidence/DataQuality realistisch[m
 - Persistenz: SQLite (runs, queries_done, urls_seen, leads) => keine Doppelten, Wiederaufnahme[m
 - Export: CSV/XLSX (append nur neue Leads)[m
 - Depth: Interne Tiefe + Sitemap-Hints[m
[36m@@ -72,7 +72,7 @@[m [mdef export_xlsx(filename: str, rows=None):[m
     df.to_excel(filename, index=False)[m
 [m
 [m
[31m-# Warnungen zu unsicherem SSL dämpfen (bewusstes Fallback via Flag)[m
[32m+[m[32m# Warnungen zu unsicherem SSL dÃ¤mpfen (bewusstes Fallback via Flag)[m
 urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)[m
 [m
 # =========================[m
[36m@@ -274,8 +274,8 @@[m [mdef init_db():[m
 [m
 def migrate_db_unique_indexes():[m
     """[m
[31m-    Fallback für sehr alte Schemas mit harten UNIQUE-Constraints.[m
[31m-    Nur ausführen, wenn Einfügen weiterhin scheitert.[m
[32m+[m[32m    Fallback fÃ¼r sehr alte Schemas mit harten UNIQUE-Constraints.[m
[32m+[m[32m    Nur ausfÃ¼hren, wenn EinfÃ¼gen weiterhin scheitert.[m
     """[m
     con = db(); cur = con.cursor()[m
     try:[m
[36m@@ -359,7 +359,7 @@[m [mdef url_seen(url: str) -> bool:[m
 [m
 def insert_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:[m
     """[m
[31m-    Führt INSERT OR IGNORE aus. Zieht Schema automatisch nach (fehlende Spalten).[m
[32m+[m[32m    FÃ¼hrt INSERT OR IGNORE aus. Zieht Schema automatisch nach (fehlende Spalten).[m
     """[m
     if not leads:[m
         return [][m
[36m@@ -472,7 +472,7 @@[m [mdef reset_history():[m
 [m
 [m
 # =========================[m
[31m-# HTTP/SSL/robots — ASYNC[m
[32m+[m[32m# HTTP/SSL/robots â€” ASYNC[m
 # =========================[m
 [m
 # Content-Guards (konfigurierbar)[m
[36m@@ -583,12 +583,12 @@[m [m_LAST_STATUS: Dict[str, int] = {}[m
 [m
 async def http_get_async(url, headers=None, params=None, timeout=HTTP_TIMEOUT):[m
     """[m
[31m-    GET mit optionalem HEAD-Preflight, Proxys/UA-Rotation, HTTP/2→1.1 Fallback[m
[32m+[m[32m    GET mit optionalem HEAD-Preflight, Proxys/UA-Rotation, HTTP/2â†’1.1 Fallback[m
     Verbesserungen:[m
[31m-      - HEAD-Preflight: 405/501 nicht „bestrafen“ (kein erneutes HEAD), aber bei 405 Host sanft penalizen.[m
[31m-      - Host-Penalty zusätzlich bei 503/504 (Rate drosseln, spätere Retries wahrscheinlicher).[m
[32m+[m[32m      - HEAD-Preflight: 405/501 nicht â€žbestrafenâ€œ (kein erneutes HEAD), aber bei 405 Host sanft penalizen.[m
[32m+[m[32m      - Host-Penalty zusÃ¤tzlich bei 503/504 (Rate drosseln, spÃ¤tere Retries wahrscheinlicher).[m
     """[m
[31m-    # --- Rotation wählen ---[m
[32m+[m[32m    # --- Rotation wÃ¤hlen ---[m
     ua = random.choice(UA_POOL) if UA_POOL else USER_AGENT[m
     proxy = random.choice(PROXY_POOL) if PROXY_POOL else None[m
 [m
[36m@@ -604,14 +604,14 @@[m [masync def http_get_async(url, headers=None, params=None, timeout=HTTP_TIMEOUT):[m
     base_to = max(5, min(timeout, 45))[m
     eff_timeout = base_to + random.uniform(0.0, 1.25)[m
 [m
[31m-    # 1) HEAD-Preflight (secure, HTTP/2/1 je nach Param) – optional[m
[32m+[m[32m    # 1) HEAD-Preflight (secure, HTTP/2/1 je nach Param) â€“ optional[m
     r_head = None[m
     try:[m
         async with _make_client(True, ua, proxy, force_http1=False, timeout_s=eff_timeout) as client_head:[m
             r_head = await client_head.head(url, headers=headers, params=params, follow_redirects=True)[m
             if r_head is not None:[m
[31m-                # Wenn HEAD 405/501 → kein erneutes HEAD versuchen (spart Roundtrips).[m
[31m-                # Zusätzlich: bei 405 sanfte Host-Penalty (viele Sites blocken HEAD hart).[m
[32m+[m[32m                # Wenn HEAD 405/501 â†’ kein erneutes HEAD versuchen (spart Roundtrips).[m
[32m+[m[32m                # ZusÃ¤tzlich: bei 405 sanfte Host-Penalty (viele Sites blocken HEAD hart).[m
                 if r_head.status_code == 405:[m
                     _penalize_host(host)[m
                     log("info", "HEAD 405: host penalized, continue with GET", url=url)[m
[36m@@ -624,14 +624,14 @@[m [masync def http_get_async(url, headers=None, params=None, timeout=HTTP_TIMEOUT):[m
                         log("info", "Head-preflight: skipped by headers", url=url, reason=reason)[m
                         return None[m
     except Exception:[m
[31m-        # Preflight ist optional – still & silent[m
[32m+[m[32m        # Preflight ist optional â€“ still & silent[m
         r_head = None[m
 [m
     async def _do_get(secure: bool, force_http1: bool) -> Optional[httpx.Response]:[m
         async with _make_client(secure, ua, proxy, force_http1, eff_timeout) as cl:[m
             return await cl.get(url, headers=headers, params=params, timeout=eff_timeout, follow_redirects=True)[m
 [m
[31m-    # 2) Primär GET (secure, HTTP/2 erlaubt)[m
[32m+[m[32m    # 2) PrimÃ¤r GET (secure, HTTP/2 erlaubt)[m
     try:[m
         r = await _do_get(secure=True, force_http1=False)[m
         if r.status_code == 200:[m
[36m@@ -702,7 +702,7 @@[m [masync def http_get_async(url, headers=None, params=None, timeout=HTTP_TIMEOUT):[m
             except Exception:[m
                 pass[m
 [m
[31m-    log("error", "HTTP GET endgültig gescheitert", url=url)[m
[32m+[m[32m    log("error", "HTTP GET endgÃ¼ltig gescheitert", url=url)[m
     return None[m
 [m
 [m
[36m@@ -714,7 +714,7 @@[m [masync def fetch_response_async(url: str, headers=None, params=None, timeout=HTTP[m
     status = getattr(r, "status_code", 0)[m
     if status != 200:[m
         _LAST_STATUS[url] = status[m
[31m-        log("warn", "Nicht-200 beim Abruf – skip", url=url, status=status)[m
[32m+[m[32m        log("warn", "Nicht-200 beim Abruf â€“ skip", url=url, status=status)[m
         return None[m
     _LAST_STATUS[url] = 200[m
     return r[m
[36m@@ -739,15 +739,15 @@[m [masync def robots_allowed_async(url: str) -> bool:[m
                 rp.parse(r.text.splitlines())[m
             else:[m
                 _ROBOTS_CACHE[base] = (rp, time.time())[m
[31m-                log("warn", "robots.txt Fetch fehlgeschlagen – konservativ erlauben", url=url)[m
[32m+[m[32m                log("warn", "robots.txt Fetch fehlgeschlagen â€“ konservativ erlauben", url=url)[m
                 return True[m
             _ROBOTS_CACHE[base] = (rp, time.time())[m
 [m
         allowed = _ROBOTS_CACHE[base][0].can_fetch(USER_AGENT, url)[m
[31m-        log("debug", "robots.txt geprüft", url=url, allowed=allowed)[m
[32m+[m[32m        log("debug", "robots.txt geprÃ¼ft", url=url, allowed=allowed)[m
         return allowed[m
     except Exception as e:[m
[31m-        log("warn", "robots.txt Prüfung fehlgeschlagen – konservativ erlauben", url=url, error=str(e))[m
[32m+[m[32m        log("warn", "robots.txt PrÃ¼fung fehlgeschlagen â€“ konservativ erlauben", url=url, error=str(e))[m
         return True[m
 [m
 # =========================[m
[36m@@ -772,17 +772,17 @@[m [mGCS_CX = _normalize_cx(GCS_CX_RAW)[m
 # Multi-Key/CX Rotation + Limits[m
 GCS_KEYS = [k.strip() for k in os.getenv("GCS_KEYS","").split(",") if k.strip()] or ([GCS_API_KEY] if GCS_API_KEY else [])[m
 GCS_CXS  = [_normalize_cx(x) for x in os.getenv("GCS_CXS","").split(",") if _normalize_cx(x)] or ([GCS_CX] if GCS_CX else [])[m
[31m-MAX_GOOGLE_PAGES = int(os.getenv("MAX_GOOGLE_PAGES","12"))  # höherer Default[m
[32m+[m[32mMAX_GOOGLE_PAGES = int(os.getenv("MAX_GOOGLE_PAGES","12"))  # hÃ¶herer Default[m
 [m
 # ======= SUCHE: Branchen & Query-Baukasten (modular) =======[m
[31m-REGION = '(NRW OR "Nordrhein-Westfalen" OR Düsseldorf OR Köln OR Essen OR Dortmund OR Bochum OR Duisburg OR Mönchengladbach)'[m
[32m+[m[32mREGION = '(NRW OR "Nordrhein-Westfalen" OR DÃ¼sseldorf OR KÃ¶ln OR Essen OR Dortmund OR Bochum OR Duisburg OR MÃ¶nchengladbach)'[m
 CONTACT = '(kontakt OR impressum OR ansprechpartner OR "e-mail" OR email OR telefon OR whatsapp)'[m
 SALES   = '(vertrieb OR d2d OR "call center" OR telesales OR outbound OR verkauf OR sales)'[m
 [m
 # Kurze, treffsichere Query-Sets je Branche[m
 INDUSTRY_QUERIES: dict[str, list[str]] = {[m
     "solar": [[m
[31m-        f'site:.de (photovoltaik OR PV OR solar OR wärmepumpe) {SALES} {CONTACT} {REGION}',[m
[32m+[m[32m        f'site:.de (photovoltaik OR PV OR solar OR wÃ¤rmepumpe) {SALES} {CONTACT} {REGION}',[m
         f'site:.de ("per WhatsApp bewerben" OR "WhatsApp Bewerbung") (photovoltaik OR PV OR solar) {REGION}',[m
         f'site:.de (energieberatung OR strom OR gas) {SALES} (ansprechpartner OR team) {REGION}',[m
     ],[m
[36m@@ -797,8 +797,8 @@[m [mINDUSTRY_QUERIES: dict[str, list[str]] = {[m
         f'site:.de (makler OR vermittler) (telesales OR outbound) (ansprechpartner OR team) {REGION}',[m
     ],[m
     "bau": [[m
[31m-        f'site:.de (fenster OR türen OR daemm* OR dämm* OR energieberatung) {SALES} {CONTACT} {REGION}',[m
[31m-        f'site:.de ("per WhatsApp bewerben" OR "WhatsApp Bewerbung") (fenster OR türen) {REGION}',[m
[32m+[m[32m        f'site:.de (fenster OR tÃ¼ren OR daemm* OR dÃ¤mm* OR energieberatung) {SALES} {CONTACT} {REGION}',[m
[32m+[m[32m        f'site:.de ("per WhatsApp bewerben" OR "WhatsApp Bewerbung") (fenster OR tÃ¼ren) {REGION}',[m
         f'site:.de (handwerk OR sanierung) (telesales OR outbound) (ansprechpartner OR team) {REGION}',[m
     ],[m
     "ecom": [[m
[36m@@ -813,7 +813,7 @@[m [mINDUSTRY_QUERIES: dict[str, list[str]] = {[m
     ],[m
     'recruiter': [[m
         # Jobsuchende und Karrierewechsler[m
[31m-        f"site:de vertrieb jobs NRW OR Düsseldorf OR Köln OR Essen OR Dortmund OR Bochum",[m
[32m+[m[32m        f"site:de vertrieb jobs NRW OR DÃ¼sseldorf OR KÃ¶ln OR Essen OR Dortmund OR Bochum",[m
         f"site:de quereinsteiger vertrieb NRW {REGION} provision OR kommission",[m
         f"site:de arbeitslos vertrieb sucht stelle {REGION}",[m
         f"site:de nebenjob vertrieb homeoffice {REGION} provision",[m
[36m@@ -833,11 +833,11 @@[m [mINDUSTRY_QUERIES: dict[str, list[str]] = {[m
     ][m
 }[m
 [m
[31m-# NEU: Recruiter-spezifische Queries für Vertriebler-Rekrutierung[m
[32m+[m[32m# NEU: Recruiter-spezifische Queries fÃ¼r Vertriebler-Rekrutierung[m
 RECRUITER_QUERIES = {[m
     'recruiter': [[m
         # Jobsuchende / Karrierewechsler[m
[31m-        'site:de Vertrieb Jobs NRW OR Düsseldorf OR Köln OR Essen',[m
[32m+[m[32m        'site:de Vertrieb Jobs NRW OR DÃ¼sseldorf OR KÃ¶ln OR Essen',[m
         'site:de Quereinsteiger Vertrieb NRW provision OR kommission',[m
         'site:de arbeitslos Vertrieb sucht stelle NRW',[m
         [m
[36m@@ -852,7 +852,7 @@[m [mRECRUITER_QUERIES = {[m
 }[m
 [m
 [m
[31m-# Fallback für "alle" Branchen – Reihenfolge[m
[32m+[m[32m# Fallback fÃ¼r "alle" Branchen â€“ Reihenfolge[m
 INDUSTRY_ORDER = ["solar","telekom","versicherung","bau","ecom","household"][m
 [m
 def build_queries([m
[36m@@ -872,7 +872,7 @@[m [mdef build_queries([m
         per_industry_limit: Queries pro Branche/Set (Default: 2)[m
     [m
     Returns:[m
[31m-        Liste von Query-Strings für diesen Run[m
[32m+[m[32m        Liste von Query-Strings fÃ¼r diesen Run[m
     """[m
     out: List[str] = [][m
     [m
[36m@@ -892,7 +892,7 @@[m [mdef build_queries([m
             log('warn', f"Branche '{selected_industry}' nicht gefunden, verwende 'all'")[m
             selected_industry = 'all'[m
     [m
[31m-    # FALL 3: 'all' = Recruiter ZUERST (höchste Priorität), dann alle Branchen[m
[32m+[m[32m    # FALL 3: 'all' = Recruiter ZUERST (hÃ¶chste PrioritÃ¤t), dann alle Branchen[m
     if selected_industry == 'all' or selected_industry is None:[m
         # Recruiter-Queries immer zuerst laden[m
         recruiter_qs = RECRUITER_QUERIES.get('recruiter', [])[m
[36m@@ -915,13 +915,13 @@[m [mdef build_queries([m
 [m
 # ---- Domain-/Pfad-Filter (erweitert) ----[m
 DENY_DOMAINS = {[m
[31m-  # Jobbörsen / Aggregatoren[m
[32m+[m[32m  # JobbÃ¶rsen / Aggregatoren[m
   #"linkedin.com","de.linkedin.com","glassdoor.com","indeed.com","stepstone.de","monster.de",[m
   #"arbeitsagentur.de","jobboerse.arbeitsagentur.de","meinestadt.de","jobrapido.com","kimeta.de",[m
   #"hays.de","randstad.de","adecco.de","xing.com","join.com","get-in-it.de",[m
   # Medien / News[m
   "tagesschau.de","wdr.de","ndr.de","spiegel.de","rp-online.de","waz.de","zeit.de","faz.net","welt.de",[m
[31m-  # Behörden / Verbände[m
[32m+[m[32m  # BehÃ¶rden / VerbÃ¤nde[m
   "bund.de","nrw.de","land.nrw","finanzverwaltung.nrw.de","bghw.de","justiz.nrw.de",[m
   # Sonstiges ungeeignet[m
   "dzbank.de","miele.de","airchina.de","gehalt.de","salesjob.de","regiomanager.de","kununu.com",[m
[36m@@ -933,7 +933,7 @@[m [mDENY_DOMAINS = {[m
 [m
 ALLOW_PATH_HINTS = ([m
   "kontakt","impressum","karriere","jobs","stellen","bewerben","team","ansprechpartner",[m
[31m-  "callcenter","telesales","outbound","vertrieb","verkauf","sales","d2d","door-to-door","haustuer","haustür"[m
[32m+[m[32m  "callcenter","telesales","outbound","vertrieb","verkauf","sales","d2d","door-to-door","haustuer","haustÃ¼r"[m
 )[m
 [m
 NEG_PATH_HINTS = ([m
[36m@@ -973,7 +973,7 @@[m [mdef _normalize_for_dedupe(u: str) -> str:[m
     try:[m
         pu = urllib.parse.urlparse(u)[m
 [m
[31m-        # Query normalisieren – Tracking & Paginierung raus[m
[32m+[m[32m        # Query normalisieren â€“ Tracking & Paginierung raus[m
         q = urllib.parse.parse_qsl(pu.query, keep_blank_values=False)[m
         q = [[m
             (k, v) for (k, v) in q[m
[36m@@ -1000,20 +1000,20 @@[m [mimport re, urllib.parse[m
 [m
 def prioritize_urls(urls: List[str]) -> List[str]:[m
     """[m
[31m-    Priorisiert typische Kontaktseiten deutlich höher als Karriere/Jobs/Datenschutz.[m
[32m+[m[32m    Priorisiert typische Kontaktseiten deutlich hÃ¶her als Karriere/Jobs/Datenschutz.[m
     - Additives Scoring (nicht nur erstes Pattern)[m
     - Starke Upvotes: /kontakt, /impressum[m
     - Downvotes: /karriere, /jobs, /stellen, /datenschutz, /privacy, /agb[m
[31m-    - Leichte Bevorzugung kurzer/oberflächlicher Pfade; Abwertung bei Paginierung/Fragmenten[m
[32m+[m[32m    - Leichte Bevorzugung kurzer/oberflÃ¤chlicher Pfade; Abwertung bei Paginierung/Fragmenten[m
     """[m
[31m-    # --- POSITIVE & NEGATIVE Schlüsselwörter ---[m
[32m+[m[32m    # --- POSITIVE & NEGATIVE SchlÃ¼sselwÃ¶rter ---[m
     # Hinweis: additive Bewertung; ein Pfad kann mehrere Treffer bekommen.[m
     PRIORITY_PATTERNS = [[m
         (r'/kontakt(?:/|$)',                    +40),[m
         (r'/kontaktformular(?:/|$)',            +32),[m
         (r'/impressum(?:/|$)',                  +35),[m
         (r'/team(?:/|$)',                       +12),[m
[31m-        (r'/ueber-uns|/über-uns|/unternehmen',  +10),[m
[32m+[m[32m        (r'/ueber-uns|/Ã¼ber-uns|/unternehmen',  +10),[m
         # NEU: Jobseeker-Signale boosten[m
         (r'/karriere(?:/|$)',                   +18),[m
         (r'/jobs?(?:/|$)',                      +18),[m
[36m@@ -1045,17 +1045,17 @@[m [mdef prioritize_urls(urls: List[str]) -> List[str]:[m
             if re.search(pat, low, re.I):[m
                 s += pts[m
 [m
[31m-        # Query-Hints (selten, aber wenn vorhanden → leicht positiv)[m
[32m+[m[32m        # Query-Hints (selten, aber wenn vorhanden â†’ leicht positiv)[m
         if re.search(r'(\?|#).*(kontakt|impressum)', low, re.I):[m
             s += 12[m
 [m
[31m-        # Pfad-Länge / -Tiefe: kurze, flache Pfade bevorzugen[m
[32m+[m[32m        # Pfad-LÃ¤nge / -Tiefe: kurze, flache Pfade bevorzugen[m
         depth = max(0, path.count('/') - 1)[m
[31m-        s += max(0, 20 - len(path))           # kürzerer Pfad = besser[m
[32m+[m[32m        s += max(0, 20 - len(path))           # kÃ¼rzerer Pfad = besser[m
         s += max(0, 10 - 5*depth)             # weniger Unterverzeichnisse = besser[m
 [m
         # Rauschfilter / Paginierung / Fragmente[m
[31m-        if len(u) > 220:                      # sehr lange URLs wirken oft „Rauschen“[m
[32m+[m[32m        if len(u) > 220:                      # sehr lange URLs wirken oft â€žRauschenâ€œ[m
             s -= 40[m
         if re.search(r'(\?|&)page=\d{1,3}\b', low):[m
             s -= 25[m
[36m@@ -1082,11 +1082,11 @@[m [mdef prioritize_urls(urls: List[str]) -> List[str]:[m
 [m
 async def google_cse_search_async(q: str, max_results: int = 60, date_restrict: Optional[str] = None) -> Tuple[List[str], bool]:[m
     if not (GCS_KEYS and GCS_CXS):[m
[31m-        log("debug","Google CSE nicht konfiguriert – übersprungen"); return [], False[m
[32m+[m[32m        log("debug","Google CSE nicht konfiguriert â€“ Ã¼bersprungen"); return [], False[m
 [m
     def _preview(txt: Optional[str]) -> str:[m
         if not txt: return ""[m
[31m-        # HTML-Tags & übermäßige Whitespaces entfernen, dann hart bei 200 cutten[m
[32m+[m[32m        # HTML-Tags & Ã¼bermÃ¤ÃŸige Whitespaces entfernen, dann hart bei 200 cutten[m
         txt = re.sub(r"<[^>]+>", " ", txt)[m
         txt = re.sub(r"\s+", " ", txt).strip()[m
         return txt[:200][m
[36m@@ -1117,7 +1117,7 @@[m [masync def google_cse_search_async(q: str, max_results: int = 60, date_restrict:[m
             key_i = (key_i + 1) % max(1,len(GCS_KEYS))[m
             cx_i  = (cx_i  + 1) % max(1,len(GCS_CXS))[m
             sleep_s = 6 + int(6*_jitter())[m
[31m-            log("warn","Google 429 – rotiere Key/CX & backoff", sleep=sleep_s)[m
[32m+[m[32m            log("warn","Google 429 â€“ rotiere Key/CX & backoff", sleep=sleep_s)[m
             await asyncio.sleep(sleep_s)[m
             continue[m
 [m
[36m@@ -1153,7 +1153,7 @@[m [masync def google_cse_search_async(q: str, max_results: int = 60, date_restrict:[m
 [m
 async def bing_search_async(q: str, count: int = 30, pages:int=3) -> Tuple[List[str], bool]:[m
     if not BING_API_KEY:[m
[31m-        log("debug","Bing nicht konfiguriert – übersprungen"); return [], False[m
[32m+[m[32m        log("debug","Bing nicht konfiguriert â€“ Ã¼bersprungen"); return [], False[m
 [m
     def _preview(txt: Optional[str]) -> str:[m
         if not txt: return ""[m
[36m@@ -1201,13 +1201,13 @@[m [masync def bing_search_async(q: str, count: int = 30, pages:int=3) -> Tuple[List[[m
 [m
 EMAIL_RE   = re.compile(r'\b(?!noreply|no-reply|donotreply)[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}\b', re.I)[m
 PHONE_RE   = re.compile(r'(?:\+49|0049|0)\s?(?:\(?\d{2,5}\)?[\s\/\-]?)?\d(?:[\s\/\-]?\d){5,10}')[m
[31m-SALES_RE   = re.compile(r'\b(vertrieb|vertriebs|sales|account\s*manager|key\s*account|business\s*development|außendienst|aussendienst|handelsvertreter|telesales|call\s*center|outbound|haustür|d2d)\b', re.I)[m
[31m-LOW_PAY_HINT   = re.compile(r'\b(12[,\.]?\d{0,2}|13[,\.]?\d{0,2})\s*€\s*/?\s*h|\b(Mindestlohn|Fixum\s+ab\s+\d{1,2}\s*€)\b', re.I)[m
[32m+[m[32mSALES_RE   = re.compile(r'\b(vertrieb|vertriebs|sales|account\s*manager|key\s*account|business\s*development|auÃŸendienst|aussendienst|handelsvertreter|telesales|call\s*center|outbound|haustÃ¼r|d2d)\b', re.I)[m
[32m+[m[32mLOW_PAY_HINT   = re.compile(r'\b(12[,\.]?\d{0,2}|13[,\.]?\d{0,2})\s*â‚¬\s*/?\s*h|\b(Mindestlohn|Fixum\s+ab\s+\d{1,2}\s*â‚¬)\b', re.I)[m
 PROVISION_HINT = re.compile(r'\b(Provisionsbasis|nur\s*Provision|hohe\s*Provision(en)?|Leistungsprovision)\b', re.I)[m
[31m-D2D_HINT       = re.compile(r'\b(Door[-\s]?to[-\s]?door|Haustür|Kaltakquise|D2D)\b', re.I)[m
[32m+[m[32mD2D_HINT       = re.compile(r'\b(Door[-\s]?to[-\s]?door|HaustÃ¼r|Kaltakquise|D2D)\b', re.I)[m
 CALLCENTER_HINT= re.compile(r'\b(Call\s*Center|Telesales|Outbound|Inhouse-?Sales)\b', re.I)[m
 B2C_HINT       = re.compile(r'\b(B2C|Privatkunden|Haushalte|Endkunden)\b', re.I)[m
[31m-JOBSEEKER_RE  = re.compile(r'\b(jobsuche|stellensuche|arbeitslos|lebenslauf|bewerb(ung)?|cv|portfolio|offen\s*f(?:ür|uer)\s*neues)\b', re.I)[m
[32m+[m[32mJOBSEEKER_RE  = re.compile(r'\b(jobsuche|stellensuche|arbeitslos|lebenslauf|bewerb(ung)?|cv|portfolio|offen\s*f(?:Ã¼r|uer)\s*neues)\b', re.I)[m
 RECRUITER_RE  = re.compile(r'\b(recruit(er|ing)?|hr|human\s*resources|personalvermittlung|headhunter|wir\s*suchen|join\s*our\s*team)\b', re.I)[m
 [m
 [m
[36m@@ -1215,33 +1215,33 @@[m [mWHATSAPP_RE    = re.compile(r'(?i)\b(WhatsApp|Whats\s*App)[:\s]*\+?\d[\d \-()]{6[m
 WA_LINK_RE     = re.compile(r'(?:https?://)?(?:wa\.me/\d+|api\.whatsapp\.com/send\?phone=\d+)', re.I)[m
 WHATS_RE       = re.compile(r'(?:\+?\d{2,3}\s?)?(?:\(?0\)?\s?)?\d{2,4}[\s\-]?\d{3,}.*?(?:whatsapp|wa\.me|api\.whatsapp)', re.I)[m
 [m
[31m-CITY_RE        = re.compile(r'\b(NRW|Nordrhein[-\s]?Westfalen|Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn)\b', re.I)[m
[31m-NAME_RE        = re.compile(r'\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+){0,2})\b')[m
[31m-# --- Kontext-Fenster für Heuristiken (Sales/Jobseeker) ---[m
[32m+[m[32mCITY_RE        = re.compile(r'\b(NRW|Nordrhein[-\s]?Westfalen|DÃ¼sseldorf|KÃ¶ln|Essen|Dortmund|MÃ¶nchengladbach|Bochum|Wuppertal|Bonn)\b', re.I)[m
[32m+[m[32mNAME_RE        = re.compile(r'\b([A-ZÃ„Ã–Ãœ][a-zÃ¤Ã¶Ã¼ÃŸ]+(?:\s+[A-ZÃ„Ã–Ãœ][a-zÃ¤Ã¶Ã¼ÃŸ\-]+){0,2})\b')[m
[32m+[m[32m# --- Kontext-Fenster fÃ¼r Heuristiken (Sales/Jobseeker) ---[m
 # Sales-Fenster: erkennt Vertriebs-/Akquise-Kontext im Umfeld von Text[m
 SALES_WINDOW = re.compile([m
[31m-    r'(?is).{0,400}(vertrieb|verkauf|sales|akquise|außendienst|aussendienst|'[m
[32m+[m[32m    r'(?is).{0,400}(vertrieb|verkauf|sales|akquise|auÃŸendienst|aussendienst|'[m
     r'call\s*center|telefonverkauf|door\s*to\s*door|d2d|provision).{0,400}'[m
 )[m
 [m
 # Jobseeker-Fenster: erkennt Lebenslauf/Bewerbung/Jobsuche-Kontext[m
 JOBSEEKER_WINDOW = re.compile([m
     r'(?is).{0,400}(jobsuche|stellensuche|arbeitslos|bewerb(?:ung)?|lebenslauf|'[m
[31m-    r'cv|portfolio|offen\s*f(?:ür|uer)\s*neues|profil).{0,400}'[m
[32m+[m[32m    r'cv|portfolio|offen\s*f(?:Ã¼r|uer)\s*neues|profil).{0,400}'[m
 )[m
 [m
 [m
[31m-NEGATIVE_HINT  = re.compile(r'\b(Behörde|Amt|Universität|Karriereportal|Blog|Ratgeber|Software|SaaS|Bank|Versicherung)\b', re.I)[m
[32m+[m[32mNEGATIVE_HINT  = re.compile(r'\b(BehÃ¶rde|Amt|UniversitÃ¤t|Karriereportal|Blog|Ratgeber|Software|SaaS|Bank|Versicherung)\b', re.I)[m
 WHATSAPP_INLINE= re.compile(r'\+?\d[\d ()\-]{6,}\s*(?:WhatsApp|WA)', re.I)[m
[31m-PERSON_PREFIX  = re.compile(r'\b(Herr|Frau|Hr\.|Fr\.)\s+[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)?')[m
[32m+[m[32mPERSON_PREFIX  = re.compile(r'\b(Herr|Frau|Hr\.|Fr\.)\s+[A-ZÃ„Ã–Ãœ][a-zÃ¤Ã¶Ã¼ÃŸ\-]+(?:\s+[A-ZÃ„Ã–Ãœ][a-zÃ¤Ã¶Ã¼ÃŸ\-]+)?')[m
 JOBSEEKER_WINDOW = re.compile([m
[31m-    r'(?is).{0,400}(jobsuche|stellensuche|arbeitslos|bewerb(ung)?|lebenslauf|cv|portfolio|offen\s*f(?:ür|uer)\s*neues).{0,400}'[m
[32m+[m[32m    r'(?is).{0,400}(jobsuche|stellensuche|arbeitslos|bewerb(ung)?|lebenslauf|cv|portfolio|offen\s*f(?:Ã¼r|uer)\s*neues).{0,400}'[m
 )[m
 INDUSTRY_PATTERNS = {[m
[31m-    "energie":      r'\b(Energie|Strom|Gas|Ökostrom|Versorger|Photovoltaik|PV|Solar|Wärmepumpe)\b',[m
[32m+[m[32m    "energie":      r'\b(Energie|Strom|Gas|Ã–kostrom|Versorger|Photovoltaik|PV|Solar|WÃ¤rmepumpe)\b',[m
     "telekom":      r'\b(Telekommunikation|Telefonie|Internet|DSL|Mobilfunk|Glasfaser|Telekom)\b',[m
     "versicherung": r'\b(Versicherung(en)?|Versicherungsmakler|Bausparen|Finanzberatung|Finanzen)\b',[m
[31m-    "bau":          r'\b(Bau|Handwerk|Sanierung|Fenster|Türen|Dämm|Energieberatung)\b',[m
[32m+[m[32m    "bau":          r'\b(Bau|Handwerk|Sanierung|Fenster|TÃ¼ren|DÃ¤mm|Energieberatung)\b',[m
     "ecommerce":    r'\b(E-?Commerce|Onlineshop|Bestellhotline|Kundengewinnung)\b',[m
     "household":    r'\b(Vorwerk|Kobold|Staubsauger|Haushaltswaren)\b'[m
 }[m
[36m@@ -1255,7 +1255,7 @@[m [mINDUSTRY_HINTS = [[m
     "solar", "photovoltaik", "pv", "energie", "energieberatung", "strom", "gas",[m
     "glasfaser", "telekom", "telekommunikation", "dsl", "mobilfunk", "internet",[m
     "vorwerk", "kobold", "staubsauger", "haushaltswaren",[m
[31m-    "fenster", "türen", "tueren", "dämm", "daemm", "wärmepumpe", "waermepumpe",[m
[32m+[m[32m    "fenster", "tÃ¼ren", "tueren", "dÃ¤mm", "daemm", "wÃ¤rmepumpe", "waermepumpe",[m
     "versicherung", "versicherungen", "bausparen", "immobilien", "makler",[m
     "onlineshop", "e-commerce", "shop", "kundengewinnung"[m
 ][m
[36m@@ -1311,9 +1311,9 @@[m [mdef same_org_domain(page_url: str, email_domain: str) -> bool:[m
         return False[m
 [m
 _OBFUSCATION_PATTERNS = [[m
[31m-    (r'\s*(\[\s*at\s*\]|\(\s*at\s*\)|\{\s*at\s*\}|\s+at\s+|\s+ät\s+)\s*', '@'),[m
[32m+[m[32m    (r'\s*(\[\s*at\s*\]|\(\s*at\s*\)|\{\s*at\s*\}|\s+at\s+|\s+Ã¤t\s+)\s*', '@'),[m
     (r'\s*(\[\s*dot\s*\]|\(\s*dot\s*\)|\{\s*dot\s*\}|\s+dot\s+|\s+punkt\s*|\s*\.\s*)\s*', '.'),[m
[31m-    (r'\s*(ät|@t)\s*', '@'),   # zusätzliche Varianten[m
[32m+[m[32m    (r'\s*(Ã¤t|@t)\s*', '@'),   # zusÃ¤tzliche Varianten[m
 ][m
 [m
 def deobfuscate_text_for_emails(text: str) -> str:[m
[36m@@ -1352,7 +1352,7 @@[m [mdef normalize_email(e: str) -> str:[m
 [m
 def extract_company_name(title_text:str)->str:[m
     if not title_text: return ""[m
[31m-    m = re.split(r'[-–|•·:]', title_text)[m
[32m+[m[32m    m = re.split(r'[-â€“|â€¢Â·:]', title_text)[m
     base = m[0].strip() if m else title_text.strip()[m
     if re.search(r'\b(Job|Karriere|Kontakt|Impressum)\b', base, re.I): return ""[m
     return base[:120][m
[36m@@ -1361,7 +1361,7 @@[m [mdef detect_company_size(text:str)->str:[m
     patterns = {[m
         "klein":  r'\b(1-10|klein|Inhaber|Familienunternehmen)\b',[m
         "mittel": r'\b(11-50|50-250|Mittelstand|[1-9]\d?\s*Mitarbeiter)\b',[m
[31m-        "groß":   r'\b(250\+|Konzern|Tochtergesellschaft|international|[2-9]\d{2,}\s*Mitarbeiter)\b'[m
[32m+[m[32m        "groÃŸ":   r'\b(250\+|Konzern|Tochtergesellschaft|international|[2-9]\d{2,}\s*Mitarbeiter)\b'[m
     }[m
     for size, pat in patterns.items():[m
         if re.search(pat, text, re.I): return size[m
[36m@@ -1375,16 +1375,16 @@[m [mdef detect_industry(text:str)->str:[m
 def detect_recency(html:str)->str:[m
     if re.search(r'\b(2025|2024)\-(0[1-9]|1[0-2])\-(0[1-9]|[12]\d|3[01])\b', html): return "aktuell"[m
     if re.search(r'\b(0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2])\.(2024|2025)\b', html): return "aktuell"[m
[31m-    if re.search(r'\b(ab\s*sofort|sofort|zum\s*nächsten?\s*möglichen\s*termin)\b', html, re.I): return "sofort"[m
[32m+[m[32m    if re.search(r'\b(ab\s*sofort|sofort|zum\s*nÃ¤chsten?\s*mÃ¶glichen\s*termin)\b', html, re.I): return "sofort"[m
     return "unbekannt"[m
 [m
 def estimate_hiring_volume(text:str)->str:[m
[31m-    if re.search(r'\b(mehrere|Teams|Team-?Erweiterung|Verstärkung|wir wachsen)\b', text, re.I): return "hoch"[m
[32m+[m[32m    if re.search(r'\b(mehrere|Teams|Team-?Erweiterung|VerstÃ¤rkung|wir wachsen)\b', text, re.I): return "hoch"[m
     if len(re.findall(r'\b(Stelle|Stellen|Job)\b', text, re.I)) > 1: return "mittel"[m
     return "niedrig"[m
 [m
 def extract_locations(text:str)->str:[m
[31m-    cities = re.findall(r'\b(Düsseldorf|Köln|Essen|Dortmund|Mönchengladbach|Bochum|Wuppertal|Bonn|NRW|Nordrhein[-\s]?Westfalen)\b', text, re.I)[m
[32m+[m[32m    cities = re.findall(r'\b(DÃ¼sseldorf|KÃ¶ln|Essen|Dortmund|MÃ¶nchengladbach|Bochum|Wuppertal|Bonn|NRW|Nordrhein[-\s]?Westfalen)\b', text, re.I)[m
     out, seen=[], set()[m
     for c in cities:[m
         k=c.lower()[m
[36m@@ -1410,13 +1410,13 @@[m [mdef tags_from(text:str)->str:[m
 [m
 def opening_line(lead:dict)->str:[m
     t = (lead.get("tags","") or "")[m
[31m-    if "d2d" in t: return "D2D in NRW: tägliche Touren + überdurchschnittliche Provision, Auszahlung wöchentlich."[m
[31m-    if "callcenter" in t: return "Outbound-Leads mit hoher Abschlussquote – Provision top, Auszahlung wöchentlich."[m
[32m+[m[32m    if "d2d" in t: return "D2D in NRW: tÃ¤gliche Touren + Ã¼berdurchschnittliche Provision, Auszahlung wÃ¶chentlich."[m
[32m+[m[32m    if "callcenter" in t: return "Outbound-Leads mit hoher Abschlussquote â€“ Provision top, Auszahlung wÃ¶chentlich."[m
     return "Warme Leads, starker Provisionsplan, schnelle Auszahlung."[m
 [m
 def normalize_phone(p: str) -> str:[m
     """[m
[31m-    DE-Telefon-Normalisierung (E.164-ähnlich) mit Edge-Cases wie '(0)'.[m
[32m+[m[32m    DE-Telefon-Normalisierung (E.164-Ã¤hnlich) mit Edge-Cases wie '(0)'.[m
     Beispiele:[m
       '0211 123456'            -> '+49211123456'[m
       '+49 (0) 211 123456'     -> '+49211123456'[m
[36m@@ -1432,13 +1432,13 @@[m [mdef normalize_phone(p: str) -> str:[m
     # Erfasst (), [], {} und beliebige Whitespaces: '(0)', '( 0 )', '[0]' etc.[m
     s = re.sub(r'[\(\[\{]\s*0\s*[\)\]\}]', '0', s)[m
 [m
[31m-    # Häufige Extension-/Zusatzangaben am Ende entfernen (ext, Durchwahl, DW, Tel.)[m
[32m+[m[32m    # HÃ¤ufige Extension-/Zusatzangaben am Ende entfernen (ext, Durchwahl, DW, Tel.)[m
     s = re.sub(r'(?:durchwahl|dw|ext\.?|extension)\s*[:\-]?\s*\d+\s*$', '', s, flags=re.I)[m
 [m
[31m-    # Alle Zeichen außer Ziffern und Plus entfernen[m
[32m+[m[32m    # Alle Zeichen auÃŸer Ziffern und Plus entfernen[m
     s = re.sub(r'[^\d+]', '', s)[m
 [m
[31m-    # Internationale Präfixe vereinheitlichen[m
[32m+[m[32m    # Internationale PrÃ¤fixe vereinheitlichen[m
     s = re.sub(r'^00', '+', s)        # 0049 -> +49, 0033 -> +33, etc.[m
     s = re.sub(r'^\+049', '+49', s)   # Tippfehler-Variante absichern[m
     s = re.sub(r'^0049', '+49', s)    # (redundant, aber explizit)[m
[36m@@ -1447,7 +1447,7 @@[m [mdef normalize_phone(p: str) -> str:[m
     # Beispiele: '+490211...' -> '+49211...'[m
     s = re.sub(r'^\+490', '+49', s)[m
 [m
[31m-    # Nationale führende 0 → +49[m
[32m+[m[32m    # Nationale fÃ¼hrende 0 â†’ +49[m
     if s.startswith('0') and not s.startswith('+'):[m
         s = '+49' + s[1:][m
 [m
[36m@@ -1455,14 +1455,14 @@[m [mdef normalize_phone(p: str) -> str:[m
     if s.count('+') > 1:[m
         s = '+' + re.sub(r'\D', '', s)[m
 [m
[31m-    # Falls noch kein '+' vorhanden ist, hinzufügen (E.164-ähnlich)[m
[32m+[m[32m    # Falls noch kein '+' vorhanden ist, hinzufÃ¼gen (E.164-Ã¤hnlich)[m
     if not s.startswith('+'):[m
         s = '+' + re.sub(r'\D', '', s)[m
 [m
[31m-    # Plausibilitätscheck (Gesamtziffernzahl)[m
[32m+[m[32m    # PlausibilitÃ¤tscheck (Gesamtziffernzahl)[m
     digits = re.sub(r'\D', '', s)[m
     if len(digits) < 8 or len(digits) > 16:[m
[31m-        return s  # unbearbeitet zurückgeben, wenn außerhalb Range[m
[32m+[m[32m        return s  # unbearbeitet zurÃ¼ckgeben, wenn auÃŸerhalb Range[m
 [m
     return s[m
 [m
[36m@@ -1505,16 +1505,16 @@[m [mdef regex_extract_contacts(text: str, src_url: str):[m
     # Text absichern[m
     text = text or ""[m
 [m
[31m-    # 2× De-Obfuscation (schluckt verschachtelte Varianten wie [at](punkt), ät, {dot}, etc.)[m
[32m+[m[32m    # 2Ã— De-Obfuscation (schluckt verschachtelte Varianten wie [at](punkt), Ã¤t, {dot}, etc.)[m
     for _ in range(2):[m
         text = deobfuscate_text_for_emails(text)[m
 [m
[31m-    # Früher Sales-Check: wenn nirgends Sales-Kontext, direkt abbrechen[m
[32m+[m[32m    # FrÃ¼her Sales-Check: wenn nirgends Sales-Kontext, direkt abbrechen[m
     if not (SALES_WINDOW.search(text) or JOBSEEKER_WINDOW.search(text)):[m
         log("info", "Regex-Fallback: kein Sales/Jobseeker-Kontext", url=src_url)[m
         return [][m
 [m
[31m-    # Näheprüfung mit erweitertem Fenster (±400 Zeichen)[m
[32m+[m[32m    # NÃ¤heprÃ¼fung mit erweitertem Fenster (Â±400 Zeichen)[m
     def _sales_near(a: int, b: int) -> bool:[m
         span = text[max(0, a - 400): min(len(text), b + 400)][m
         return bool(SALES_WINDOW.search(span))[m
[36m@@ -1530,7 +1530,7 @@[m [mdef regex_extract_contacts(text: str, src_url: str):[m
         log("info", "Regex-Fallback: keine Treffer", url=src_url)[m
         return rows[m
 [m
[31m-    # E-Mails mit nächster Telefonnummer verbinden (falls vorhanden) + Name raten[m
[32m+[m[32m    # E-Mails mit nÃ¤chster Telefonnummer verbinden (falls vorhanden) + Name raten[m
     for e, es, ee in email_hits:[m
         if not _sales_near(es, ee):[m
             continue[m
[36m@@ -1551,7 +1551,7 @@[m [mdef regex_extract_contacts(text: str, src_url: str):[m
             "quelle": src_url[m
         })[m
 [m
[31m-    # Telefonnummern ergänzen, die noch nicht genutzt wurden[m
[32m+[m[32m    # Telefonnummern ergÃ¤nzen, die noch nicht genutzt wurden[m
     used_tel = set(r["telefon"] for r in rows if r.get("telefon"))[m
     for p, ps, pe in phone_hits:[m
         if not _sales_near(ps, pe):[m
[36m@@ -1677,14 +1677,14 @@[m [mdef compute_score(text: str, url: str) -> int:[m
     has_personal_email = has_email and not any(g in t for g in generic_mail_fragments)[m
     has_switch_now = any(k in t for k in [[m
         "quereinsteiger", "ab sofort", "sofort starten", "sofort start",[m
[31m-        "keine erfahrung nötig", "ohne erfahrung", "jetzt bewerben",[m
[32m+[m[32m        "keine erfahrung nÃ¶tig", "ohne erfahrung", "jetzt bewerben",[m
         "heute noch bewerben", "direkt bewerben"[m
     ])[m
     has_lowpay_or_prov = bool(PROVISION_HINT.search(t)) or any(k in t for k in [[m
         "nur provision", "provisionsbasis", "fixum + provision",[m
[31m-        "freelancer", "selbstständig", "selbststaendig", "werkvertrag"[m
[32m+[m[32m        "freelancer", "selbststÃ¤ndig", "selbststaendig", "werkvertrag"[m
     ])[m
[31m-    has_d2d = bool(D2D_HINT.search(t)) or any(k in t for k in ["door to door", "haustür", "haustuer", "kaltakquise"])[m
[32m+[m[32m    has_d2d = bool(D2D_HINT.search(t)) or any(k in t for k in ["door to door", "haustÃ¼r", "haustuer", "kaltakquise"])[m
     has_callcenter = bool(CALLCENTER_HINT.search(t))[m
     has_b2c = bool(B2C_HINT.search(t))[m
     industry_hits = sum(1 for k in INDUSTRY_HINTS if k in t)[m
[36m@@ -1785,10 +1785,10 @@[m [mdef validate_content(html: str, url: str) -> bool:[m
     lower = text.lower()[m
     login_gate = ([m
         re.search(r'\b(anmelden|login|passwort)\b', lower, re.I) and[m
[31m-        re.search(r'\b(geschützt|nur\s*für\s*mitglieder|zugang\s*verweigert|restricted)\b', lower, re.I)[m
[32m+[m[32m        re.search(r'\b(geschÃ¼tzt|nur\s*fÃ¼r\s*mitglieder|zugang\s*verweigert|restricted)\b', lower, re.I)[m
     )[m
     is_404 = any(phrase in lower for phrase in ["404", "seite nicht gefunden", "page not found", "not found"])[m
[31m-    german_core = re.search(r'\b(der|die|das|und|in|zu|für|mit|auf)\b', lower, re.I) is not None[m
[32m+[m[32m    german_core = re.search(r'\b(der|die|das|und|in|zu|fÃ¼r|mit|auf)\b', lower, re.I) is not None[m
     contact_tolerant = any(k in lower for k in ["kontakt", "impressum", "telefon", "e-mail", "email", "bewerben"])[m
     no_german = not (german_core or contact_tolerant)[m
     checks = {[m
[36m@@ -1808,7 +1808,7 @@[m [masync def process_link_async(url: str, run_id: int, *, force: bool = False) -> T[m
         log("debug", "URL bereits gesehen (skip)", url=url)[m
         return (0, [])[m
     if is_denied(url) or not path_ok(url):[m
[31m-        log("debug", "Vorprüfung blockt URL", url=url)[m
[32m+[m[32m        log("debug", "VorprÃ¼fung blockt URL", url=url)[m
         mark_url_seen(url, run_id)[m
         return (1, [])[m
     if not await robots_allowed_async(url):[m
[36m@@ -1821,14 +1821,14 @@[m [masync def process_link_async(url: str, run_id: int, *, force: bool = False) -> T[m
     if not resp:[m
         st = _LAST_STATUS.get(url, -1)[m
         if st in (429, 403, -1):[m
[31m-            log("warn", "Kein Content – Retry später (nicht markiert)", url=url, status=st)[m
[32m+[m[32m            log("warn", "Kein Content â€“ Retry spÃ¤ter (nicht markiert)", url=url, status=st)[m
             return (1, [])[m
         mark_url_seen(url, run_id)[m
         return (1, [])[m
 [m
     ct = (resp.headers.get("Content-Type", "") or "").lower()[m
     if "application/pdf" in ct and not CFG.allow_pdf:[m
[31m-        log("info", "PDF übersprungen (ALLOW_PDF=0)", url=url)[m
[32m+[m[32m        log("info", "PDF Ã¼bersprungen (ALLOW_PDF=0)", url=url)[m
         mark_url_seen(url, run_id)[m
         return (1, [])[m
 [m
[36m@@ -1882,12 +1882,12 @@[m [masync def process_link_async(url: str, run_id: int, *, force: bool = False) -> T[m
     if soup is None:[m
         soup = BeautifulSoup(html, "html.parser")[m
     [m
[31m-        # >>> FAST-PATH: Kontakt/Impressum/Team/Ansprechpartner – Anker-Scan & Early-Return[m
[32m+[m[32m        # >>> FAST-PATH: Kontakt/Impressum/Team/Ansprechpartner â€“ Anker-Scan & Early-Return[m
     lu = url.lower()[m
     if any(key in lu for key in ("/kontakt", "/impressum", "/team", "/ansprechpartner")):[m
         fast_items = _anchor_contacts_fast(soup, url)[m
         if fast_items:[m
[31m-            # Minimaler Score: Kontaktseiten haben oft wenig Sales-Text -> künstlich anheben[m
[32m+[m[32m            # Minimaler Score: Kontaktseiten haben oft wenig Sales-Text -> kÃ¼nstlich anheben[m
             base_score = compute_score(text, url)[m
             base_score = max(CFG.min_score, base_score) + 20  # Kontakt-Bonus[m
 [m
[36m@@ -1948,7 +1948,7 @@[m [masync def process_link_async(url: str, run_id: int, *, force: bool = False) -> T[m
 [m
             out: List[Dict[str, Any]] = [][m
             for r in fast_items:[m
[31m-                # Evtl. E-Mail-Qualität prüfen + Boost[m
[32m+[m[32m                # Evtl. E-Mail-QualitÃ¤t prÃ¼fen + Boost[m
                 boost = 0[m
                 if r.get("email"):[m
                     boost_label = _mail_boost_and_label(r.get("email"))[m
[36m@@ -1959,7 +1959,7 @@[m [masync def process_link_async(url: str, run_id: int, *, force: bool = False) -> T[m
                 tel_boost, extras = _tel_wa_boost(r, text, html)[m
                 boost += tel_boost[m
 [m
[31m-                # Tags lokal ergänzen[m
[32m+[m[32m                # Tags lokal ergÃ¤nzen[m
                 tag_local = (base_tags or "").strip()[m
                 if extras.get("tags_add_whatsapp"):[m
                     parts = [p for p in tag_local.split(",") if p][m
[36m@@ -1997,7 +1997,7 @@[m [masync def process_link_async(url: str, run_id: int, *, force: bool = False) -> T[m
             return (1, out)[m
 [m
 [m
[31m-    # Sales-Kontext prüfen[m
[32m+[m[32m    # Sales-Kontext prÃ¼fen[m
     if not (SALES_RE.search(text) or JOBSEEKER_WINDOW.search(text)):[m
         log("debug", "Kein Ver