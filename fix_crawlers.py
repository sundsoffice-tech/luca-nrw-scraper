import re

path = r'C:\Users\sunds\Desktop\Luca\luca_scraper\crawlers.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Einfache String-Ersetzungen
replacements = {
    'soup.  select_one': 'soup.select_one',
    "'.  userprofile": "'.userprofile",
    "'.  iconlist": "'.iconlist",
    'asyncio. sleep': 'asyncio.sleep',
    'seen_cache. add': 'seen_cache.add',
    'detail_urls.  append': 'detail_urls.append',
    'data. get': 'data.get',
    'wa_number. replace': 'wa_number.replace',
    "'html. parser'": "'html.parser'",
    ', 2. 0)': ', 2.0)',
    'seen_cache:  set': 'seen_cache: set',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed successfully!')
