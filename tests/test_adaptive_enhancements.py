"""
Tests for phase-based adaptive search enhancements.
"""
import pytest
import time
from scriptname import validate_phone, normalize_phone, should_drop_lead
from stream3_scoring_layer import scoring_enhanced as se
from metrics import MetricsStore, DorkMetrics, HostMetrics
from wasserfall import WasserfallManager, MODE_CONSERVATIVE, MODE_MODERATE, MODE_AGGRESSIVE


class TestPhoneValidation:
    """Test phone validation with strict requirements."""
    
    def test_valid_german_mobile(self):
        """Test valid German mobile numbers."""
        is_valid, phone_type = validate_phone("+491761234567")
        assert is_valid is True
        assert phone_type == "mobile"
        
        is_valid, phone_type = validate_phone("0176 1234567")
        assert is_valid is True
        assert phone_type == "mobile"
        
        is_valid, phone_type = validate_phone("+4915012345678")
        assert is_valid is True
        assert phone_type == "mobile"
    
    def test_valid_german_landline(self):
        """Test valid German landline numbers."""
        is_valid, phone_type = validate_phone("+49211123456")
        assert is_valid is True
        assert phone_type == "landline"
        
        is_valid, phone_type = validate_phone("0211 123456")
        assert is_valid is True
        assert phone_type == "landline"
    
    def test_invalid_phone_too_short(self):
        """Test rejection of too short numbers."""
        is_valid, phone_type = validate_phone("123")
        assert is_valid is False
        assert phone_type == "invalid"
        
        is_valid, phone_type = validate_phone("0211 123")
        assert is_valid is False
        assert phone_type == "invalid"
    
    def test_invalid_phone_too_long(self):
        """Test rejection of too long numbers."""
        is_valid, phone_type = validate_phone("12345678901234567890")
        assert is_valid is False
        assert phone_type == "invalid"
    
    def test_invalid_phone_null_empty(self):
        """Test rejection of null/empty phones."""
        is_valid, phone_type = validate_phone(None)
        assert is_valid is False
        assert phone_type == "invalid"
        
        is_valid, phone_type = validate_phone("")
        assert is_valid is False
        assert phone_type == "invalid"
    
    def test_international_numbers(self):
        """Test international phone numbers."""
        is_valid, phone_type = validate_phone("+33612345678")
        assert is_valid is True
        assert phone_type == "international"
        
        is_valid, phone_type = validate_phone("+441234567890")
        assert is_valid is True
        assert phone_type == "international"
    
    def test_phone_normalization(self):
        """Test phone normalization."""
        assert normalize_phone("0211 123456") == "+49211123456"
        assert normalize_phone("+49 (0) 211-123456") == "+49211123456"
        assert normalize_phone("0049 (0)176 123 45 67") == "+491761234567"
        assert normalize_phone("+49-(0)-176 123 45 67") == "+491761234567"


class TestDropperBehaviors:
    """Test dropper behaviors according to requirements."""
    
    def test_drop_no_phone(self):
        """Test drop when no valid phone."""
        lead = {"email": "someone@example.com", "telefon": ""}
        drop, reason = should_drop_lead(lead, "https://example.com/profile", "Kontakt")
        assert drop is True
        assert reason == "no_phone"
    
    def test_drop_invalid_phone(self):
        """Test drop when phone is invalid."""
        lead = {"email": "someone@example.com", "telefon": "123"}
        drop, reason = should_drop_lead(lead, "https://example.com/profile", "Kontakt")
        assert drop is True
        assert reason == "no_phone"
    
    def test_keep_valid_phone(self):
        """Test keep when valid phone."""
        lead = {"email": "someone@example.com", "telefon": "+491761234567"}
        drop, reason = should_drop_lead(lead, "https://example.com/profile", "Kontakt")
        # Should not drop for no_phone reason
        assert not (drop is True and reason == "no_phone")
    
    def test_drop_portal_domain_email(self):
        """Test drop when email from portal domain."""
        lead = {"email": "person@stepstone.de", "telefon": "+491761234567"}
        drop, reason = should_drop_lead(lead, "https://example.com/profile", "profile text")
        assert drop is True
        assert reason == "portal_domain"
    
    def test_drop_generic_mailbox(self):
        """Test drop when generic mailbox."""
        lead = {"email": "info@example.com", "telefon": "+491761234567"}
        drop, reason = should_drop_lead(lead, "https://example.com/profile", "profile text")
        assert drop is True
        assert reason == "generic_mailbox"
    
    def test_drop_pdf_without_cv_hint(self, monkeypatch):
        """Test drop PDF without CV hint."""
        import scriptname
        monkeypatch.setattr(scriptname, "ALLOW_PDF_NON_CV", False)
        lead = {"email": "user@example.com", "telefon": "+491761234567"}
        drop, reason = should_drop_lead(lead, "https://example.com/brochure.pdf", "Produktuebersicht")
        assert drop is True
        assert reason == "pdf_without_cv_hint"
    
    def test_keep_pdf_with_cv_hint(self, monkeypatch):
        """Test keep PDF with CV hint."""
        import scriptname
        monkeypatch.setattr(scriptname, "ALLOW_PDF_NON_CV", False)
        lead = {"email": "user@example.com", "telefon": "+491761234567"}
        drop, reason = should_drop_lead(lead, "https://example.com/cv.pdf", "Lebenslauf Sales")
        assert drop is False
        assert reason == ""


