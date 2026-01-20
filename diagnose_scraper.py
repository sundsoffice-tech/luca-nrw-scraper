import sys
import traceback

print("=" * 60)
print("LUCA SCRAPER - UMFASSENDE DIAGNOSE")
print("=" * 60)

# ============================================
# 1. PYTHON & ENVIRONMENT
# ============================================
print("\n[1] PYTHON ENVIRONMENT")
print(f"    Python Version: {sys.version}")
print(f"    Python Path: {sys.executable}")
print(f"    Working Dir: {__import__('os').getcwd()}")

# ============================================
# 2. LUCA_SCRAPER MODULE TESTS
# ============================================
print("\n[2] LUCA_SCRAPER MODULE IMPORTS")

modules_to_test = [
    ("luca_scraper", None),
    ("luca_scraper.config", ["DATABASE_BACKEND"]),
    ("luca_scraper.repository", ["start_scraper_run_sqlite", "finish_scraper_run_sqlite"]),
    ("luca_scraper.db_router", ["start_scraper_run", "finish_scraper_run", "upsert_lead"]),
    ("luca_scraper.database", None),
    ("luca_scraper.search", ["build_queries"]),
]

for module_name, attrs in modules_to_test: 
    try:
        module = __import__(module_name, fromlist=attrs or [])
        status = "OK"
        if attrs:
            missing = [a for a in attrs if not hasattr(module, a)]
            if missing:
                status = f"PARTIAL - missing:  {missing}"
        print(f"    {module_name}: {status}")
    except Exception as e:
        print(f"    {module_name}:  FAILED - {type(e).__name__}: {e}")

# ============================================
# 3. DATABASE BACKEND CONFIG
# ============================================
print("\n[3] DATABASE CONFIGURATION")
try:
    from luca_scraper.config import DATABASE_BACKEND
    print(f"    DATABASE_BACKEND:  {DATABASE_BACKEND}")
    
    from luca_scraper.db_router import get_backend_info
    info = get_backend_info()
    print(f"    Active Backend: {info}")
except Exception as e:
    print(f"    ERROR: {e}")

# ============================================
# 4. DATABASE CONNECTION TEST
# ============================================
print("\n[4] DATABASE CONNECTION TEST")
try:
    from luca_scraper.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"    Connection:  OK")
    print(f"    Tables found: {len(tables)}")
    print(f"    Tables: {tables[: 10]}{'...' if len(tables) > 10 else ''}")
    conn.close()
except Exception as e:
    print(f"    ERROR: {e}")

# ============================================
# 5. SCRAPER RUN FUNCTIONS TEST
# ============================================
print("\n[5] SCRAPER RUN FUNCTIONS TEST")
try:
    from luca_scraper.db_router import start_scraper_run, finish_scraper_run
    
    # Test start_scraper_run
    run_id = start_scraper_run()
    print(f"    start_scraper_run(): OK - Run ID: {run_id}")
    
    # Test finish_scraper_run
    finish_scraper_run(run_id, links_checked=0, leads_new=0, status="test")
    print(f"    finish_scraper_run(): OK")
except Exception as e:
    print(f"    ERROR: {e}")
    traceback.print_exc()

# ============================================
# 6. SCRIPTNAME. PY IMPORT TEST
# ============================================
print("\n[6] SCRIPTNAME.PY IMPORT TEST")
print("    Attempting to import scriptname.py...")

try:
    # Simuliere den Import wie in scriptname.py
    from luca_scraper.db_router import (
        upsert_lead,
        lead_exists,
        get_lead_count,
        is_url_seen,
        mark_url_seen,
        is_query_done,
        mark_query_done,
        start_scraper_run,
        finish_scraper_run,
    )
    print("    All db_router imports:  OK")
    print(f"    start_scraper_run = {start_scraper_run}")
except ImportError as e:
    print(f"    IMPORT ERROR: {e}")
    traceback.print_exc()

# ============================================
# 7. FULL SCRIPTNAME.PY LOAD TEST
# ============================================
print("\n[7] SCRIPTNAME.PY FULL LOAD TEST")
print("    This may take a moment...")

try:
    # Versuche scriptname.py zu importieren
    import importlib.util
    spec = importlib.util.spec_from_file_location("scriptname", "scriptname.py")
    if spec and spec.loader:
        print("    File found, attempting to load...")
        # Nur laden, nicht ausführen
        module = importlib.util.module_from_spec(spec)
        sys.modules["scriptname"] = module
        spec.loader.exec_module(module)
        print("    scriptname.py: LOADED OK")
        
        # Prüfe ob die kritische Funktion existiert
        if hasattr(module, '_start_scraper_run_router'):
            print(f"    _start_scraper_run_router:  EXISTS")
        else:
            print(f"    _start_scraper_run_router: NOT FOUND!")
            # Suche nach ähnlichen Namen
            similar = [n for n in dir(module) if 'scraper' in n.lower() and 'run' in n.lower()]
            print(f"    Similar names found:  {similar}")
except Exception as e:
    print(f"    ERROR during load: {type(e).__name__}: {e}")
    traceback.print_exc()

# ============================================
# 8. CHECK FOR IMPORT ERRORS IN SCRIPTNAME.PY
# ============================================
print("\n[8] SCRIPTNAME.PY SYNTAX & IMPORT CHECK")
try:
    with open("scriptname.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Compile check
    compile(content, "scriptname.py", "exec")
    print("    Syntax:  OK")
    
    # Check for the problematic import
    if "from luca_scraper.db_router import" in content:
        print("    db_router import statement:  FOUND")
        
        # Extract the import block
        import re
        match = re.search(r'from luca_scraper\.db_router import \(([\s\S]*?)\)', content)
        if match:
            imports = match.group(1)
            print(f"    Imported items: {[i.strip().split(' as ')[0] for i in imports.split(',') if i.strip()]}")
    
    # Check if _start_scraper_run_router is used
    count = content.count("_start_scraper_run_router")
    print(f"    _start_scraper_run_router usage count: {count}")
    
except Exception as e:
    print(f"    ERROR: {e}")

# ============================================
# 9. ENVIRONMENT VARIABLES
# ============================================
print("\n[9] RELEVANT ENVIRONMENT VARIABLES")
import os
env_vars = ["DATABASE_BACKEND", "DJANGO_SETTINGS_MODULE", "PYTHONPATH", "LUCA_DB_PATH"]
for var in env_vars: 
    value = os.environ.get(var, "NOT SET")
    print(f"    {var}: {value}")

# ============================================
# 10. SUMMARY
# ============================================
print("\n" + "=" * 60)
print("DIAGNOSE ABGESCHLOSSEN")
print("=" * 60)
