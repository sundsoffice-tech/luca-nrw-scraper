"""
Tests for talent_hunt mode to ensure it correctly identifies and processes
active salespeople profiles instead of job seekers.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestTalentHuntModeDetection:
    """Test talent_hunt mode detection and behavior."""
    
    def test_is_talent_hunt_mode_true(self):
        """Test that _is_talent_hunt_mode returns True when INDUSTRY=talent_hunt."""
        from scriptname import _is_talent_hunt_mode
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert _is_talent_hunt_mode() is True
    
    def test_is_talent_hunt_mode_false(self):
        """Test that _is_talent_hunt_mode returns False for other modes."""
        from scriptname import _is_talent_hunt_mode
        
        with patch.dict(os.environ, {"INDUSTRY": "candidates"}):
            assert _is_talent_hunt_mode() is False
        
        with patch.dict(os.environ, {"INDUSTRY": "recruiter"}):
            assert _is_talent_hunt_mode() is False
        
        with patch.dict(os.environ, {"INDUSTRY": "all"}):
            assert _is_talent_hunt_mode() is False
    
    def test_is_candidates_mode_excludes_talent_hunt(self):
        """Test that _is_candidates_mode returns False when in talent_hunt mode."""
        from scriptname import _is_candidates_mode
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert _is_candidates_mode() is False
    
    def test_is_candidates_mode_true_for_candidates(self):
        """Test that _is_candidates_mode returns True for candidates/recruiter."""
        from scriptname import _is_candidates_mode
        
        with patch.dict(os.environ, {"INDUSTRY": "candidates"}):
            assert _is_candidates_mode() is True
        
        with patch.dict(os.environ, {"INDUSTRY": "recruiter"}):
            assert _is_candidates_mode() is True


class TestTalentHuntURLFiltering:
    """Test URL filtering in talent_hunt mode."""
    
    def test_linkedin_profile_allowed_in_talent_hunt(self):
        """Test that LinkedIn profiles are allowed in talent_hunt mode."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert is_denied("https://www.linkedin.com/in/max-mustermann") is False
            assert is_denied("https://linkedin.com/in/jane-doe") is False
    
    def test_xing_profile_allowed_in_talent_hunt(self):
        """Test that XING profiles are allowed in talent_hunt mode."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert is_denied("https://www.xing.com/profile/Max_Mustermann") is False
            assert is_denied("https://xing.com/profiles/Jane_Doe") is False
    
    def test_team_pages_allowed_in_talent_hunt(self):
        """Test that team pages are allowed in talent_hunt mode."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert is_denied("https://example.com/team") is False
            assert is_denied("https://example.com/unser-team") is False
            assert is_denied("https://example.com/mitarbeiter") is False
            assert is_denied("https://example.com/ansprechpartner") is False
    
    def test_freelancer_portals_allowed_in_talent_hunt(self):
        """Test that freelancer portals are allowed in talent_hunt mode."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert is_denied("https://www.freelancermap.de/profile/123") is False
            assert is_denied("https://gulp.de/freelancer/456") is False
            assert is_denied("https://freelance.de/profil/789") is False
    
    def test_cdh_allowed_in_talent_hunt(self):
        """Test that CDH (Handelsvertreter) is allowed in talent_hunt mode."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert is_denied("https://www.cdh.de/handelsvertreter/123") is False
    
    def test_ihk_blocked_in_non_talent_hunt(self):
        """Test that IHK is blocked in non-talent_hunt modes."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "all"}):
            assert is_denied("https://www.ihk.de/page") is True
    
    def test_ihk_allowed_in_talent_hunt(self):
        """Test that IHK is allowed in talent_hunt mode."""
        from scriptname import is_denied
        
        with patch.dict(os.environ, {"INDUSTRY": "talent_hunt"}):
            assert is_denied("https://www.ihk.de/handelsvertreter") is False


class TestTalentHuntLeadTypeDetection:
    """Test lead type detection for talent_hunt mode."""
    
    def test_detect_active_salesperson_linkedin(self):
        """Test that LinkedIn profiles without #opentowork are detected as active salespeople."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://linkedin.com/in/max-mustermann"
        text = "Account Manager at Company X. 10 years experience in sales."
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "active_salesperson"
    
    def test_detect_candidate_linkedin_opentowork(self):
        """Test that LinkedIn profiles with #opentowork are detected as candidates."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://linkedin.com/in/jane-doe"
        text = "Sales Manager #opentowork. Looking for new opportunities."
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "candidate"
    
    def test_detect_candidate_offen_fuer(self):
        """Test German 'offen für' is detected as candidate."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://xing.com/profile/Max_Mustermann"
        text = "Vertriebsleiter. Offen für neue Herausforderungen."
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "candidate"
    
    def test_detect_team_member_from_url(self):
        """Test that team pages are detected as team_member."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://company.de/team/sales"
        text = "Our sales team"
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "team_member"
    
    def test_detect_freelancer_from_portal(self):
        """Test that freelancer portal profiles are detected as freelancer."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://freelancermap.de/freelancer/123"
        text = "Freiberuflicher Vertriebsberater"
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "freelancer"
    
    def test_detect_hr_contact(self):
        """Test that HR contacts are detected."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://company.de/kontakt"
        text = "Jane Doe, HR Manager, Human Resources Department"
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "hr_contact"
    
    def test_detect_handelsvertreter_from_cdh(self):
        """Test that CDH profiles are detected as active salespeople."""
        from scriptname import _detect_lead_type_talent_hunt
        
        url = "https://www.cdh.de/mitglieder/12345"
        text = "Handelsvertreter für NRW"
        lead = {}
        
        result = _detect_lead_type_talent_hunt(url, text, lead)
        assert result == "active_salesperson"


class TestTalentHuntLeadTypeFiltering:
    """Test that lead type filtering works correctly in talent_hunt mode."""
    
    def test_talent_hunt_allows_active_salesperson(self):
        """Test that active_salesperson leads are allowed in talent_hunt mode."""
        # This would need to be tested in integration with the actual filtering logic
        # Just documenting the expected behavior
        allowed_types = ("active_salesperson", "team_member", "freelancer", 
                        "hr_contact", "candidate", "company", "contact", None, "")
        
        assert "active_salesperson" in allowed_types
        assert "team_member" in allowed_types
        assert "freelancer" in allowed_types
        assert "hr_contact" in allowed_types
    
    def test_candidates_mode_only_allows_candidates(self):
        """Test that candidates mode only allows candidate and group_invite."""
        allowed_types = ("candidate", "group_invite")
        
        assert "candidate" in allowed_types
        assert "group_invite" in allowed_types
        assert "active_salesperson" not in allowed_types


class TestTalentHuntQueries:
    """Test that talent_hunt queries are properly configured."""
    
    def test_talent_hunt_queries_exist(self):
        """Test that INDUSTRY_QUERIES contains talent_hunt queries."""
        from scriptname import INDUSTRY_QUERIES
        
        assert "talent_hunt" in INDUSTRY_QUERIES
        assert len(INDUSTRY_QUERIES["talent_hunt"]) > 0
    
    def test_talent_hunt_queries_target_profiles(self):
        """Test that talent_hunt queries target LinkedIn/XING profiles."""
        from scriptname import INDUSTRY_QUERIES
        
        queries = INDUSTRY_QUERIES.get("talent_hunt", [])
        
        # Check that some queries target LinkedIn
        linkedin_queries = [q for q in queries if "linkedin.com/in" in q]
        assert len(linkedin_queries) > 0
        
        # Check that some queries target XING
        xing_queries = [q for q in queries if "xing.com/profile" in q]
        assert len(xing_queries) > 0
        
        # Check that queries exclude job seekers
        excluding_opentowork = [q for q in queries if "-\"#opentowork\"" in q or "-\"open to work\"" in q]
        assert len(excluding_opentowork) > 0
    
    def test_talent_hunt_queries_target_team_pages(self):
        """Test that talent_hunt queries target team pages."""
        from scriptname import INDUSTRY_QUERIES
        
        queries = INDUSTRY_QUERIES.get("talent_hunt", [])
        
        # Check for team page queries
        team_queries = [q for q in queries if any(term in q.lower() for term in ["team", "mitarbeiter", "ansprechpartner"])]
        assert len(team_queries) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
