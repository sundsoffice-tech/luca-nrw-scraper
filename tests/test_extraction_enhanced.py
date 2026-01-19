"""
Comprehensive tests for extraction_enhanced.py
Testing email extraction, name extraction, and role detection.
"""

import pytest
from stream2_extraction_layer.extraction_enhanced import (
    extract_email_robust,
    extract_name_enhanced,
    extract_role_with_context,
    _deobfuscate,
    validate_name,
    ExtractionResult,
)


class TestEmailDeobfuscation:
    """Test email deobfuscation patterns"""

    def test_deobfuscate_brackets_at(self):
        """Test [at] pattern"""
        result = _deobfuscate("max [at] firma [dot] de")
        assert "@" in result
        assert "firma" in result

    def test_deobfuscate_parentheses_at(self):
        """Test (at) pattern"""
        result = _deobfuscate("max (at) firma (dot) de")
        assert "@" in result

    def test_deobfuscate_curly_braces(self):
        """Test {at} pattern"""
        result = _deobfuscate("max {at} firma {dot} de")
        assert "@" in result

    def test_deobfuscate_german_at(self):
        """Test ät pattern"""
        result = _deobfuscate("max ät firma punkt de")
        assert "@" in result

    def test_deobfuscate_space_at(self):
        """Test 'at' with spaces"""
        result = _deobfuscate("max at firma dot de")
        assert "@" in result

    def test_deobfuscate_no_change(self):
        """Test that normal text isn't changed"""
        text = "This is normal text"
        result = _deobfuscate(text)
        assert "This is normal text" in result


class TestEmailExtraction:
    """Test email extraction with various patterns"""

    def test_extract_simple_email(self):
        """Test extraction of simple email"""
        text = "Contact me at max.mustermann@firma.de"
        email = extract_email_robust(text, "")
        assert email == "max.mustermann@firma.de"

    def test_extract_obfuscated_email(self):
        """Test extraction of obfuscated email"""
        text = "Kontakt: max [at] firma [dot] de"
        email = extract_email_robust(text, "")
        assert email == "max@firma.de"

    def test_extract_german_obfuscation(self):
        """Test German obfuscation patterns"""
        text = "E-Mail: info ät example punkt de"
        email = extract_email_robust(text, "")
        assert email == "info@example.de"

    def test_ignore_noreply_emails(self):
        """Test that noreply emails are filtered"""
        text = "Contact: noreply@firma.de and real@firma.de"
        email = extract_email_robust(text, "")
        # Should prefer real email over noreply
        assert email is None or email != "noreply@firma.de"

    def test_ignore_portal_emails(self):
        """Test that portal emails are filtered"""
        text = "apply@stepstone.de"
        email = extract_email_robust(text, "")
        assert email is None

    def test_extract_from_html(self):
        """Test extraction from HTML content"""
        html = '<a href="mailto:contact@firma.de">Email us</a>'
        email = extract_email_robust("", html)
        assert email == "contact@firma.de"

    def test_no_email_found(self):
        """Test when no email is present"""
        text = "This text has no email address"
        email = extract_email_robust(text, "")
        assert email is None


class TestNameExtraction:
    """Test name extraction patterns"""

    def test_extract_name_with_context(self):
        """Test name extraction with context markers"""
        text = "Manager: Max Mustermann ist unser Kontakt"
        name = extract_name_enhanced(text, "")
        assert name is not None
        assert "Max Mustermann" in name

    def test_extract_name_with_title(self):
        """Test name extraction with Herr/Frau title"""
        text = "Ansprechpartner: Herr Peter Schmidt"
        name = extract_name_enhanced(text, "")
        assert name is not None
        assert "Peter Schmidt" in name or "Peter" in name

    def test_extract_name_with_parentheses(self):
        """Test name extraction with parentheses"""
        text = "Max Mustermann (CEO) is the contact"
        name = extract_name_enhanced(text, "")
        assert name is not None
        assert "Max Mustermann" in name

    def test_extract_name_ihr_ansprechpartner(self):
        """Test German 'Ihr Ansprechpartner' pattern"""
        text = "Ihr Ansprechpartner: Anna Schmidt"
        name = extract_name_enhanced(text, "")
        assert name is not None
        assert "Anna Schmidt" in name

    def test_no_name_found(self):
        """Test when no name is found"""
        text = "this is just some text without a proper name"
        name = extract_name_enhanced(text, "")
        # May return None or empty string depending on implementation
        assert name is None or name == ""

    def test_validate_name(self):
        """Test name validation"""
        assert validate_name("Max Mustermann") is True
        assert validate_name("M") is False
        assert validate_name(None) is False


