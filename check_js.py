import re
import os

print("=" * 60)
print("    JS EINBINDUNG ANALYSE")
print("=" * 60)

files_to_check = [
    ("telis_recruitment/templates/crm/leads.html", "leads.js"),
    ("telis_recruitment/email_templates/templates/email_templates/flow_builder.html", "flow-builder. js"),
    ("telis_recruitment/templates/scraper_control/dashboard.html", "scraper-control.js"),
]

for html_path, js_name in files_to_check: 
    html_path = html_path.replace("/", os.sep)
    print(f"\n{html_path}:")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        if js_name in content:
            print(f"  [OK] {js_name} eingebunden")
        else:
            print(f"  [FEHLT] {js_name} NICHT eingebunden!")
        
        # Find static includes
        static = re.findall(r"\{% static ['\"]([^'\"]+)['\"] %\}", content)
        if static:
            print(f"  Static includes:")
            for s in static[: 10]:
                print(f"    - {s}")
        else:
            print("  Keine {% static %} includes gefunden")
    else:
        print(f"  [! ] Datei nicht gefunden")

print("\n" + "=" * 60)
print("    FUNKTIONEN IN JS DATEIEN")
print("=" * 60)

js_files = [
    "telis_recruitment/static/js/leads.js",
    "telis_recruitment/static/js/flow-builder.js",
    "telis_recruitment/static/js/scraper-control.js",
    "telis_recruitment/static/js/dashboard.js",
]

for js_path in js_files: 
    js_path = js_path.replace("/", os.sep)
    print(f"\n{os.path.basename(js_path)}:")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        funcs = re.findall(r"function\s+(\w+)\s*\(", content)
        async_funcs = re. findall(r"async\s+function\s+(\w+)\s*\(", content)
        all_funcs = list(set(funcs + async_funcs))
        if all_funcs:
            print(f"  {len(all_funcs)} Funktionen: {', '.join(all_funcs[: 15])}")
        else:
            print("  Keine Funktionen gefunden")
    else:
        print(f"  [!] Datei nicht gefunden")

print("\n" + "=" * 60)
print("    WAS FEHLT IN DEN TEMPLATES?")
print("=" * 60)

# Check leads.html vs leads.js
leads_html = "telis_recruitment/templates/crm/leads. html". replace("/", os.sep)
leads_js = "telis_recruitment/static/js/leads. js".replace("/", os.sep)

if os.path.exists(leads_html) and os.path.exists(leads_js):
    with open(leads_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    with open(leads_js, "r", encoding="utf-8") as f:
        js_content = f.read()
    
    # Functions called in HTML
    html_funcs = set(re.findall(r"onclick=\"(\w+)\(", html_content))
    # Functions defined in JS
    js_funcs = set(re.findall(r"function\s+(\w+)\s*\(", js_content))
    js_funcs. update(re.findall(r"async\s+function\s+(\w+)\s*\(", js_content))
    
    print(f"\nleads.html onclick aufrufe: {html_funcs}")
    print(f"leads.js definiert: {js_funcs}")
    
    missing = html_funcs - js_funcs
    if missing:
        print(f"\n[FEHLT] Diese Funktionen fehlen in leads. js: {missing}")
    
    found = html_funcs & js_funcs
    if found:
        print(f"[OK] Diese sind abgedeckt: {found}")

print("\n" + "=" * 60)
