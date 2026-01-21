import re
import os

print("=" * 60)
print("    DETAILLIERTE PROBLEM-ANALYSE")
print("=" * 60)

# 1. Check scraper-control.js - warum leer?
print("\n[1] SCRAPER-CONTROL.JS INHALT:")
sc_path = "telis_recruitment/static/js/scraper-control. js". replace("/", os.sep)
if os.path.exists(sc_path):
    with open(sc_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"  Dateigroesse: {len(content)} Zeichen")
    print(f"  Erste 500 Zeichen:\n{content[:500]}")
else:
    print("  DATEI NICHT GEFUNDEN!")

# 2. Was braucht scraper dashboard?
print("\n" + "=" * 60)
print("[2] SCRAPER DASHBOARD - BENOETIGTE FUNKTIONEN:")
dash_path = "telis_recruitment/templates/scraper_control/dashboard.html". replace("/", os.sep)
if os.path.exists(dash_path):
    with open(dash_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # onclick functions
    onclick = set(re.findall(r'onclick="(\w+)\(', content))
    print(f"  onclick Funktionen: {onclick}")
    
    # Check inline script
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    inline_funcs = []
    for script in scripts: 
        funcs = re.findall(r'function\s+(\w+)\s*\(', script)
        inline_funcs.extend(funcs)
    print(f"  Inline definiert: {set(inline_funcs)}")
    
    missing = onclick - set(inline_funcs)
    if missing:
        print(f"  [FEHLT] {missing}")

# 3. Flow Builder Fix Check
print("\n" + "=" * 60)
print("[3] FLOW BUILDER - FIX BENOETIGT:")
fb_path = "telis_recruitment/email_templates/templates/email_templates/flow_builder.html".replace("/", os.sep)
if os.path.exists(fb_path):
    with open(fb_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    onclick = set(re.findall(r'onclick="(\w+)\(', content))
    print(f"  Benoetigt:  {onclick}")
    
    # Check if extends base
    if "{% extends" in content:
        base = re.findall(r'{% extends ["\']([^"\']+)["\']', content)
        print(f"  Extends:  {base}")
    
    # Check for block js
    if "{% block" in content: 
        blocks = re.findall(r'{% block (\w+)', content)
        print(f"  Blocks: {blocks}")

# 4. Alle Templates ohne JS
print("\n" + "=" * 60)
print("[4] TEMPLATES DIE JS BRAUCHEN ABER KEINE STATIC INCLUDES HABEN:")

templates_dir = "telis_recruitment"
problem_templates = []

for root, dirs, files in os.walk(templates_dir):
    dirs[:] = [d for d in dirs if d not in ["__pycache__", "migrations", "static"]]
    for file in files:
        if file.endswith(". html"):
            filepath = os. path.join(root, file)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            onclick = re.findall(r'onclick="(\w+)\(', content)
            has_static_js = "{% static" in content and ". js" in content
            has_inline = "<script>" in content or "<script " in content
            
            if onclick and not has_static_js and not has_inline:
                problem_templates.append((filepath. replace(templates_dir + os.sep, ""), onclick[: 5]))

if problem_templates: 
    for t, funcs in problem_templates[: 10]:
        print(f"  {t}")
        print(f"    -> braucht:  {funcs}")
else:
    print("  Alle Templates haben JS eingebunden!")

print("\n" + "=" * 60)