class TestScoringTiers:
    """Test scoring tiers and bonuses."""
    
    def test_no_phone_penalty(self):
        """Test -100 penalty for no phone."""
        text = "Sales profile"
        url = "https://example.com/profile"
        lead = {"email": "alice@example.com", "telefon": ""}
        score = se.compute_score_v2(text, url, lead)
        # Should have strong negative penalty
        assert score <= 10  # Very low score due to -100 penalty
    
    def test_whatsapp_bonus(self):
        """Test +15 bonus for WhatsApp."""
        text = "Sales profile wa.me/491234567890"
        url = "https://example.com/profile"
        lead = {"telefon": "+491761234567", "email": "alice@example.com"}
        score_with_wa = se.compute_score_v2(text, url, lead)
        
        text_no_wa = "Sales profile"
        score_without_wa = se.compute_score_v2(text_no_wa, url, lead)
        
        # Should have +15 bonus
        assert score_with_wa >= score_without_wa + 10  # At least +10 to account for rounding
    
    def test_email_tier_ordering(self):
        """Test email tier bonuses: corporate > free > generic > portal."""
        text = "Sales profile"
        url = "https://example.com/profile"
        base_lead = {"telefon": "+491761234567"}
        
        corp = dict(base_lead, email="alice@company.com")
        free = dict(base_lead, email="bob@gmail.com")
        generic = dict(base_lead, email="info@company.com")
        portal = dict(base_lead, email="carol@stepstone.de")
        
        score_corp = se.compute_score_v2(text, url, corp)
        score_free = se.compute_score_v2(text, url, free)
        score_generic = se.compute_score_v2(text, url, generic)
        score_portal = se.compute_score_v2(text, url, portal)
        
        # Corporate should be highest
        assert score_corp > score_free
        assert score_free > score_generic
        assert score_generic > score_portal
    
    def test_url_penalties(self):
        """Test URL penalties."""
        text = "Profile"
        base_lead = {"telefon": "+491761234567", "email": "alice@example.com"}
        
        # Impressum penalty -20
        score_impressum = se.compute_score_v2(text, "https://example.com/impressum", base_lead)
        score_normal = se.compute_score_v2(text, "https://example.com/profile", base_lead)
        assert score_normal > score_impressum
        
        # Job path penalty -15
        score_jobs = se.compute_score_v2(text, "https://example.com/jobs/developer", base_lead)
        assert score_normal > score_jobs
        
        # Portal host penalty -25
        score_portal = se.compute_score_v2(text, "https://stepstone.de/profile", base_lead)
        assert score_normal > score_portal


class TestDynamicThreshold:
    """Test dynamic threshold behavior."""
    
    def test_median_for_small_sample(self):
        """Test median used for n<8."""
        leads = [
            {"telefon": "+491761234567", "quelle": "https://example.com/1", "score": 10},
            {"telefon": "+491761234567", "quelle": "https://example.com/2", "score": 20},
            {"telefon": "+491761234567", "quelle": "https://example.com/3", "score": 30},
            {"telefon": "+491761234567", "quelle": "https://example.com/4", "score": 40},
            {"telefon": "+491761234567", "quelle": "https://example.com/5", "score": 50},
        ]
        
        filtered, info = se.apply_dynamic_threshold(leads)
        
        # Should use median (30)
        assert info["threshold"] == 30
        assert info["removed_reason"] == "below_dynamic"
    
    def test_q1_plus_5_for_large_sample(self):
        """Test Q1+5 used for n>=8."""
        leads = [
            {"telefon": "+491761234567", "quelle": f"https://example.com/{i}", "score": i * 10}
            for i in range(1, 11)
        ]
        
        filtered, info = se.apply_dynamic_threshold(leads)
        
        # Should use Q1+5 (not median)
        assert info["threshold"] > 0
        assert info["removed_reason"] == "below_dynamic"
        # Q1 of [10,20,30,40,50,60,70,80,90,100] is ~27.5, so threshold ~32-33
        assert 25 <= info["threshold"] <= 40


