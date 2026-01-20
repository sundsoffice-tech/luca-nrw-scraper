with open('scriptname.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Fixe die 2 verbleibenden _router Aufrufe ===")

changes_made = 0

for i, line in enumerate(lines):
    # Fix 1: _is_url_seen_router
    if '_is_url_seen_router(url)' in line and 'import' not in line:
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        lines[i] = f'{spaces}from luca_scraper.db_router import is_url_seen as _url_seen_fn; seen = _url_seen_fn(url)\n'
        print(f"[OK] Zeile {i+1}: _is_url_seen_router gefixt")
        changes_made += 1
    
    # Fix 2: _upsert_lead_router
    if '_upsert_lead_router(' in line and 'import' not in line:
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        # Ersetze nur den Funktionsnamen
        new_line = line.replace('_upsert_lead_router(', '_upsert_fn(')
        # Fuege Import davor ein
        import_line = f'{spaces}from luca_scraper.db_router import upsert_lead as _upsert_fn\n'
        lines[i] = import_line + new_line
        print(f"[OK] Zeile {i+1}: _upsert_lead_router gefixt")
        changes_made += 1

print(f"\n{changes_made} Aenderungen vorgenommen")

# Speichern
with open('scriptname. py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Syntax check
content = ''.join(lines)
import ast
try:
    ast.parse(content)
    print("Syntax:  OK!")
except SyntaxError as e:
    print(f"Syntax Error: {e}")

# Pruefe verbleibende _router Aufrufe
import re
remaining = re.findall(r'_\w+_router\(', content)
if remaining:
    print(f"\nNoch {len(remaining)} _router Aufrufe:")
    for r in remaining: 
        print(f"  - {r}")
else:
    print("\nAlle _router Aufrufe ersetzt!")
