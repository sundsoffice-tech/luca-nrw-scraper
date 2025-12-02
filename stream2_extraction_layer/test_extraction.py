def test_extract_email_deobfuscate():
    from stream2_extraction_layer.extraction_enhanced import extract_email_robust

    text = "Kontakt: max [at] firma [dot] de"
    email = extract_email_robust(text, "")
    assert email == "max@firma.de"
