import sqlite3

# Die RICHTIGE Datenbank (ohne Leerzeichen!)
con = sqlite3.connect("scraper.db")
cur = con.cursor()

# Alle Tabellen anzeigen
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("=== TABELLEN IN scraper.db ===")
for t in tables:
    table_name = t[0]
    print(f"\n--- {table_name} ---")
    cur.execute(f"PRAGMA table_info({table_name})")
    for col in cur. fetchall():
        print(f"  {col[1]} ({col[2]})")

# Anzahl Leads
try:
    cur.execute("SELECT COUNT(*) FROM leads")
    count = cur.fetchone()[0]
    print(f"\n=== LEADS ANZAHL: {count} ===")
except: 
    print("\n=== KEINE leads TABELLE!  ===")

con.close()
