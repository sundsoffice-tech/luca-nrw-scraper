import sqlite3
conn = sqlite3.connect('scraper.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tabellen:', [t[0] for t in tables])
for t in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {t[0]}')
    count = cursor.fetchone()[0]
    print(f'  {t[0]}: {count} Einträge')
conn.close()
