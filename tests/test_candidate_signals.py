"""
Tests for candidate signal detection to ensure job-seeking candidates are not blocked.
These tests verify the fixes for the candidates mode that prevent false blocking.
"""
import pytest
from scriptname import (
    is_candidate_seeking_job,
    is_job_advertisement,
    is_garbage_context,
    has_nrw_signal,
)


class TestCandidateSignalDetection:
    """Test that candidate signals are properly detected."""
    
    def test_candidate_seeking_job_with_ich_suche(self):
        """Test detection of 'ich suche' patterns."""
        assert is_candidate_seeking_job("Ich suche Job im Vertrieb", "", "") is True
        assert is_candidate_seeking_job("ich suche arbeit als Verkäufer", "", "") is True
        assert is_candidate_seeking_job("Ich suche neue Stelle im Außendienst", "", "") is True
    
    def test_candidate_seeking_job_with_stellengesuch(self):
        """Test detection of 'stellengesuch' patterns."""
        assert is_candidate_seeking_job("Stellengesuch: Vertriebsmitarbeiter", "", "") is True
        assert is_candidate_seeking_job("", "Stellengesuch Verkäufer", "") is True
    
    def test_candidate_seeking_job_with_open_to_work(self):
        """Test detection of 'open to work' patterns."""
        assert is_candidate_seeking_job("Sales Manager - Open to Work", "", "") is True
        assert is_candidate_seeking_job("#OpenToWork Vertrieb Köln", "", "") is True
        assert is_candidate_seeking_job("", "Max Mustermann | #opentowork", "") is True
    
    def test_candidate_seeking_job_with_verfuegbar(self):
        """Test detection of 'verfügbar ab' patterns."""
        assert is_candidate_seeking_job("Vertriebsprofi verfügbar ab sofort", "", "") is True
        assert is_candidate_seeking_job("Freigestellt, suche neue Herausforderung", "", "") is True
    
    def test_candidate_seeking_job_with_offen_fuer(self):
        """Test detection of 'offen für' patterns."""
        assert is_candidate_seeking_job("Offen für Angebote im Sales Bereich", "", "") is True
        assert is_candidate_seeking_job("Offen für neue Chancen", "", "") is True
    
    def test_not_candidate_when_company_hiring(self):
        """Test that company job offers are not detected as candidates."""
        assert is_candidate_seeking_job("Wir suchen Vertriebsmitarbeiter", "", "") is False
        assert is_candidate_seeking_job("Gesucht: Sales Manager (m/w/d)", "", "") is False


class TestJobAdvertisementDetection:
    """Test that job advertisements are distinguished from candidate profiles."""
    
    def test_candidate_not_marked_as_job_ad(self):
        """Test that candidates seeking jobs are NOT marked as job ads."""
        # These should NOT be job ads (they are candidates)
        assert is_job_advertisement("Ich suche Job im Vertrieb", "", "") is False
        assert is_job_advertisement("Stellengesuch: Verkäufer mit Erfahrung", "", "") is False
        assert is_job_advertisement("Auf Jobsuche - Sales Professional", "", "") is False
        assert is_job_advertisement("", "Open to Work | Vertrieb", "") is False
    
    def test_company_job_offers_marked_as_job_ad(self):
        """Test that company job offers ARE marked as job ads."""
        # These SHOULD be job ads (companies hiring)
        assert is_job_advertisement("Wir suchen Vertriebsmitarbeiter (m/w/d)", "", "") is True
        assert is_job_advertisement("Sales Manager gesucht", "", "") is True
        assert is_job_advertisement("Join our team! Vertrieb (m/w/d)", "", "") is True
        assert is_job_advertisement("", "Stellenanzeige: Außendienst (m/w/d)", "") is True
    
    def test_mixed_signals_prioritize_candidate(self):
        """Test that when both candidate and company signals exist, candidate wins."""
        # Candidate signal should take priority
        text = "Ich suche Job im Vertrieb. Nicht: Wir suchen"
        assert is_job_advertisement(text, "", "") is False


