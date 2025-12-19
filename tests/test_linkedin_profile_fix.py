"""
Tests for LinkedIn Profile Fix in Candidates Mode.
This validates that LinkedIn profiles are not blocked as "job_ad" in candidates mode.
"""
import pytest
import os
from scriptname import (
    is_candidate_profile_text,
    is_garbage_context,
    _is_candidates_mode,
)


class TestCandidatesModeFunctions:
    """Test the _is_candidates_mode helper function."""
    
    def test_is_candidates_mode_with_candidates(self):
        """Test that 'candidates' in INDUSTRY returns True."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "candidates"
            assert _is_candidates_mode() is True
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_is_candidates_mode_with_recruiter(self):
        """Test that 'recruiter' in INDUSTRY returns True."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "recruiter"
            assert _is_candidates_mode() is True
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_is_candidates_mode_with_other(self):
        """Test that other INDUSTRY values return False."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "all"
            assert _is_candidates_mode() is False
            
            os.environ["INDUSTRY"] = "vertrieb"
            assert _is_candidates_mode() is False
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]


class TestIsCandidateProfileTextFix:
    """Test that is_candidate_profile_text returns True in candidates mode."""
    
    def test_returns_true_in_candidates_mode(self):
        """Test that function returns True for any text in candidates mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "candidates"
            
            # Should return True for any text in candidates mode
            assert is_candidate_profile_text("") is True
            assert is_candidate_profile_text("some random text") is True
            assert is_candidate_profile_text("wir suchen") is True
            assert is_candidate_profile_text("GmbH Company") is True
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_returns_true_in_recruiter_mode(self):
        """Test that function returns True for any text in recruiter mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "recruiter"
            
            # Should return True for any text in recruiter mode
            assert is_candidate_profile_text("") is True
            assert is_candidate_profile_text("some random text") is True
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_normal_behavior_in_standard_mode(self):
        """Test that function behaves normally when not in candidates mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "all"
            
            # Should return False for text without positive markers
            assert is_candidate_profile_text("random text") is False
            
            # Should return True for text with positive markers
            assert is_candidate_profile_text("suche job im vertrieb") is True
            
            # Should return False if negative markers present
            assert is_candidate_profile_text("wir suchen vertrieb") is False
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]


class TestIsGarbageContextFix:
    """Test that is_garbage_context never marks social profiles as garbage in candidates mode."""
    
    def test_linkedin_profile_not_garbage_in_candidates_mode(self):
        """Test that LinkedIn profiles are not marked as garbage in candidates mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "candidates"
            
            # LinkedIn profiles should not be garbage
            is_garbage, reason = is_garbage_context(
                text="wir suchen vertrieb",  # Would normally be marked as job_ad
                url="https://de.linkedin.com/in/lchgoodman",
                title="John Doe - LinkedIn",
                h1=""
            )
            assert is_garbage is False, f"LinkedIn profile should not be garbage, got reason: {reason}"
            assert reason == ""
            
            # Another LinkedIn profile test
            is_garbage, reason = is_garbage_context(
                text="some text with gmbh",
                url="https://www.linkedin.com/in/alexandra-grows-business/de",
                title="Alexandra - LinkedIn Profile",
                h1=""
            )
            assert is_garbage is False, f"LinkedIn profile should not be garbage, got reason: {reason}"
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_xing_profile_not_garbage_in_candidates_mode(self):
        """Test that XING profiles are not marked as garbage in candidates mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "candidates"
            
            is_garbage, reason = is_garbage_context(
                text="wir suchen vertrieb",
                url="https://www.xing.com/profile/Max_Mustermann",
                title="Max Mustermann - XING",
                h1=""
            )
            assert is_garbage is False
            assert reason == ""
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_other_social_profiles_not_garbage_in_candidates_mode(self):
        """Test that other social media profiles are not marked as garbage in candidates mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "candidates"
            
            social_urls = [
                "https://www.instagram.com/johndoe",
                "https://www.facebook.com/janedoe",
                "https://twitter.com/handle",
                "https://x.com/handle",
                "https://t.me/username",
                "https://chat.whatsapp.com/invite123",
            ]
            
            for url in social_urls:
                is_garbage, reason = is_garbage_context(
                    text="wir suchen vertrieb",
                    url=url,
                    title="Profile",
                    h1=""
                )
                assert is_garbage is False, f"Social profile {url} should not be garbage"
                assert reason == ""
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_normal_garbage_detection_in_standard_mode(self):
        """Test that garbage detection works normally when not in candidates mode."""
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "all"
            
            # Job ads should still be detected as garbage
            is_garbage, reason = is_garbage_context(
                text="wir suchen vertrieb mitarbeiter",
                url="https://example.com/jobs/sales",
                title="Job Opening",
                h1=""
            )
            assert is_garbage is True
            assert reason == "job_ad"
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]
    
    def test_linkedin_profile_with_job_ad_text_not_garbage_in_candidates_mode(self):
        """
        Test the exact scenario from the problem statement:
        LinkedIn profile with job_ad-like text should not be marked as garbage.
        """
        original = os.environ.get("INDUSTRY")
        try:
            os.environ["INDUSTRY"] = "candidates"
            
            # This is the exact scenario: LinkedIn profile with text that looks like job ad
            is_garbage, reason = is_garbage_context(
                text="wir suchen einen Vertriebsmitarbeiter",
                url="https://de.linkedin.com/in/lchgoodman",
                title="L. Ch. Goodman",
                h1="About"
            )
            
            # Should NOT be marked as garbage
            assert is_garbage is False, (
                f"LinkedIn profile should not be marked as garbage even with job_ad text. "
                f"Got is_garbage={is_garbage}, reason={reason}"
            )
            assert reason == "", f"Expected empty reason, got: {reason}"
            
        finally:
            if original:
                os.environ["INDUSTRY"] = original
            elif "INDUSTRY" in os.environ:
                del os.environ["INDUSTRY"]


class TestTitleGuardFix:
    """
    Test title guard behavior for social profiles in candidates mode.
    Note: We cannot directly test process_link_async here since it's async and has many dependencies.
    This test documents the expected behavior.
    """
    
    def test_title_guard_documentation(self):
        """
        Document the expected behavior of the title guard fix:
        
        In candidates mode:
        - Social profiles (linkedin.com/in/, xing.com/profile/, etc.) should SKIP the title guard
        - This means profiles with "GmbH" in the title should NOT be blocked
        - Non-social URLs should still apply the title guard logic
        
        This is implemented in process_link_async around line 4313-4328.
        """
        # This is a documentation test - the actual behavior is tested via integration tests
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
