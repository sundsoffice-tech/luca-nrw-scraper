import re

# Lese scriptname.py
with open('scriptname.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Suche nach der Stelle nach dem db_router Import
fix_code = '''
# === FIX:  Ensure db_router imports are available ===
try:
    _start_scraper_run_router
except NameError:
    from luca_scraper.db_router import start_scraper_run as _start_scraper_run_router
    print("[WARN] _start_scraper_run_router was not imported, re-importing...")

try:
    _finish_scraper_run_router
except NameError:
    from luca_scraper.db_router import finish_scraper_run as _finish_scraper_run_router
    print("[WARN] _finish_scraper_run_router was not imported, re-importing...")
# === END FIX ===
'''

# Finde die Stelle nach "finish_scraper_run as _finish_scraper_run_router"
pattern = r'(finish_scraper_run as _finish_scraper_run_router,\s*\))'
if re.search(pattern, content):
    content = re.sub(pattern, r'\1\n' + fix_code, content, count=1)
    
    with open('scriptname.py. backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open('scriptname.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("FIX APPLIED!  Backup saved as scriptname.py.backup")
else:
    print("Pattern not found - checking...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '_start_scraper_run_router' in line:
            print(f"  Line {i+1}: {line[: 80]}")
