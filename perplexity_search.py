import os
import json
import requests
import random
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY', '')

def ask_perplexity(prompt):
    if not PERPLEXITY_API_KEY:
        print('[ERROR] PERPLEXITY_API_KEY nicht gesetzt!')
        return []
    
    headers = {
        'Authorization':  f'Bearer {PERPLEXITY_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'sonar',
        'messages': [
            {
                'role': 'system',
                'content': 'Du bist ein Experte fuer Vertriebsrecherche in Deutschland. Finde aktuelle Links zu Vertriebsprofis.  Antworte NUR mit JSON:  ["url1", "url2", ...]'
            },
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 1500,
        'temperature': 0.8
    }
    
    try:
        resp = requests.post('https://api.perplexity.ai/chat/completions', headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        import re
        json_match = re. search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            urls = json.loads(json_match.group())
            return [u for u in urls if isinstance(u, str) and u.startswith('http')]
        return []
    except Exception as e:
        print(f'[Perplexity Error] {e}')
        return []

def get_prompt():
    prompts = [
        "Finde 15 LinkedIn Profile von Vertriebsmitarbeitern in NRW die offen fuer neue Jobs sind.  Nur URLs.",
        "Suche 15 Kleinanzeigen. de Links wo Vertriebler Stellengesuche haben.  Nur URLs.",
        "Finde 15 XING Profile von Handelsvertretern oder freien Aussendienstlern. Nur URLs.",
        "Suche 15 Stellengesuche von Vertrieblern auf Indeed, Stepstone.  Nur URLs.",
        "Finde 15 Freelancermap Profile im Bereich Sales, Vertrieb.  Nur URLs.",
        "Suche 15 Profile von Solar-Vertrieblern die neue Auftraggeber suchen. Nur URLs.",
        "Finde 15 Versicherungsvertreter die neue Jobs suchen.  Nur URLs.",
        "Suche 15 Telekom Vertriebsleute auf Karriereportalen. Nur URLs.",
        "Finde 15 Call-Center Mitarbeiter die Jobs suchen. Nur URLs.",
        "Suche 15 D2D Vertriebler Stellengesuche. Nur URLs.",
    ]
    return random.choice(prompts)

if __name__ == '__main__':
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Perplexity Search...")
    prompt = get_prompt()
    print(f"Prompt: {prompt[: 70]}...")
    urls = ask_perplexity(prompt)
    print(f"Gefunden: {len(urls)} URLs")
    for i, url in enumerate(urls[: 10], 1):
        print(f"  {i}. {url[: 80]}")
