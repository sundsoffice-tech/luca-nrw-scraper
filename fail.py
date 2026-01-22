import sqlite3

con = sqlite3.connect('scraper.db')
cur = con.cursor()

print('=== FAILED EXTRACTIONS ===')
cur.execute("SELECT COUNT(*) FROM failed_extractions")
print(f'Anzahl: {cur.fetchone()[0]}')

cur.execute("SELECT * FROM failed_extractions LIMIT 5")
cols = [d[0] for d in cur.description]
print(f'Spalten: {cols}')
for row in cur.fetchall():
    print(dict(zip(cols, row)))

print('\n=== LEARNING PORTAL METRICS ===')
cur.execute("SELECT * FROM learning_portal_metrics LIMIT 5")
cols = [d[0] for d in cur.description]
print(f'Spalten: {cols}')
for row in cur.fetchall():
    print(dict(zip(cols, row)))

con.close()