class TestGarbageContextDetection:
    """Test that garbage detection doesn't block candidates."""
    
    def test_candidate_not_marked_as_garbage(self):
        """Test that candidates are NOT marked as garbage."""
        is_garbage, reason = is_garbage_context("Ich suche Job im Vertrieb", "", "Stellengesuch", "")
        assert is_garbage is False
        
        is_garbage, reason = is_garbage_context("Open to Work - Sales Manager", "", "#OpenToWork", "")
        assert is_garbage is False
        
        is_garbage, reason = is_garbage_context("Suche neue Stelle im Außendienst", "", "Jobsuche", "")
        assert is_garbage is False
    
    def test_job_ads_marked_as_garbage(self):
        """Test that job ads are marked as garbage."""
        is_garbage, reason = is_garbage_context("Wir suchen Vertriebsmitarbeiter", "", "Job (m/w/d)", "")
        assert is_garbage is True
        assert reason == "job_ad"
        
        is_garbage, reason = is_garbage_context("Stellenanzeige: Sales Manager gesucht", "", "", "")
        assert is_garbage is True
        assert reason == "job_ad"
    
    def test_news_still_marked_as_garbage(self):
        """Test that news/blog content is still marked as garbage."""
        is_garbage, reason = is_garbage_context("Die neuesten Vertriebstrends 2024", "", "News Artikel", "")
        assert is_garbage is True
        assert reason == "news_blog"


class TestNRWSignalDetection:
    """Test that NRW region signals are detected."""
    
    def test_nrw_explicit(self):
        """Test detection of explicit 'NRW' mention."""
        assert has_nrw_signal("Vertrieb NRW") is True
        assert has_nrw_signal("Sales Job in NRW") is True
        assert has_nrw_signal("Nordrhein-Westfalen") is True
    
    def test_nrw_cities(self):
        """Test detection of NRW cities."""
        assert has_nrw_signal("Vertrieb Düsseldorf") is True
        assert has_nrw_signal("Sales Job Köln") is True
        assert has_nrw_signal("Außendienst Dortmund") is True
        assert has_nrw_signal("Verkäufer Essen") is True
        assert has_nrw_signal("Münster Vertrieb") is True
    
    def test_nrw_regions(self):
        """Test detection of NRW regions."""
        assert has_nrw_signal("Ruhrgebiet Vertrieb") is True
        assert has_nrw_signal("Rheinland Sales") is True
        assert has_nrw_signal("Sauerland") is True
    
    def test_not_nrw(self):
        """Test that non-NRW locations return False."""
        assert has_nrw_signal("München Bayern") is False
        assert has_nrw_signal("Berlin") is False
        assert has_nrw_signal("Hamburg") is False


class TestCandidateScenarios:
    """Test real-world candidate scenarios from the problem statement."""
    
    def test_kleinanzeigen_stellengesuch_not_blocked(self):
        """Test that Kleinanzeigen Stellengesuche are not blocked."""
        title = "Ich suche Job im Vertrieb - NRW"
        text = "Ich suche neuen Job als Vertriebsmitarbeiter in NRW. Mobil: 0176-12345678"
        url = "https://kleinanzeigen.de/s-stellengesuche/vertrieb-123"
        
        assert is_candidate_seeking_job(text, title, url) is True
        assert is_job_advertisement(text, title, "") is False
        is_garbage, _ = is_garbage_context(text, url, title, "")
        assert is_garbage is False
    
    def test_minijob_search_not_blocked(self):
        """Test that minijob searches by candidates are not blocked."""
        title = "Ich suche Minijobs im Verkauf"
        text = "Suche Minijob als Verkäuferin, Erfahrung vorhanden"
        
        assert is_candidate_seeking_job(text, title, "") is True
        assert is_job_advertisement(text, title, "") is False
    
    def test_haushaltshilfe_search_not_blocked(self):
        """Test that job searches (even for helpers) are not blocked as garbage."""
        title = "Suche Job als Haushaltshilfe"
        text = "Ich suche Arbeit als Haushaltshilfe in Köln"
        
        # This is a candidate seeking work
        assert is_candidate_seeking_job(text, title, "") is True
        # Not a job advertisement
        assert is_job_advertisement(text, title, "") is False
    
    def test_linkedin_open_to_work_not_blocked(self):
        """Test that LinkedIn Open to Work profiles are not blocked."""
        title = "Max Mustermann | Sales Manager | #OpenToWork"
        text = "Experienced sales professional, open to work in NRW region"
        url = "https://linkedin.com/in/max-mustermann"
        
        assert is_candidate_seeking_job(text, title, url) is True
        assert is_job_advertisement(text, title, "") is False
        is_garbage, _ = is_garbage_context(text, url, title, "")
        assert is_garbage is False
    
    def test_xing_profile_offen_fuer_angebote_not_blocked(self):
        """Test that Xing profiles with 'offen für Angebote' are not blocked."""
        title = "Anna Schmidt - Vertriebsleiterin"
        text = "Offen für neue Angebote im Sales Bereich. Region NRW bevorzugt."
        url = "https://xing.com/profile/Anna_Schmidt"
        
        assert is_candidate_seeking_job(text, title, url) is True
        assert is_job_advertisement(text, title, "") is False
    
    def test_company_job_posting_is_blocked(self):
        """Test that company job postings ARE blocked (as they should be)."""
        title = "Sales Manager (m/w/d) gesucht"
        text = "Wir suchen Vertriebsmitarbeiter (m/w/d) für unser Team in Düsseldorf"
        
        # This is NOT a candidate
        assert is_candidate_seeking_job(text, title, "") is False
        # This IS a job advertisement
        assert is_job_advertisement(text, title, "") is True
        # Should be marked as garbage
        is_garbage, reason = is_garbage_context(text, "", title, "")
        assert is_garbage is True
        assert reason == "job_ad"


