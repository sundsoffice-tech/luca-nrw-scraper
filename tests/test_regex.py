from scriptname import regex_extract_contacts
def test_obfuscation():
    html = "Mail: max [at] firma [dot] de Tel: +49 176 1234567 Vertrieb jetzt starten"
    rows = regex_extract_contacts(html, "https://example.de/kontakt")
    assert any(r.get("email")=="max@firma.de" for r in rows)
    assert any(r.get("telefon").startswith("+49176") for r in rows)
