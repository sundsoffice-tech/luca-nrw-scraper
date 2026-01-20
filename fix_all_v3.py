with open('scriptname.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open('scriptname_backup_v3.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("=== Ersetze ALLE _router Aufrufe ===")

# Alle Ersetzungen - diesmal mit dem EXAKTEN Text aus der Datei
replacements = [
    # url_seen Funktion (Zeile 1732)
    ('seen = _is_url_seen_router(url)', 
     '''from luca_scraper.db_router import is_url_seen as _is_url_seen_fn
        seen = _is_url_seen_fn(url)'''),
    
    # mark_url_seen Aufrufe
    ('_mark_url_seen_router(url', 
     '''from luca_scraper.db_router import mark_url_seen as _mark_url_seen_fn
        _mark_url_seen_fn(url'''),
    
    # is_query_done (bereits teilweise gefixt, aber sicherstellen)
    ('return _is_query_done_router(q)', 
     '''from luca_scraper.db_router import is_query_done as _is_query_done_fn
    return _is_query_done_fn(q)'''),
    
    # mark_query_done
    ('_mark_query_done_router(q, run_id)', 
     '''from luca_scraper.db_router import mark_query_done as _mark_query_done_fn
    _mark_query_done_fn(q, run_id)'''),
    
    # upsert_lead
    ('return _upsert_lead_router(data)', 
     '''from luca_scraper.db_router import upsert_lead as _upsert_lead_fn
    return _upsert_lead_fn(data)'''),
    
    # lead_exists
    ('return _lead_exists_router(email', 
     '''from luca_scraper.db_router import lead_exists as _lead_exists_fn
    return _lead_exists_fn(email'''),
    
    # get_lead_count
    ('return _get_lead_count_router()', 
     '''from luca_scraper.db_router import get_lead_count as _get_lead_count_fn
    return _get_lead_count_fn()'''),
    
    # start_scraper_run
    ('return _start_scraper_run_router()', 
     '''from luca_scraper.db_router import start_scraper_run as _start_fn
    return _start_fn()'''),
    
    # finish_scraper_run
    ('_finish_scraper_run_router(run_id', 
     '''from luca_scraper.db_router import finish_scraper_run as _finish_fn
    _finish_fn(run_id'''),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f"[OK] Ersetzt: {old[: 50]}...")
    else:
        print(f"[--] Nicht gefunden: {old[:50]}...")

# Speichern
with open('scriptname. py', 'w', encoding='utf-8') as f:
    f.write(content)

# Syntax check
import ast
try:
    ast.parse(content)
    print(f"\nSyntax:  OK!  ({count} Ersetzungen)")
except SyntaxError as e:
    print(f"\nSyntax Error: {e}")

# Zeige verbleibende _router Aufrufe
import re
remaining = re.findall(r'_\w+_router\([^)]*\)', content)
if remaining:
    print(f"\nWARNUNG: Noch {len(remaining)} _router Aufrufe gefunden:")
    for r in remaining[: 5]: 
        print(f"  - {r}")
else:
    print("\nAlle _router Aufrufe ersetzt!")
