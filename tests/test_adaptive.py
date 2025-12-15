"""
Tests for adaptive dork selection and Wasserfall mode management.
"""

import os
import tempfile
import pytest

# These imports will work when the modules are in place
from metrics import MetricsStore, DorkMetrics, HostMetrics
from adaptive_dorks import AdaptiveDorkSelector
from wasserfall import WasserfallManager, MODE_CONSERVATIVE, MODE_MODERATE, MODE_AGGRESSIVE


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def metrics_store(temp_db):
    """Create a metrics store for testing."""
    return MetricsStore(temp_db)


class TestMetricsStore:
    """Test metrics storage and retrieval."""
    
    def test_dork_metrics_creation(self, metrics_store):
        """Test creating and retrieving dork metrics."""
        m = metrics_store.get_dork_metrics("test dork")
        assert m.dork == "test dork"
        assert m.queries_total == 0
        assert m.score() == 0.0
    
    def test_dork_score_calculation(self, metrics_store):
        """Test dork score calculation."""
        m = metrics_store.get_dork_metrics("test dork")
        m.queries_total = 10
        m.accepted_leads = 5
        
        # Score = accepted_leads / queries_total
        assert m.score() == 0.5
    
    def test_dork_score_fallback(self, metrics_store):
        """Test dork score fallback to leads_kept."""
        m = metrics_store.get_dork_metrics("test dork")
        m.queries_total = 10
        m.leads_kept = 3
        m.accepted_leads = 0
        
        # Should use leads_kept when no accepted_leads
        assert m.score() == 0.3
    
    def test_host_metrics_drop_rate(self, metrics_store):
        """Test host drop rate calculation."""
        h = metrics_store.get_host_metrics("example.com")
        h.hits_total = 10
        h.drops_by_reason["no_phone"] = 8
        
        assert h.drop_rate() == 0.8
    
    def test_host_backoff_logic(self, metrics_store):
        """Test host backoff activation and expiry."""
        h = metrics_store.get_host_metrics("example.com")
        h.hits_total = 10
        h.drops_by_reason["no_phone"] = 9
        
        # Should trigger backoff
        assert h.should_backoff(threshold=0.8) is True
        
        # Set backoff
        metrics_store.set_host_backoff("example.com", duration_seconds=1)
        assert h.is_backedoff() is True
        
        # Wait for expiry (in real test, would sleep or mock time)
        import time
        time.sleep(1.1)
        assert h.is_backedoff() is False
    
    def test_metrics_persistence(self, temp_db):
        """Test that metrics persist across store instances."""
        # Create store and add metrics
        store1 = MetricsStore(temp_db)
        store1.record_query("test dork")
        store1.record_accepted_lead("test dork")
        store1.persist()
        
        # Create new store from same DB
        store2 = MetricsStore(temp_db)
        m = store2.get_dork_metrics("test dork")
        
        assert m.queries_total == 1
        assert m.accepted_leads == 1


