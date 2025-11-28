Kritische Stellen:
- http_get_async: HEAD-Preflight, HTTP/2→1.1, SSL-Fallback, 429/403 Handling
- process_link_async: Content-Validierung, Regex/LLM-Extraktion, Scoring
- _Rate: Concurrency global/pro Host
- DB: UNIQUE per E-Mail/Telefon (partielle Indizes), Migrations
- Export: CSV/XLSX Append, Spalten 'whatsapp_link', 'phone_type'
