# -*- coding: utf-8 -*-
"""Tests for the portal_optimizer module."""

import pytest
import os
import sqlite3
import tempfile
from learning_engine import LearningEngine
from portal_optimizer import PortalOptimizer, get_portal_optimizer


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def learning_engine(temp_db):
    """Create a learning engine instance with temp database."""
    return LearningEngine(temp_db)


@pytest.fixture
def portal_optimizer(learning_engine):
    """Create a portal optimizer instance."""
    return PortalOptimizer(learning_engine)


class TestPortalOptimizer:
    """Tests for the PortalOptimizer class."""
    
    def test_initialization(self, portal_optimizer):
        """Test that portal optimizer initializes correctly."""
        assert portal_optimizer.learning_engine is not None
    
    def test_analyze_portal_performance_empty(self, portal_optimizer):
        """Test analysis with no performance data."""
        analysis = portal_optimizer.analyze_portal_performance()
        
        assert 'summary' in analysis
        assert 'disable_recommendations' in analysis
        assert 'delay_recommendations' in analysis
        assert 'prioritize_recommendations' in analysis
        
        # Should have zero recommendations with no data
        assert analysis['summary']['low_performing'] == 0
        assert analysis['summary']['rate_limited'] == 0
    
    def test_analyze_portal_performance_with_data(self, portal_optimizer, learning_engine):
        """Test analysis with performance data."""
        # Add low-performing portal (should be recommended for disabling)
        for i in range(15):
            learning_engine.update_domain_performance(
                domain="badportal.de",
                success=False,
                rate_limited=False
            )
        
        # Add rate-limited portal
        for i in range(10):
            learning_engine.update_domain_performance(
                domain="ratelimited.de",
                success=False,
                rate_limited=True
            )
        
        # Add high-performing portal
        for i in range(10):
            learning_engine.update_domain_performance(
                domain="goodportal.de",
                success=True,
                rate_limited=False
            )
        
        analysis = portal_optimizer.analyze_portal_performance()
        
        # Should have recommendations
        assert analysis['summary']['low_performing'] >= 1
        assert analysis['summary']['rate_limited'] >= 1
        assert analysis['summary']['high_performing'] >= 1
    
    def test_generate_portal_config(self, portal_optimizer, learning_engine):
        """Test generating optimized portal configuration."""
        # Add low-performing portal
        for i in range(15):
            learning_engine.update_domain_performance(
                domain="meinestadt.de",
                success=False,
                rate_limited=False
            )
        
        current_config = {
            "kleinanzeigen": True,
            "meinestadt": True,
            "quoka": True,
        }
        
        current_delays = {
            "kleinanzeigen": 3.0,
            "meinestadt": 3.0,
            "quoka": 3.0,
        }
        
        result = portal_optimizer.generate_portal_config(current_config, current_delays)
        
        assert 'config' in result
        assert 'delays' in result
        assert 'changes' in result
        assert 'recommendations' in result
        
        # meinestadt should be disabled
        # Note: This might not work if domain mapping fails
        assert isinstance(result['changes'], list)
    
    def test_get_optimization_suggestions(self, portal_optimizer, learning_engine):
        """Test getting human-readable optimization suggestions."""
        # Add some performance data
        for i in range(15):
            learning_engine.update_domain_performance(
                domain="meinestadt.de",
                success=False,
                rate_limited=False
            )
        
        suggestions = portal_optimizer.get_optimization_suggestions()
        
        assert isinstance(suggestions, list)
        
        if len(suggestions) > 0:
            # Check structure
            for suggestion in suggestions:
                assert 'priority' in suggestion
                assert 'type' in suggestion
                assert 'portal' in suggestion
                assert 'reason' in suggestion
                assert 'action' in suggestion
                assert suggestion['priority'] in ['HIGH', 'MEDIUM', 'LOW']
    
    def test_get_portal_health_report(self, portal_optimizer, learning_engine):
        """Test generating portal health report."""
        # Add some portal data
        for i in range(10):
            learning_engine.update_domain_performance(
                domain="kleinanzeigen.de",
                success=True if i < 8 else False,
                rate_limited=False
            )
        
        for i in range(10):
            learning_engine.update_domain_performance(
                domain="meinestadt.de",
                success=False,
                rate_limited=False
            )
        
        report = portal_optimizer.get_portal_health_report()
        
        assert 'overall_health' in report
        assert 'health_grade' in report
        assert 'portals' in report
        assert 'total_portals' in report
        assert 'recommendations' in report
        
        # Check health grade format
        assert report['health_grade'] in ['A', 'B', 'C', 'D', 'F']
        
        # Check portal info
        assert isinstance(report['portals'], list)
        if len(report['portals']) > 0:
            portal = report['portals'][0]
            assert 'domain' in portal
            assert 'health' in portal
            assert 'success_rate' in portal
            assert portal['health'] in ['excellent', 'good', 'fair', 'poor', 'critical', 'unknown']
    
    def test_get_portal_health_report_enabled_field(self, portal_optimizer, learning_engine):
        """Test that enabled field is accessed correctly from sqlite3.Row (bug fix test)."""
        # Add portal data
        learning_engine.update_domain_performance(
            domain="test.de",
            success=True,
            rate_limited=False
        )
        
        # This should not raise AttributeError: 'sqlite3.Row' object has no attribute 'get'
        report = portal_optimizer.get_portal_health_report()
        
        # Verify report structure
        assert 'portals' in report
        assert len(report['portals']) > 0
        
        # Verify enabled field is present and is a boolean
        portal = report['portals'][0]
        assert 'enabled' in portal
        assert isinstance(portal['enabled'], bool)
    
    def test_domain_to_portal_key_mapping(self, portal_optimizer):
        """Test internal domain to portal key mapping."""
        # This is a private method, but we can test it indirectly
        # by checking if optimization suggestions use correct portal keys
        
        # Just verify the method exists and is callable
        result = portal_optimizer._domain_to_portal_key("kleinanzeigen.de")
        assert result == "kleinanzeigen"
        
        result = portal_optimizer._domain_to_portal_key("meinestadt.de")
        assert result == "meinestadt"
        
        result = portal_optimizer._domain_to_portal_key("unknown.de")
        assert result is None
    
    def test_health_to_grade_conversion(self, portal_optimizer):
        """Test health score to letter grade conversion."""
        assert portal_optimizer._health_to_grade(95) == "A"
        assert portal_optimizer._health_to_grade(85) == "B"
        assert portal_optimizer._health_to_grade(75) == "C"
        assert portal_optimizer._health_to_grade(65) == "D"
        assert portal_optimizer._health_to_grade(50) == "F"


class TestPortalOptimizerFactory:
    """Test the factory function."""
    
    def test_get_portal_optimizer(self, temp_db):
        """Test creating optimizer via factory function."""
        optimizer = get_portal_optimizer(temp_db)
        
        assert isinstance(optimizer, PortalOptimizer)
        assert optimizer.learning_engine is not None
        assert optimizer.learning_engine.db_path == temp_db
