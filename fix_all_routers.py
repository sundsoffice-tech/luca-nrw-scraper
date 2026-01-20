import re

with open('scriptname.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open('scriptname_full_backup.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Backup erstellt:  scriptname_full_backup.py")

# Liste aller Router-Funktionen die ersetzt werden muessen
replacements = [
    ('_start_scraper_run_router()', 'start_scraper_run()'),
    ('_finish_scraper_run_router(', 'finish_scraper_run('),
    ('_is_query_done_router(', 'is_query_done_direct('),
    ('_mark_query_done_router(', 'mark_query_done_direct('),
    ('_is_url_seen_router(', 'is_url_seen_direct('),
    ('_mark_url_seen_router(', 'mark_url_seen_direct('),
    ('_upsert_lead_router(', 'upsert_lead_direct('),
    ('_lead_exists_router(', 'lead_exists_direct('),
    ('_get_lead_count_router(', 'get_lead_count_direct('),
]

# Fuege Helper-Funktionen am Anfang ein (nach den imports)
helper_functions = '''
# === AUTO-GENERATED ROUTER HELPERS ===
def start_scraper_run():
    from luca_scraper.db_router import start_scraper_run as _fn
    return _fn()

def finish_scraper_run(*args, **kwargs):
    from luca_scraper.db_router import finish_scraper_run as _fn
    return _fn(*args, **kwargs)

def is_query_done_direct(q):
    from luca_scraper.db_router import is_query_done as _fn
    return _fn(q)

def mark_query_done_direct(q, run_id=None):
    from luca_scraper.db_router import mark_query_done as _fn
    return _fn(q, run_id)

def is_url_seen_direct(url):
    from luca_scraper. db_router import is_url_seen as _fn
    return _fn(url)

def mark_url_seen_direct(url, run_id=None):
    from luca_scraper.db_router import mark_url_seen as _fn
    return _fn(url, run_id)

def upsert_lead_direct(data):
    from luca_scraper.db_router import upsert_lead as _fn
    return _fn(data)

def lead_exists_direct(email=None, telefon=None):
    from luca_scraper.db_router import lead_exists as _fn
    return _fn(email, telefon)

def get_lead_count_direct():
    from luca_scraper.db_router import get_lead_count as _fn
    return _fn()
# === END AUTO-GENERATED ROUTER HELPERS ===

'''

# Ersetze die Router-Aufrufe
for old, new in replacements:
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        print(f"Ersetzt:  {old} -> {new} ({count}x)")

# Finde eine gute Stelle fuer die Helper-Funktionen
# Nach "# === Phase" oder nach den ersten Funktionsdefinitionen
insert_marker = "def _normalize_cx"
if insert_marker in content:
    content = content.replace(insert_marker, helper_functions + insert_marker)
    print(f"Helper-Funktionen eingefuegt vor '{insert_marker}'")
else:
    # Alternative: Nach dem grossen try-except Block
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'except ImportError' in line and i > 200: 
            # Nach dem except Block einfuegen
            for j in range(i, min(i+10, len(lines))):
                if lines[j]. strip() == '' or lines[j].strip().startswith('#'):
                    lines. insert(j+1, helper_functions)
                    print(f"Helper-Funktionen eingefuegt bei Zeile {j+1}")
                    break
            break
    content = '\n'.join(lines)

# Speichern
with open('scriptname. py', 'w', encoding='utf-8') as f:
    f.write(content)

# Syntax Check
import ast
try:
    ast.parse(content)
    print("\nSyntax:  OK!")
except SyntaxError as e:
    print(f"\nSyntax Error: {e}")

print("\nFix abgeschlossen!")
