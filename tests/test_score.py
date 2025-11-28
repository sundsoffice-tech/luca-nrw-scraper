from scriptname import compute_score
def test_contact_path_bonus():
    t = "Vertrieb | WhatsApp +49 176 1234567 | E-Mail sales@firma.de"
    assert compute_score(t, "https://example.de/kontakt") >= compute_score(t, "https://example.de/blog")
