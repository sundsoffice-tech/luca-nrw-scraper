# -*- coding: utf-8 -*-
"""
Tests für ML-basierte Extraktoren und Feedback-Loop-System.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stream2_extraction_layer.ml_extractors import (
    SimpleNERNameExtractor,
    MLPhoneExtractor,
    MLEmailClassifier,
    MLIndustryClassifier,
    get_name_extractor,
    get_email_classifier,
    get_industry_classifier,
)
from stream3_scoring_layer.feedback_loop import (
    FeedbackLoopSystem,
    FeedbackEntry,
    QualityMetrics,
)


class TestSimpleNERNameExtractor:
    """Tests für Namen-Extraktor."""
    
    def test_extract_name_with_context(self):
        extractor = SimpleNERNameExtractor()
        text = "Ihr Ansprechpartner: Max Mustermann kann Ihnen weiterhelfen."
        result = extractor.extract(text)
        
        assert result.value == "Max Mustermann"
        assert result.confidence > 0.5
        assert result.method == "ner_heuristic"
    
    def test_extract_name_with_title(self):
        extractor = SimpleNERNameExtractor()
        text = "Kontaktieren Sie Herrn Dr. Peter Schmidt für weitere Informationen."
        result = extractor.extract(text)
        
        assert result.value is not None
        assert "Schmidt" in result.value or "Peter" in result.value
        assert result.confidence > 0.4
    
    def test_no_name_found(self):
        extractor = SimpleNERNameExtractor()
        text = "Dies ist ein Text ohne Namen mit nur generischen Begriffen."
        result = extractor.extract(text)
        
        assert result.value is None
        assert result.confidence == 0.0
    
    def test_blacklist_filtering(self):
        extractor = SimpleNERNameExtractor()
        text = "Unser Ansprechpartner: Nordrhein Westfalen GmbH"
        result = extractor.extract(text)
        
        # Should not extract company names
        assert result.value is None or "GmbH" not in result.value


class TestMLPhoneExtractor:
    """Tests für Telefonnummer-Scoring."""
    
    def test_score_mobile_high_confidence(self):
        extractor = MLPhoneExtractor()
        phone = "+491751234567"
        raw = "0175 1234567"
        context = "Rufen Sie mich mobil an: 0175 1234567"
        
        score = extractor.score_phone(phone, raw, context)
        assert score > 0.6  # Should have high confidence
    
    def test_score_hotline_low_confidence(self):
        extractor = MLPhoneExtractor()
        phone = "+491751234567"
        raw = "0175 1234567"
        context = "Unsere Service-Hotline: 0175 1234567"
        
        score = extractor.score_phone(phone, raw, context)
        assert score < 0.6  # Should have lower confidence
    
    def test_mobile_bonus(self):
        extractor = MLPhoneExtractor()
        mobile = "+491751234567"
        landline = "+492211234567"
        context = "Telefon: "
        
        mobile_score = extractor.score_phone(mobile, mobile, context)
        landline_score = extractor.score_phone(landline, landline, context)
        
        assert mobile_score > landline_score


class TestMLEmailClassifier:
    """Tests für E-Mail-Klassifikator."""
    
    def test_classify_portal_email(self):
        classifier = MLEmailClassifier()
        result = classifier.classify("jobs@stepstone.de")
        
        assert result['category'] == 'portal'
        assert result['quality'] == 'very_low'
        assert result['score_modifier'] < 0
    
    def test_classify_generic_corporate(self):
        classifier = MLEmailClassifier()
        result = classifier.classify("info@firma.de")
        
        assert result['category'] == 'generic'
        assert result['quality'] == 'low'
    
    def test_classify_personal_corporate(self):
        classifier = MLEmailClassifier()
        result = classifier.classify("max.mustermann@firma.de")
        
        assert result['category'] == 'corporate_personal'
        assert result['quality'] == 'high'
        assert result['score_modifier'] > 0
    
    def test_classify_free_personal(self):
        classifier = MLEmailClassifier()
        result = classifier.classify("max.mustermann@gmail.com")
        
        assert result['category'] == 'free_personal'
        assert result['quality'] == 'medium'
    
    def test_is_personal_pattern(self):
        classifier = MLEmailClassifier()
        
        assert classifier._is_personal_pattern("max.mustermann")
        assert classifier._is_personal_pattern("m.mustermann")
        assert classifier._is_personal_pattern("max_mustermann")
        assert not classifier._is_personal_pattern("info")
        assert not classifier._is_personal_pattern("kontakt")


class TestMLIndustryClassifier:
    """Tests für Branchen-Klassifikator."""
    
    def test_classify_insurance(self):
        classifier = MLIndustryClassifier()
        text = "Wir sind ein Versicherungsmakler und suchen Vertriebsmitarbeiter für Versicherungsprodukte."
        industry, confidence = classifier.classify(text)
        
        assert industry == 'versicherung'
        assert confidence > 0.5
    
    def test_classify_energy(self):
        classifier = MLIndustryClassifier()
        text = "Stadtwerke sucht Mitarbeiter für Strom- und Gasvertrieb."
        industry, confidence = classifier.classify(text)
        
        assert industry == 'energie'
        assert confidence > 0.3
    
    def test_classify_recruiter(self):
        classifier = MLIndustryClassifier()
        text = "Personalberatung für IT-Recruiting und Headhunting."
        industry, confidence = classifier.classify(text)
        
        assert industry == 'recruiter'
        assert confidence > 0.3
    
    def test_no_industry_found(self):
        classifier = MLIndustryClassifier()
        text = "Dies ist ein generischer Text ohne Branchenbezug."
        industry, confidence = classifier.classify(text)
        
        assert industry is None
        assert confidence == 0.0
    
    def test_learn_from_feedback(self):
        classifier = MLIndustryClassifier()
        text = "Wir verkaufen innovative Solarpanels und Photovoltaik-Anlagen."
        
        # Initially might not classify correctly
        industry1, conf1 = classifier.classify(text)
        
        # Provide feedback
        classifier.learn_from_feedback(text, 'energie')
        classifier.learn_from_feedback(text + " Solarpanels", 'energie')
        classifier.learn_from_feedback(text + " Photovoltaik", 'energie')
        
        # After learning, should have new keywords
        assert 'solarpanels' in classifier.learning_data.get('energie', {})


class TestFeedbackLoopSystem:
    """Tests für Feedback-Loop-System."""
    
    @pytest.fixture
    def feedback_system(self, tmp_path):
        """Erstellt temporäres Feedback-System für Tests."""
        db_path = str(tmp_path / "test_feedback.db")
        return FeedbackLoopSystem(db_path)
    
    def test_record_feedback(self, feedback_system):
        feedback = FeedbackEntry(
            lead_id=1,
            feedback_type='quality',
            rating=0.8,
            user_id='test_user',
            notes='Good lead',
            metadata={'email_domain': 'firma.de', 'industry': 'versicherung'}
        )
        
        success = feedback_system.record_feedback(feedback)
        assert success
    
    def test_get_quality_metrics(self, feedback_system):
        # Add some feedback
        for i in range(5):
            feedback = FeedbackEntry(
                lead_id=i,
                feedback_type='quality',
                rating=0.7 + (i * 0.05),
            )
            feedback_system.record_feedback(feedback)
        
        metrics = feedback_system.get_quality_metrics(days=7)
        
        assert metrics.total_feedback == 5
        assert metrics.avg_rating > 0.7
        assert 0 <= metrics.positive_rate <= 1
    
    def test_dynamic_score_adjustment(self, feedback_system):
        # Record feedback with metadata
        feedback = FeedbackEntry(
            lead_id=1,
            feedback_type='quality',
            rating=0.9,
            metadata={'email_domain': 'goodcompany.de', 'industry': 'energie'}
        )
        feedback_system.record_feedback(feedback)
        
        # Get adjustment for similar lead
        lead = {
            'email': 'test@goodcompany.de',
            'industry': 'energie'
        }
        adjustment = feedback_system.get_dynamic_score_adjustment(lead)
        
        # Adjustment might be small initially, but should exist
        assert isinstance(adjustment, float)
    
    def test_record_extraction_accuracy(self, feedback_system):
        success = feedback_system.record_extraction_accuracy(
            lead_id=1,
            field_name='email',
            extracted='test@firma.de',
            correct='test@firma.de',
            confidence=0.9
        )
        assert success
        
        accuracy = feedback_system.get_field_accuracy('email', days=7)
        assert accuracy == 1.0  # 100% correct
    
    def test_record_quality_pattern(self, feedback_system):
        pattern_data = {
            'email_format': 'firstname.lastname',
            'domain_type': 'corporate'
        }
        
        # Record successful pattern
        feedback_system.record_quality_pattern('email_format', pattern_data, True)
        feedback_system.record_quality_pattern('email_format', pattern_data, True)
        feedback_system.record_quality_pattern('email_format', pattern_data, False)
        
        # Get best patterns
        patterns = feedback_system.get_best_patterns('email_format', min_samples=2)
        
        assert len(patterns) > 0
        pattern, success_rate = patterns[0]
        assert pattern == pattern_data
        assert 0 <= success_rate <= 1
    
    def test_feedback_summary(self, feedback_system):
        # Add some data
        for i in range(3):
            feedback = FeedbackEntry(
                lead_id=i,
                feedback_type='quality',
                rating=0.8,
                metadata={'industry': 'versicherung'}
            )
            feedback_system.record_feedback(feedback)
        
        summary = feedback_system.get_feedback_summary(days=7)
        
        assert 'quality_metrics' in summary
        assert 'active_adjustments' in summary
        assert 'field_accuracy' in summary
        assert isinstance(summary['quality_metrics'], dict)


class TestIntegration:
    """Integrationstests für ML-Komponenten."""
    
    def test_name_extractor_singleton(self):
        extractor1 = get_name_extractor()
        extractor2 = get_name_extractor()
        assert extractor1 is extractor2
    
    def test_email_classifier_singleton(self):
        classifier1 = get_email_classifier()
        classifier2 = get_email_classifier()
        assert classifier1 is classifier2
    
    def test_industry_classifier_singleton(self):
        classifier1 = get_industry_classifier()
        classifier2 = get_industry_classifier()
        assert classifier1 is classifier2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
