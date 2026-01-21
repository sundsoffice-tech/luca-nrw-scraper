import os
import re
from collections import defaultdict

print('=' * 70)
print('    UI BUTTON ANALYSE - FEHLENDE FUNKTIONEN')
print('=' * 70)

onclick_functions = set()
html_buttons = defaultdict(list)

for root, dirs, files in os.walk('telis_recruitment'):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', 'migrations', '. git']]
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                matches = re.findall(r'onclick="([^"]+)"', content)
                for m in matches: 
                    func_match = re. match(r'(\w+)\s*\(', m)
                    if func_match: 
                        func_name = func_match.group(1)
                        onclick_functions.add(func_name)
                        html_buttons[func_name].append(filepath.replace('telis_recruitment\\', ''))
            except: 
                pass

print(f'\n[1] Gefundene onclick Funktionen: {len(onclick_functions)}')

defined_functions = set()

for root, dirs, files in os.walk('telis_recruitment'):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules']]
    for file in files: 
        if file.endswith('. js') or file.endswith('. html'):
            filepath = os. path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                patterns = [
                    r'function\s+(\w+)\s*\(',
                    r'async\s+function\s+(\w+)\s*\(',
                ]
                for pattern in patterns: 
                    for match in re.finditer(pattern, content):
                        defined_functions.add(match.group(1))
            except:
                pass

print(f'[2] Definierte JS Funktionen: {len(defined_functions)}')

browser_funcs = {'fetch', 'alert', 'confirm', 'prompt', 'open', 'close', 'print', 
                 'event', 'window', 'document', 'console', 'history', 'location',
                 'this', 'JSON', 'Array', 'Object', 'String', 'Number', 'Boolean'}
missing = onclick_functions - defined_functions - browser_funcs

print(f'\n' + '=' * 70)
print(f'[3] FEHLENDE FUNKTIONEN:  {len(missing)}')
print('=' * 70)

if missing:
    for func in sorted(missing):
        locations = html_buttons.get(func, [])[:2]
        print(f'\n  [FEHLT] {func}()')
        for loc in locations: 
            print(f'          -> {loc}')
else:
    print('\n  Alle onclick Funktionen sind definiert!')

print(f'\n' + '=' * 70)
print('[4] FLASK UI ROUTES CHECK')
print('=' * 70)

try:
    with open('scriptname.py', 'r', encoding='utf-8') as f:
        scraper_content = f.read()
    flask_routes = re.findall(r"@app\.route\(['\"](/[^'\"]*)['\"]", scraper_content)
    flask_onclick = re.findall(r"fetch\(['\"](/[^'\"]+)['\"]", scraper_content)
    print(f'\nFlask Routes:  {flask_routes if flask_routes else "KEINE"}')
    print(f'onclick fetch: {flask_onclick}')
    missing_routes = set(flask_onclick) - set(flask_routes)
    if missing_routes:
        print(f'\n  [FEHLT] Routes: ')
        for route in missing_routes:
            print(f'          -> {route}')
except Exception as e:
    print(f'  Fehler: {e}')

print(f'\n' + '=' * 70)
print('[5] KRITISCHE BUTTONS CHECK')
print('=' * 70)

critical = {
    'saveFlow': 'Flow Builder - Speichern',
    'addStep': 'Flow Builder - Schritt hinzufuegen',
    'deleteStep': 'Flow Builder - Schritt loeschen',
    'saveTemplate': 'Email Template - Speichern',
    'sendTestEmail': 'Email - Test senden',
    'saveContent': 'Page Builder - Speichern',
    'publishPage': 'Page Builder - Veroeffentlichen',
    'exportReport': 'Reports - Export',
    'loadNextLead': 'Phone - Naechster Lead',
    'logCall': 'Phone - Anruf loggen',
    'batchUpdateStatus': 'Leads - Status aendern',
    'batchDelete':  'Leads - Loeschen',
    'showRunDetails': 'Scraper - Run Details',
    'buildProject':  'Pages - Projekt bauen',
    'exportProject': 'Pages - Projekt exportieren',
}

for func, desc in critical.items():
    status = 'OK' if func in defined_functions else 'FEHLT'
    mark = '  ' if status == 'OK' else '[! ]'
    print(f'{mark} {func}(): {status} - {desc}')

print(f'\n' + '=' * 70)
