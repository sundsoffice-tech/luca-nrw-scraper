with open('scriptname.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Fixe die 2 verbleibenden _router Aufrufe ===")

# Zeile 1732: seen = _is_url_seen_router(url)
line_1732 = lines[1731]
if '_is_url_seen_router' in line_1732:
    indent = len(line_1732) - len(line_1732.lstrip())
    spaces = ' ' * indent
    lines[1731] = f'{spaces}from luca_scraper.db_router import is_url_seen as _is_url_seen_fn\n'
    lines. insert(1732, f'{spaces}seen = _is_url_seen_fn(url)\n')
    print("[OK] Zeile 1732 gefixt:  _is_url_seen_router -> direkter Import")

# Zeile 2272: lead_id, created = _upsert_lead_router(r)
# Nach dem Insert ist es jetzt Zeile 2273
line_2273 = lines[2272]
if '_upsert_lead_router' in line_2273:
    indent = len(line_2273) - len(line_2273.lstrip())
    spaces = ' ' * indent
    lines[2272] = f'{spaces}from luca_scraper.db_router import upsert_lead as _upsert_lead_fn\n'
    lines.insert(2273, f'{spaces}lead_id, created = _upsert_lead_fn(r)\n')
    print("[OK] Zeile 2272 gefixt: _upsert_lead_router -> direkter Import")

# Speichern
with open('scriptname.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Syntax check
content = ''.join(lines)
import ast
try:
    ast.parse(content)
    print("\nSyntax:  OK!")
except SyntaxError as e:
    print(f"\nSyntax Error: {e}")

# Pruefe ob noch _router Aufrufe da sind
import re
remaining = re.findall(r'_\w+_router\(', content)
print(f"\nVerbleibende _router Aufrufe: {len(remaining)}")