class TestEnhancedCandidateSignals:
    """Test the enhanced candidate signal detection."""
    
    def test_quereinstieg_signals(self):
        """Test that Quereinstieg signals are detected."""
        assert is_candidate_seeking_job("Suche Quereinstieg im Vertrieb", "", "") is True
        assert is_candidate_seeking_job("Quereinsteiger mit Motivation", "", "") is True
        assert is_candidate_seeking_job("Möchte mehr Geld verdienen im Sales", "", "") is True
    
    def test_url_pattern_stellengesuche(self):
        """Test that Stellengesuche URL patterns are always detected as candidates."""
        url = "https://kleinanzeigen.de/s-stellengesuche/vertrieb-nrw/123"
        # Even with negative text, URL pattern should win
        assert is_candidate_seeking_job("", "", url) is True
        
        is_garbage, _ = is_garbage_context("wir suchen", url, "", "")
        assert is_garbage is False  # URL pattern overrides
    
    def test_url_pattern_stellenangebote_blocked(self):
        """Test that Stellenangebote URL patterns are blocked as job ads."""
        url = "https://kleinanzeigen.de/s-jobs/vertrieb-nrw/123"
        # This should be blocked as job ad
        is_garbage, reason = is_garbage_context("Vertriebsmitarbeiter", url, "", "")
        assert is_garbage is True
        assert reason == "job_ad"
    
    def test_contact_data_with_medium_signal(self):
        """Test that medium signals with contact data are accepted."""
        text = "Mein Profil: Erfahrung im Vertrieb. Tel: 0176-12345678"
        assert is_candidate_seeking_job(text, "", "") is True
    
    def test_sales_context_with_medium_signal(self):
        """Test that medium signals with sales context are accepted."""
        text = "Meine Erfahrung im Vertrieb: 5 Jahre Außendienst"
        assert is_candidate_seeking_job(text, "", "") is True
    
    def test_homeoffice_search_not_blocked(self):
        """Test that homeoffice job searches are not blocked."""
        text = "Ich suche Homeoffice Job im Vertrieb"
        assert is_candidate_seeking_job(text, "", "") is True
        assert is_job_advertisement(text, "", "") is False
    
    def test_handelsvertreter_signals(self):
        """Test that Handelsvertreter signals are detected."""
        assert is_candidate_seeking_job("Handelsvertreter sucht neue Vertretung", "", "") is True
        assert is_candidate_seeking_job("Auf Provisionsbasis arbeiten", "", "") is True
    
    def test_karrierewechsel_signals(self):
        """Test that career change signals are detected."""
        assert is_candidate_seeking_job("Karrierewechsel geplant", "", "") is True
        assert is_candidate_seeking_job("Bereit für Veränderung", "", "") is True
        assert is_candidate_seeking_job("Wechselbereit und motiviert", "", "") is True
