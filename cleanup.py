import sqlite3

conn = sqlite3.connect('scraper.db')
c = conn.cursor()

# Zaehle vorher
c.execute("SELECT COUNT(*) FROM leads")
vorher = c.fetchone()[0]
print(f"Leads vorher: {vorher}")

# Loesche Muell
c.execute("DELETE FROM leads WHERE name LIKE '%_probe_%'")
c.execute("DELETE FROM leads WHERE telefon LIKE '%1234567890%'")
c.execute("DELETE FROM leads WHERE telefon IS NULL OR telefon = ''")
c.execute("DELETE FROM leads WHERE LENGTH(telefon) < 12")

conn.commit()

# Zaehle nachher
c.execute("SELECT COUNT(*) FROM leads")
nachher = c.fetchone()[0]
print(f"Leads nachher: {nachher}")
print(f"Geloescht: {vorher - nachher}")

conn.close()