class TestAdaptiveDorkSelector:
    """Test adaptive dork selection."""
    
    def test_initial_pool_creation(self, metrics_store):
        """Test initial core/explore pool creation."""
        dorks = [f"dork_{i}" for i in range(20)]
        selector = AdaptiveDorkSelector(metrics_store, dorks, explore_rate=0.2)
        
        # Should have core and explore pools
        assert len(selector.core_dorks) >= selector.min_core
        assert len(selector.explore_dorks) > 0
        assert len(selector.core_dorks) + len(selector.explore_dorks) == len(dorks)
    
    def test_dork_selection(self, metrics_store):
        """Test dork selection with ε-greedy."""
        dorks = [f"dork_{i}" for i in range(20)]
        
        # Add some metrics to make some dorks better
        for i in range(5):
            m = metrics_store.get_dork_metrics(f"dork_{i}")
            m.queries_total = 10
            m.accepted_leads = 5 + i  # Progressive improvement
        
        selector = AdaptiveDorkSelector(metrics_store, dorks, explore_rate=0.2)
        selected = selector.select_dorks(num_dorks=10, google_ratio=0.25)
        
        # Should select 10 dorks
        assert len(selected) == 10
        
        # Should have both core and explore
        core_count = sum(1 for d in selected if d["pool"] == "core")
        explore_count = sum(1 for d in selected if d["pool"] == "explore")
        assert core_count > 0
        assert explore_count > 0
        
        # Should assign sources (25% google, 75% ddg)
        google_count = sum(1 for d in selected if d["source"] == "google")
        ddg_count = sum(1 for d in selected if d["source"] == "ddg")
        assert google_count >= 2  # ~25% of 10
        assert ddg_count >= 7  # ~75% of 10
    
    def test_dork_promotion(self, metrics_store):
        """Test manual dork promotion."""
        dorks = [f"dork_{i}" for i in range(10)]
        selector = AdaptiveDorkSelector(metrics_store, dorks)
        
        # Find an explore dork
        if selector.explore_dorks:
            test_dork = selector.explore_dorks[0]
            selector.promote_to_core(test_dork)
            
            assert test_dork in selector.core_dorks
            assert test_dork not in selector.explore_dorks


class TestWasserfallManager:
    """Test Wasserfall mode management."""
    
    def test_initial_mode(self, metrics_store):
        """Test initial mode is conservative."""
        manager = WasserfallManager(metrics_store)
        
        assert manager.current_mode.name == "conservative"
        assert manager.current_mode.ddg_bucket_rate == 15
    
    def test_mode_transition_up(self, metrics_store):
        """Test transition to more aggressive mode."""
        manager = WasserfallManager(metrics_store, phone_find_rate_threshold=0.2)
        
        # Simulate good metrics
        for i in range(10):
            metrics_store.record_query(f"dork_{i}")
            metrics_store.record_url_fetch(f"dork_{i}", f"host_{i}")
            metrics_store.record_lead_found(f"dork_{i}")
            metrics_store.record_accepted_lead(f"dork_{i}")
        
        # Need min runs
        for _ in range(3):
            manager.increment_run()
        
        # Check if should transition
        assert manager.should_transition_up() is True
        
        # Do transition
        new_mode = manager.transition_mode("up", "test")
        
        assert new_mode is not None
        assert new_mode.name == "moderate"
        assert manager.current_mode.ddg_bucket_rate == 30
    
    def test_mode_transition_down(self, metrics_store):
        """Test transition to more conservative mode."""
        manager = WasserfallManager(
            metrics_store,
            initial_mode="aggressive",
            phone_find_rate_threshold=0.25
        )
        
        # Simulate bad metrics (lots of fetches, few leads)
        for i in range(100):
            metrics_store.record_url_fetch("dork_0", f"host_{i}")
            if i < 5:  # Only 5% success
                metrics_store.record_lead_found("dork_0")
        
        metrics_store.record_query("dork_0")
        
        manager.increment_run()
        manager.increment_run()
        
        # Should want to transition down
        assert manager.should_transition_down() is True
        
        # Do transition
        new_mode = manager.transition_mode("down", "poor performance")
        
        assert new_mode is not None
        assert new_mode.name == "moderate"
    
    def test_mode_boundaries(self, metrics_store):
        """Test that transitions respect mode boundaries."""
        # Conservative can't go down
        manager = WasserfallManager(metrics_store, initial_mode="conservative")
        result = manager.transition_mode("down", "test")
        assert result is None
        
        # Aggressive can't go up
        manager = WasserfallManager(metrics_store, initial_mode="aggressive")
        result = manager.transition_mode("up", "test")
        assert result is None
    
    def test_mode_status(self, metrics_store):
        """Test getting mode status."""
        manager = WasserfallManager(metrics_store)
        
        status = manager.get_status()
        
        assert "current_mode" in status
        assert "run_count" in status
        assert "phone_find_rate" in status
        assert status["current_mode"]["name"] == "conservative"
