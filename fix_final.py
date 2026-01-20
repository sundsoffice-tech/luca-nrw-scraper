with open('scriptname.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open('scriptname_backup_final.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Backup erstellt")

# Ersetze alle _router Aufrufe mit direkten Imports
replacements = [
    ('return _is_query_done_router(q)', 
     '''from luca_scraper.db_router import is_query_done as _is_query_done_fn
    return _is_query_done_fn(q)'''),
    
    ('_mark_query_done_router(q, run_id)', 
     '''from luca_scraper.db_router import mark_query_done as _mark_query_done_fn
    _mark_query_done_fn(q, run_id)'''),
    
    ('return _is_url_seen_router(url)', 
     '''from luca_scraper.db_router import is_url_seen as _is_url_seen_fn
    return _is_url_seen_fn(url)'''),
    
    ('_mark_url_seen_router(url, run_id)', 
     '''from luca_scraper. db_router import mark_url_seen as _mark_url_seen_fn
    _mark_url_seen_fn(url, run_id)'''),
    
    ('return _upsert_lead_router(data)', 
     '''from luca_scraper.db_router import upsert_lead as _upsert_lead_fn
    return _upsert_lead_fn(data)'''),
    
    ('return _lead_exists_router(', 
     '''from luca_scraper.db_router import lead_exists as _lead_exists_fn
    return _lead_exists_fn('''),
    
    ('return _get_lead_count_router()', 
     '''from luca_scraper.db_router import get_lead_count as _get_lead_count_fn
    return _get_lead_count_fn()'''),
    
    ('return _start_scraper_run_router()', 
     '''from luca_scraper.db_router import start_scraper_run as _start_scraper_run_fn
    return _start_scraper_run_fn()'''),
    
    ('_finish_scraper_run_router(', 
     '''from luca_scraper.db_router import finish_scraper_run as _finish_scraper_run_fn
    _finish_scraper_run_fn('''),
]

for old, new in replacements: 
    if old in content:
        content = content.replace(old, new)
        print(f"Ersetzt: {old[: 40]}...")
    else:
        print(f"Nicht gefunden: {old[: 40]}...")

with open('scriptname.py', 'w', encoding='utf-8') as f:
    f.write(content)

import ast
try:
    ast. parse(content)
    print("\nSyntax: OK!")
except SyntaxError as e: 
    print(f"\nSyntax Error: {e}")

print("\n=== FIX ANGEWENDET ===")
