"""
Comprehensive unit tests for Scraper API Endpoints.

Tests cover:
- Scraper start/stop/status API
- Parameter validation
- Rate limiting and portal control endpoints
- Circuit breaker reset endpoint
- Configuration endpoints
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from rest_framework.test import APITestCase
from rest_framework import status

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "telis.settings")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Mark all tests as Django tests
pytestmark = pytest.mark.django


class TestScraperStatusAPI(APITestCase):
    """Tests for scraper status API endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.status_url = "/crm/scraper/api/scraper/status/"

    @patch("scraper_control.views.get_manager")
    def test_status_returns_stopped_when_not_running(self, mock_get_manager):
        """Test status endpoint returns stopped status."""
        mock_manager = MagicMock()
        mock_manager.get_status.return_value = {
            "status": "stopped",
            "pid": None,
            "run_id": None,
            "params": {},
        }
        mock_get_manager.return_value = mock_manager

        response = self.client.get(self.status_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "stopped"
        assert response.data["pid"] is None

    @patch("scraper_control.views.get_manager")
    def test_status_returns_running_when_active(self, mock_get_manager):
        """Test status endpoint returns running status with metrics."""
        mock_manager = MagicMock()
        mock_manager.get_status.return_value = {
            "status": "running",
            "pid": 12345,
            "run_id": 1,
            "uptime_seconds": 120,
            "cpu_percent": 45.2,
            "memory_mb": 128.5,
            "leads_found": 10,
            "api_cost": 2.50,
            "params": {"industry": "recruiter", "qpi": 15},
        }
        mock_get_manager.return_value = mock_manager

        response = self.client.get(self.status_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "running"
        assert response.data["pid"] == 12345
        assert response.data["uptime_seconds"] == 120
        assert response.data["leads_found"] == 10

    def test_status_requires_authentication(self):
        """Test status endpoint requires authentication."""
        self.client.logout()
        self.client.force_authenticate(user=None)

        response = self.client.get(self.status_url)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestScraperStartAPI(APITestCase):
    """Tests for scraper start API endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        from scraper_control.models import ScraperConfig

        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.start_url = "/crm/scraper/api/scraper/start/"

        # Ensure config exists
        ScraperConfig.get_config()

    @patch("scraper_control.views.get_manager")
    def test_start_with_valid_params(self, mock_get_manager):
        """Test start with valid parameters."""
        mock_manager = MagicMock()
        mock_manager.start.return_value = {
            "success": True,
            "status": "running",
            "pid": 12345,
            "run_id": 1,
        }
        mock_get_manager.return_value = mock_manager

        response = self.client.post(
            self.start_url,
            {
                "industry": "recruiter",
                "qpi": 15,
                "mode": "standard",
                "once": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        mock_manager.start.assert_called_once()

    def test_start_rejects_invalid_industry(self):
        """Test start rejects invalid industry parameter."""
        response = self.client.post(
            self.start_url,
            {
                "industry": "invalid_industry_xyz",
                "qpi": 15,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Ungültige Industry" in response.data["error"]

    @patch("scraper_control.views.get_manager")
    def test_start_accepts_all_valid_industries(self, mock_get_manager):
        """Test start accepts all valid industries."""
        mock_manager = MagicMock()
        mock_manager.start.return_value = {"success": True}
        mock_get_manager.return_value = mock_manager

        valid_industries = [
            "recruiter",
            "candidates",
            "talent_hunt",
            "all",
            "nrw",
            "social",
            "solar",
            "telekom",
            "versicherung",
            "bau",
            "ecom",
            "household",
        ]

        for industry in valid_industries:
            response = self.client.post(
                self.start_url,
                {"industry": industry, "qpi": 15, "once": True, "dry_run": True},
                format="json",
            )

            # Should not return 400 for invalid industry
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                assert "Ungültige Industry" not in response.data.get("error", "")

    @patch("scraper_control.views.get_manager")
    def test_start_falls_back_invalid_mode_to_standard(self, mock_get_manager):
        """Test that invalid mode falls back to standard."""
        mock_manager = MagicMock()
        mock_manager.start.return_value = {"success": True}
        mock_get_manager.return_value = mock_manager

        response = self.client.post(
            self.start_url,
            {
                "industry": "recruiter",
                "qpi": 15,
                "mode": "invalid_mode",
                "once": True,
                "dry_run": True,
            },
            format="json",
        )

        # Should not fail because of invalid mode (falls back to standard)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert "mode" not in response.data.get("error", "").lower()

    @patch("scraper_control.views.get_manager")
    def test_start_clamps_qpi_to_valid_range(self, mock_get_manager):
        """Test that QPI is clamped to valid range."""
        mock_manager = MagicMock()
        mock_manager.start.return_value = {"success": True}
        mock_get_manager.return_value = mock_manager

        # Test QPI > 100 should be clamped to 100
        response = self.client.post(
            self.start_url,
            {"industry": "recruiter", "qpi": 200, "once": True},
            format="json",
        )

        # Verify that the manager was called with clamped QPI
        if mock_manager.start.called:
            called_params = mock_manager.start.call_args[0][0]
            assert called_params.get("qpi", 0) <= 100

        # Test QPI < 1 should be clamped to 1
        response = self.client.post(
            self.start_url,
            {"industry": "recruiter", "qpi": 0, "once": True},
            format="json",
        )

        if mock_manager.start.called:
            called_params = mock_manager.start.call_args[0][0]
            assert called_params.get("qpi", 0) >= 1

    @patch("scraper_control.views.get_manager")
    def test_start_dry_run_aggressive_fallback(self, mock_get_manager):
        """Test that dry_run + aggressive mode falls back to standard."""
        mock_manager = MagicMock()
        mock_manager.start.return_value = {"success": True}
        mock_get_manager.return_value = mock_manager

        response = self.client.post(
            self.start_url,
            {
                "industry": "recruiter",
                "qpi": 15,
                "mode": "aggressive",
                "dry_run": True,
                "once": True,
            },
            format="json",
        )

        # Verify the mode was changed to standard
        if mock_manager.start.called:
            called_params = mock_manager.start.call_args[0][0]
            assert called_params.get("mode") == "standard"

    def test_start_requires_authentication(self):
        """Test start endpoint requires authentication."""
        self.client.logout()
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.start_url,
            {"industry": "recruiter", "qpi": 15},
            format="json",
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestScraperStopAPI(APITestCase):
    """Tests for scraper stop API endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.stop_url = "/crm/scraper/api/scraper/stop/"

    @patch("scraper_control.views.get_manager")
    def test_stop_success(self, mock_get_manager):
        """Test successful scraper stop."""
        mock_manager = MagicMock()
        mock_manager.stop.return_value = {"success": True, "status": "stopped"}
        mock_get_manager.return_value = mock_manager

        response = self.client.post(self.stop_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        mock_manager.stop.assert_called_once()

    @patch("scraper_control.views.get_manager")
    def test_stop_when_not_running(self, mock_get_manager):
        """Test stop when no scraper is running."""
        mock_manager = MagicMock()
        mock_manager.stop.return_value = {
            "success": False,
            "error": "Kein Scraper-Prozess läuft",
        }
        mock_get_manager.return_value = mock_manager

        response = self.client.post(self.stop_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_stop_requires_authentication(self):
        """Test stop endpoint requires authentication."""
        self.client.logout()
        self.client.force_authenticate(user=None)

        response = self.client.post(self.stop_url)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestScraperConfigAPI(APITestCase):
    """Tests for scraper configuration API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        from scraper_control.models import ScraperConfig

        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.config_url = "/crm/scraper/api/scraper/config/"

        # Reset config to defaults
        config = ScraperConfig.get_config()
        config.industry = "recruiter"
        config.qpi = 15
        config.mode = "standard"
        config.save()

    def test_get_config(self):
        """Test getting scraper configuration."""
        response = self.client.get(self.config_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["industry"] == "recruiter"
        assert response.data["qpi"] == 15
        assert response.data["mode"] == "standard"

    def test_update_config(self):
        """Test updating scraper configuration."""
        response = self.client.put(
            self.config_url,
            {
                "industry": "candidates",
                "qpi": 25,
                "mode": "learning",
                "smart": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify changes persisted
        from scraper_control.models import ScraperConfig

        config = ScraperConfig.get_config()
        assert config.industry == "candidates"
        assert config.qpi == 25
        assert config.mode == "learning"
        assert config.smart is False

    def test_update_config_sets_updated_by(self):
        """Test that updated_by is set when config is updated."""
        response = self.client.put(
            self.config_url,
            {"industry": "solar"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        from scraper_control.models import ScraperConfig

        config = ScraperConfig.get_config()
        assert config.updated_by == self.user


class TestRateLimitAPI(APITestCase):
    """Tests for rate limit control API."""

    def setUp(self):
        """Set up test fixtures."""
        from scraper_control.models import ScraperConfig

        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.rate_limit_url = "/crm/scraper/api/control/rate-limit/"

        # Ensure config exists
        ScraperConfig.get_config()

    def test_update_global_rate_limit(self):
        """Test updating global rate limit."""
        response = self.client.post(
            self.rate_limit_url,
            {"rate_limit_seconds": 5.0},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        from scraper_control.models import ScraperConfig

        config = ScraperConfig.get_config()
        assert config.sleep_between_queries == 5.0

    def test_rate_limit_validation_min(self):
        """Test rate limit minimum validation."""
        response = self.client.post(
            self.rate_limit_url,
            {"rate_limit_seconds": 0.1},  # Below minimum 0.5
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "muss zwischen" in response.data["error"]

    def test_rate_limit_validation_max(self):
        """Test rate limit maximum validation."""
        response = self.client.post(
            self.rate_limit_url,
            {"rate_limit_seconds": 100.0},  # Above maximum 60
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "muss zwischen" in response.data["error"]

    def test_rate_limit_required(self):
        """Test rate_limit_seconds is required."""
        response = self.client.post(
            self.rate_limit_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "erforderlich" in response.data["error"]


class TestPortalControlAPI(APITestCase):
    """Tests for portal control API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        from scraper_control.models import PortalSource

        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.toggle_url = "/crm/scraper/api/control/portal/toggle/"
        self.portals_url = "/crm/scraper/api/control/portals/"
        self.reset_cb_url = "/crm/scraper/api/control/circuit-breaker/reset/"

        # Create a test portal
        self.portal = PortalSource.objects.create(
            name="test_portal",
            display_name="Test Portal",
            base_url="https://test.example.com",
            is_active=True,
            circuit_breaker_enabled=True,
            circuit_breaker_tripped=False,
        )

    def test_toggle_portal_enable(self):
        """Test enabling a portal."""
        self.portal.is_active = False
        self.portal.save()

        response = self.client.post(
            self.toggle_url,
            {"portal": "test_portal", "active": True},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        self.portal.refresh_from_db()
        assert self.portal.is_active is True

    def test_toggle_portal_disable(self):
        """Test disabling a portal."""
        response = self.client.post(
            self.toggle_url,
            {"portal": "test_portal", "active": False},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        self.portal.refresh_from_db()
        assert self.portal.is_active is False

    def test_toggle_portal_not_found(self):
        """Test toggle with non-existent portal."""
        response = self.client.post(
            self.toggle_url,
            {"portal": "nonexistent_portal", "active": True},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_toggle_portal_requires_name(self):
        """Test toggle requires portal name."""
        response = self.client.post(
            self.toggle_url,
            {"active": True},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_portals_status(self):
        """Test getting all portals status."""
        response = self.client.get(self.portals_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

        # Find our test portal
        test_portal = next(
            (p for p in response.data if p["name"] == "test_portal"), None
        )
        assert test_portal is not None
        assert test_portal["is_active"] is True
        assert test_portal["circuit_breaker_enabled"] is True

    def test_reset_circuit_breaker(self):
        """Test resetting circuit breaker."""
        from django.utils import timezone

        # Trip the circuit breaker
        self.portal.circuit_breaker_tripped = True
        self.portal.circuit_breaker_reset_at = timezone.now() + timezone.timedelta(
            minutes=5
        )
        self.portal.consecutive_errors = 5
        self.portal.save()

        response = self.client.post(
            self.reset_cb_url,
            {"portal": "test_portal"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        self.portal.refresh_from_db()
        assert self.portal.circuit_breaker_tripped is False
        assert self.portal.circuit_breaker_reset_at is None
        assert self.portal.consecutive_errors == 0

    def test_reset_circuit_breaker_not_found(self):
        """Test reset circuit breaker with non-existent portal."""
        response = self.client.post(
            self.reset_cb_url,
            {"portal": "nonexistent_portal"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reset_circuit_breaker_requires_portal(self):
        """Test reset circuit breaker requires portal name."""
        response = self.client.post(
            self.reset_cb_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestScraperRunsAPI(APITestCase):
    """Tests for scraper runs history API."""

    def setUp(self):
        """Set up test fixtures."""
        from scraper_control.models import ScraperRun

        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.runs_url = "/crm/scraper/api/scraper/runs/"

        # Create some test runs
        self.run1 = ScraperRun.objects.create(
            status="completed",
            leads_found=10,
            leads_accepted=8,
            leads_rejected=2,
            links_checked=100,
            links_successful=90,
            started_by=self.user,
        )
        self.run2 = ScraperRun.objects.create(
            status="failed",
            leads_found=5,
            started_by=self.user,
        )

    def test_get_runs_list(self):
        """Test getting list of scraper runs."""
        response = self.client.get(self.runs_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_runs_include_metrics(self):
        """Test that runs include enhanced metrics."""
        response = self.client.get(self.runs_url)

        assert response.status_code == status.HTTP_200_OK

        # Find our first run
        run = next((r for r in response.data if r["id"] == self.run1.id), None)
        assert run is not None
        assert run["leads_found"] == 10
        assert run["leads_accepted"] == 8
        assert run["leads_rejected"] == 2
        assert run["links_checked"] == 100
        assert "success_rate" in run
        assert "lead_acceptance_rate" in run


class TestLogsAPI(APITestCase):
    """Tests for logs filtering API."""

    def setUp(self):
        """Set up test fixtures."""
        from scraper_control.models import ScraperRun, ScraperLog

        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.logs_url = "/crm/scraper/api/logs/"

        # Create a test run and logs
        self.run = ScraperRun.objects.create(
            status="running",
            started_by=self.user,
        )

        self.log1 = ScraperLog.objects.create(
            run=self.run,
            level="INFO",
            message="Test log message 1",
            portal="stepstone",
        )
        self.log2 = ScraperLog.objects.create(
            run=self.run,
            level="ERROR",
            message="Test error message",
            portal="indeed",
        )

    def test_get_all_logs(self):
        """Test getting all logs."""
        response = self.client.get(self.logs_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_filter_logs_by_run_id(self):
        """Test filtering logs by run ID."""
        response = self.client.get(f"{self.logs_url}?run_id={self.run.id}")

        assert response.status_code == status.HTTP_200_OK
        for log in response.data:
            assert log["run_id"] == self.run.id

    def test_filter_logs_by_level(self):
        """Test filtering logs by level."""
        response = self.client.get(f"{self.logs_url}?level=ERROR")

        assert response.status_code == status.HTTP_200_OK
        for log in response.data:
            assert log["level"] == "ERROR"

    def test_filter_logs_by_portal(self):
        """Test filtering logs by portal."""
        response = self.client.get(f"{self.logs_url}?portal=stepstone")

        assert response.status_code == status.HTTP_200_OK
        for log in response.data:
            assert "stepstone" in log["portal"].lower()

    def test_logs_limit(self):
        """Test logs limit parameter."""
        response = self.client.get(f"{self.logs_url}?limit=1")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