class TestHostBackoff:
    """Test host backoff TTL logic."""
    
    def test_backoff_set_duration(self):
        """Test backoff sets 7-day TTL."""
        metrics = MetricsStore(":memory:")
        host = "example.com"
        
        metrics.set_host_backoff(host, duration_seconds=604800)
        h = metrics.get_host_metrics(host)
        
        assert h.is_backedoff()
        # Check TTL is approximately 7 days
        time_until = h.backoff_until - time.time()
        assert 604790 <= time_until <= 604810
    
    def test_backoff_trigger_on_high_drop_rate(self):
        """Test backoff triggered when drop rate > 0.8."""
        h = HostMetrics(host="example.com", hits_total=10)
        h.drops_by_reason["no_phone"] = 9
        
        assert h.should_backoff(threshold=0.8) is True
    
    def test_backoff_not_triggered_below_threshold(self):
        """Test backoff not triggered when drop rate < 0.8."""
        h = HostMetrics(host="example.com", hits_total=10)
        h.drops_by_reason["no_phone"] = 5
        
        assert h.should_backoff(threshold=0.8) is False
    
    def test_backoff_bad_reasons(self):
        """Test backoff triggered by specific bad reasons."""
        h = HostMetrics(host="example.com", hits_total=10)
        h.drops_by_reason["portal_domain"] = 9
        
        assert h.should_backoff(threshold=0.8) is True
    
    def test_backoff_expires(self):
        """Test backoff expires after TTL."""
        h = HostMetrics(host="example.com")
        h.backoff_until = time.time() - 1  # Expired 1 second ago
        
        assert h.is_backedoff() is False


class TestWasserfallModeTransitions:
    """Test Wasserfall mode transitions."""
    
    def test_initial_conservative_mode(self):
        """Test starts in conservative mode."""
        metrics = MetricsStore(":memory:")
        wasserfall = WasserfallManager(metrics, initial_mode="conservative")
        
        mode = wasserfall.get_current_mode()
        assert mode.name == "conservative"
        assert mode.ddg_bucket_rate == 15
    
    def test_transition_up_conservative_to_moderate(self):
        """Test transition from conservative to moderate."""
        metrics = MetricsStore(":memory:")
        # Add some good metrics
        for i in range(5):
            metrics.record_query(f"dork{i}")
            metrics.record_url_fetch(f"dork{i}", f"example{i}.com")
            metrics.record_lead_found(f"dork{i}")
            metrics.record_accepted_lead(f"dork{i}")
        
        wasserfall = WasserfallManager(
            metrics,
            initial_mode="conservative",
            phone_find_rate_threshold=0.20,
            min_runs_for_transition=3
        )
        wasserfall.run_count = 3
        
        # Should transition up
        assert wasserfall.should_transition_up() is True
        new_mode = wasserfall.transition_mode("up", "Good metrics")
        assert new_mode.name == "moderate"
        assert new_mode.ddg_bucket_rate == 30
    
    def test_transition_down_on_poor_metrics(self):
        """Test transition down when metrics degrade."""
        metrics = MetricsStore(":memory:")
        # Add poor metrics (low phone find rate)
        for i in range(10):
            metrics.record_query(f"dork{i}")
            metrics.record_url_fetch(f"dork{i}", f"example{i}.com")
            # No leads found
        
        wasserfall = WasserfallManager(
            metrics,
            initial_mode="moderate",
            phone_find_rate_threshold=0.25,
            min_runs_for_transition=2
        )
        wasserfall.run_count = 2
        
        # Should transition down
        assert wasserfall.should_transition_down() is True
        new_mode = wasserfall.transition_mode("down", "Poor metrics")
        assert new_mode.name == "conservative"
        assert new_mode.ddg_bucket_rate == 15
    
    def test_no_transition_at_boundary(self):
        """Test no transition when at mode boundary."""
        metrics = MetricsStore(":memory:")
        wasserfall = WasserfallManager(metrics, initial_mode="aggressive")
        
        # Can't go up from aggressive
        new_mode = wasserfall.transition_mode("up", "Test")
        assert new_mode is None
        
        # Still aggressive
        assert wasserfall.get_current_mode().name == "aggressive"
    
    def test_mode_bucket_settings(self):
        """Test mode bucket rate settings."""
        metrics = MetricsStore(":memory:")
        
        # Conservative
        w_cons = WasserfallManager(metrics, initial_mode="conservative")
        assert w_cons.get_current_mode().ddg_bucket_rate == 15
        assert w_cons.get_current_mode().explore_rate == 0.20
        
        # Moderate
        w_mod = WasserfallManager(metrics, initial_mode="moderate")
        assert w_mod.get_current_mode().ddg_bucket_rate == 30
        assert w_mod.get_current_mode().explore_rate == 0.15
        
        # Aggressive
        w_agg = WasserfallManager(metrics, initial_mode="aggressive")
        assert w_agg.get_current_mode().ddg_bucket_rate == 50
        assert w_agg.get_current_mode().explore_rate == 0.10