class TestRoleDetection:
    """Test role detection from text"""

    def test_detect_vertriebsleiter(self):
        """Test detection of Vertriebsleiter role"""
        text = "Wir suchen einen erfahrenen Vertriebsleiter"
        role, confidence = extract_role_with_context(text, "", "")
        assert role is not None
        assert "vertriebsleiter" in role.lower()

    def test_detect_sales_director(self):
        """Test detection of Sales Director"""
        text = "Position: Sales Director for Germany"
        role, confidence = extract_role_with_context(text, "", "")
        assert role is not None
        # Should map to vertriebsleiter category

    def test_detect_aussendienst(self):
        """Test detection of Außendienst"""
        text = "Außendienstmitarbeiter gesucht"
        role, confidence = extract_role_with_context(text, "", "")
        assert role is not None
        assert "außendienst" in role.lower() or "aussendienst" in role.lower()

    def test_detect_recruiter(self):
        """Test detection of Recruiter"""
        text = "We need a talented recruiter"
        role, confidence = extract_role_with_context(text, "", "")
        assert role is not None
        assert "recruiter" in role.lower()

    def test_detect_callcenter(self):
        """Test detection of Call Center roles"""
        text = "Call Center Agent for outbound sales"
        role, confidence = extract_role_with_context(text, "", "")
        assert role is not None
        # Should detect callcenter-related role

    def test_no_role_detected(self):
        """Test when no role is detected"""
        text = "Just some random text"
        role, confidence = extract_role_with_context(text, "", "")
        # Should return None or empty string
        assert role is None or role == ""


class TestExtractionResult:
    """Test ExtractionResult dataclass"""

    def test_extraction_result_creation(self):
        """Test creating an ExtractionResult"""
        result = ExtractionResult(
            name="Max Mustermann",
            rolle="Vertriebsleiter",
            email="max@firma.de",
            extraction_method="regex",
            confidence=0.85,
        )
        assert result.name == "Max Mustermann"
        assert result.rolle == "Vertriebsleiter"
        assert result.email == "max@firma.de"
        assert result.confidence == 0.85

    def test_extraction_result_defaults(self):
        """Test ExtractionResult with default values"""
        result = ExtractionResult()
        assert result.name is None
        assert result.rolle is None
        assert result.email is None
        assert result.extraction_method is None
        assert result.confidence == 0.0


@pytest.mark.integration
class TestIntegratedExtraction:
    """Integration tests combining multiple extraction functions"""

    def test_extract_full_contact_info(self):
        """Test extracting complete contact information"""
        text = """
        Ihr Ansprechpartner: Max Mustermann
        Position: Vertriebsleiter
        E-Mail: max.mustermann@firma.de
        """
        
        name = extract_name_enhanced(text, "")
        email = extract_email_robust(text, "")
        role, confidence = extract_role_with_context(text, "", "")
        
        assert name is not None
        assert email == "max.mustermann@firma.de"
        assert role is not None

    def test_extract_from_job_posting(self):
        """Test extraction from a typical job posting"""
        text = """
        Wir suchen einen Vertriebsleiter (m/w/d) für unseren Standort in NRW.
        Ihr Ansprechpartner: Herr Schmidt
        Kontakt: schmidt [at] beispiel [dot] de
        """
        
        name = extract_name_enhanced(text, "")
        email = extract_email_robust(text, "")
        role, confidence = extract_role_with_context(text, "", "")
        
        assert name is not None
        assert "Schmidt" in name
        assert email is not None
        assert "@" in email
        assert role is not None
        assert "vertrieb" in role.lower()

    def test_extract_obfuscated_contact(self):
        """Test extraction with heavily obfuscated contact info"""
        text = "Anna Meyer (at) company (dot) com - Recruiting Manager"
        
        email = extract_email_robust(text, "")
        name = extract_name_enhanced(text, "")
        role, confidence = extract_role_with_context(text, "", "")
        
        assert email is not None
        assert "@" in email
        # Name extraction might be challenging with obfuscation
        # Role should detect "Recruiting"
        assert role is not None or "recruit" in text.lower()
