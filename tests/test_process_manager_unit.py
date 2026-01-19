"""
Comprehensive unit tests for ProcessManager.

Tests cover:
- Process lifecycle (start, stop, status)
- Command building with various parameters
- Early exit detection and error handling
- Singleton pattern
- Log handling
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "telis.settings")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Mark all tests as Django tests
pytestmark = pytest.mark.django


class TestProcessManagerSingleton:
    """Test the singleton pattern of ProcessManager."""

    def test_singleton_returns_same_instance(self):
        """Test that ProcessManager returns the same instance."""
        from scraper_control.process_manager import ProcessManager

        # Reset singleton for clean test
        ProcessManager._instance = None

        manager1 = ProcessManager()
        manager2 = ProcessManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    def test_get_manager_returns_global_instance(self):
        """Test that get_manager returns consistent global instance."""
        from scraper_control.process_manager import get_manager, ProcessManager

        # Reset singleton
        ProcessManager._instance = None

        manager1 = get_manager()
        manager2 = get_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ProcessManager)


class TestProcessManagerCommandBuilding:
    """Test command building logic of ProcessManager."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        return ProcessManager()

    def test_build_command_basic_module(self, manager):
        """Test building a basic command for module execution."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert cmd[:3] == ["python", "-m", "luca_scraper"]
        assert "--industry" in cmd
        assert "recruiter" in cmd
        assert "--qpi" in cmd
        assert "15" in cmd
        assert "--once" in cmd

    def test_build_command_basic_script(self, manager):
        """Test building a basic command for script execution."""
        params = {
            "industry": "candidates",
            "qpi": 20,
            "once": True,
        }

        cmd = manager._build_command(params, "script", "/path/to/scriptname.py")

        assert cmd[:2] == ["python", "/path/to/scriptname.py"]
        assert "--industry" in cmd
        assert "candidates" in cmd

    def test_build_command_with_all_flags(self, manager):
        """Test building command with all boolean flags."""
        params = {
            "industry": "recruiter",
            "qpi": 10,
            "mode": "learning",
            "smart": True,
            "force": True,
            "once": True,
            "dry_run": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--smart" in cmd
        assert "--force" in cmd
        assert "--once" in cmd
        assert "--dry-run" in cmd
        assert "--mode" in cmd
        assert "learning" in cmd

    def test_build_command_standard_mode_omitted(self, manager):
        """Test that standard mode is not explicitly added (it's the default)."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "mode": "standard",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--mode" not in cmd
        assert "standard" not in cmd

    def test_build_command_learning_mode_included(self, manager):
        """Test that learning mode is properly included."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "mode": "learning",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--mode" in cmd
        mode_idx = cmd.index("--mode")
        assert cmd[mode_idx + 1] == "learning"

    def test_build_command_aggressive_mode_included(self, manager):
        """Test that aggressive mode is properly included."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "mode": "aggressive",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--mode" in cmd
        mode_idx = cmd.index("--mode")
        assert cmd[mode_idx + 1] == "aggressive"

    def test_build_command_snippet_only_mode_included(self, manager):
        """Test that snippet_only mode is properly included."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "mode": "snippet_only",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--mode" in cmd
        mode_idx = cmd.index("--mode")
        assert cmd[mode_idx + 1] == "snippet_only"

    def test_build_command_invalid_mode_skipped(self, manager):
        """Test that invalid mode is skipped."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "mode": "invalid_mode",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        # Invalid mode should not be included
        assert "invalid_mode" not in cmd
        # --mode flag should not be present for invalid modes
        assert "--mode" not in cmd

    def test_build_command_with_daterestrict(self, manager):
        """Test that daterestrict is properly added."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "daterestrict": "d30",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--daterestrict" in cmd
        dr_idx = cmd.index("--daterestrict")
        assert cmd[dr_idx + 1] == "d30"

    def test_build_command_daterestrict_whitespace_stripped(self, manager):
        """Test that daterestrict whitespace is stripped."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "daterestrict": "  d30  ",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--daterestrict" in cmd
        dr_idx = cmd.index("--daterestrict")
        assert cmd[dr_idx + 1] == "d30"
        assert "  d30  " not in " ".join(cmd)

    def test_build_command_empty_daterestrict_omitted(self, manager):
        """Test that empty daterestrict is not added."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "daterestrict": "",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--daterestrict" not in cmd

    def test_build_command_whitespace_only_daterestrict_omitted(self, manager):
        """Test that whitespace-only daterestrict is not added."""
        params = {
            "industry": "recruiter",
            "qpi": 15,
            "daterestrict": "   ",
            "once": True,
        }

        cmd = manager._build_command(params, "module", "luca_scraper")

        assert "--daterestrict" not in cmd

    def test_build_command_all_industries(self, manager):
        """Test command building with various industries."""
        industries = [
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

        for industry in industries:
            params = {
                "industry": industry,
                "qpi": 15,
                "once": True,
            }

            cmd = manager._build_command(params, "module", "luca_scraper")

            assert "--industry" in cmd
            ind_idx = cmd.index("--industry")
            assert cmd[ind_idx + 1] == industry

    def test_build_command_qpi_values(self, manager):
        """Test command building with various QPI values."""
        for qpi in [1, 5, 15, 50, 100]:
            params = {
                "industry": "recruiter",
                "qpi": qpi,
                "once": True,
            }

            cmd = manager._build_command(params, "module", "luca_scraper")

            assert "--qpi" in cmd
            qpi_idx = cmd.index("--qpi")
            assert cmd[qpi_idx + 1] == str(qpi)

    def test_build_command_defaults(self, manager):
        """Test command building with minimal params (uses defaults)."""
        params = {}

        cmd = manager._build_command(params, "module", "luca_scraper")

        # Should have default industry
        assert "--industry" in cmd
        ind_idx = cmd.index("--industry")
        assert cmd[ind_idx + 1] == "recruiter"

        # Should have default qpi
        assert "--qpi" in cmd
        qpi_idx = cmd.index("--qpi")
        assert cmd[qpi_idx + 1] == "15"


class TestProcessManagerIsRunning:
    """Test the is_running method of ProcessManager."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        mgr = ProcessManager()
        # Reset state
        mgr.process = None
        mgr.pid = None
        mgr.status = "stopped"
        return mgr

    def test_is_running_when_no_process(self, manager):
        """Test is_running returns False when no process."""
        assert manager.is_running() is False

    def test_is_running_when_process_running(self, manager):
        """Test is_running returns True when process is running."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # None means still running

        manager.process = mock_process

        assert manager.is_running() is True

    def test_is_running_when_process_finished(self, manager):
        """Test is_running returns False when process has finished."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Exit code 0

        manager.process = mock_process
        manager.pid = None

        assert manager.is_running() is False

    @patch("scraper_control.process_manager.psutil.Process")
    def test_is_running_checks_pid_with_psutil(self, mock_psutil, manager):
        """Test is_running uses psutil to check PID when process object is None."""
        mock_proc = MagicMock()
        mock_proc.is_running.return_value = True
        mock_psutil.return_value = mock_proc

        manager.process = None
        manager.pid = 12345

        assert manager.is_running() is True
        mock_psutil.assert_called_once_with(12345)

    @patch("scraper_control.process_manager.psutil.Process")
    def test_is_running_handles_no_such_process(self, mock_psutil, manager):
        """Test is_running handles NoSuchProcess exception."""
        import psutil

        mock_psutil.side_effect = psutil.NoSuchProcess(12345)

        manager.process = None
        manager.pid = 12345

        assert manager.is_running() is False


class TestProcessManagerGetStatus:
    """Test the get_status method of ProcessManager."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        mgr = ProcessManager()
        mgr.process = None
        mgr.pid = None
        mgr.status = "stopped"
        mgr.params = {}
        mgr.start_time = None
        mgr.current_run_id = None
        return mgr

    def test_get_status_when_stopped(self, manager):
        """Test get_status when scraper is stopped."""
        status = manager.get_status()

        assert status["status"] == "stopped"
        assert status["pid"] is None
        assert status["run_id"] is None
        assert status["params"] == {}

    def test_get_status_when_running(self, manager):
        """Test get_status when scraper is running."""
        from django.utils import timezone

        mock_process = MagicMock()
        mock_process.poll.return_value = None

        manager.process = mock_process
        manager.pid = 12345
        manager.status = "running"
        manager.start_time = timezone.now()
        manager.params = {"industry": "recruiter", "qpi": 15}
        manager.current_run_id = 1

        status = manager.get_status()

        assert status["status"] == "running"
        assert status["pid"] == 12345
        assert status["run_id"] == 1
        assert status["params"]["industry"] == "recruiter"
        assert "uptime_seconds" in status
        assert "start_time" in status

    def test_get_status_detects_finished_process(self, manager):
        """Test get_status detects when process has finished."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process finished

        manager.process = mock_process
        manager.pid = 12345
        manager.status = "running"

        status = manager.get_status()

        # Should detect process finished and update status
        assert manager.status == "stopped"
        assert manager.pid is None


class TestProcessManagerGetLogs:
    """Test the get_logs method of ProcessManager."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        mgr = ProcessManager()
        mgr.logs = []
        return mgr

    def test_get_logs_empty(self, manager):
        """Test get_logs when no logs exist."""
        logs = manager.get_logs()
        assert logs == []

    def test_get_logs_returns_recent(self, manager):
        """Test get_logs returns recent log entries."""
        manager.logs = [
            {"timestamp": "2024-01-01T00:00:00", "message": "Log 1"},
            {"timestamp": "2024-01-01T00:00:01", "message": "Log 2"},
            {"timestamp": "2024-01-01T00:00:02", "message": "Log 3"},
        ]

        logs = manager.get_logs(lines=2)

        assert len(logs) == 2
        # Should return last 2 logs
        assert logs[0]["message"] == "Log 2"
        assert logs[1]["message"] == "Log 3"

    def test_get_logs_default_limit(self, manager):
        """Test get_logs uses default limit of 100."""
        manager.logs = [
            {"timestamp": f"2024-01-01T00:00:{i:02d}", "message": f"Log {i}"}
            for i in range(150)
        ]

        logs = manager.get_logs()

        assert len(logs) == 100


class TestProcessManagerFindScript:
    """Test the _find_scraper_script method."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        return ProcessManager()

    @patch("os.path.exists")
    def test_find_script_priority_scriptname(self, mock_exists, manager):
        """Test that scriptname.py has priority."""

        def exists_side_effect(path):
            return "scriptname.py" in path and "backup" not in path

        mock_exists.side_effect = exists_side_effect

        script_type, script_path = manager._find_scraper_script()

        assert script_type == "script"
        assert "scriptname.py" in script_path

    @patch("os.path.exists")
    def test_find_script_fallback_to_module(self, mock_exists, manager):
        """Test fallback to luca_scraper module when scriptname.py not found."""

        def exists_side_effect(path):
            return "__main__.py" in path

        mock_exists.side_effect = exists_side_effect

        script_type, script_path = manager._find_scraper_script()

        assert script_type == "module"
        assert script_path == "luca_scraper"

    @patch("os.path.exists")
    def test_find_script_none_found(self, mock_exists, manager):
        """Test when no script is found."""
        mock_exists.return_value = False

        script_type, script_path = manager._find_scraper_script()

        assert script_type is None
        assert script_path is None


class TestProcessManagerStart:
    """Test the start method of ProcessManager."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        mgr = ProcessManager()
        mgr.process = None
        mgr.pid = None
        mgr.status = "stopped"
        return mgr

    @patch.object(
        MagicMock,
        "is_running",
        return_value=True,
    )
    def test_start_fails_when_already_running(self, manager):
        """Test start fails when scraper is already running."""
        # Mock is_running to return True
        with patch.object(manager, "is_running", return_value=True):
            result = manager.start({"industry": "recruiter", "qpi": 15})

            assert result["success"] is False
            assert "bereits" in result["error"] or "already" in result.get(
                "error", ""
            ).lower()

    @patch("scraper_control.process_manager.ProcessManager._find_scraper_script")
    def test_start_fails_when_script_not_found(self, mock_find, manager):
        """Test start fails when scraper script not found."""
        mock_find.return_value = (None, None)

        with patch.object(manager, "is_running", return_value=False):
            with patch("scraper_control.process_manager.ScraperConfig") as mock_config:
                mock_config.get_config.return_value = MagicMock()

                with patch(
                    "scraper_control.process_manager.ScraperRun"
                ) as mock_run_class:
                    mock_run = MagicMock()
                    mock_run.id = 1
                    mock_run_class.objects.create.return_value = mock_run

                    result = manager.start({"industry": "recruiter", "qpi": 15})

                    assert result["success"] is False
                    assert "nicht gefunden" in result["error"]


class TestProcessManagerStop:
    """Test the stop method of ProcessManager."""

    @pytest.fixture
    def manager(self):
        """Get a fresh ProcessManager instance for testing."""
        from scraper_control.process_manager import ProcessManager

        ProcessManager._instance = None
        mgr = ProcessManager()
        mgr.process = None
        mgr.pid = None
        mgr.status = "stopped"
        return mgr

    def test_stop_fails_when_not_running(self, manager):
        """Test stop fails when no scraper is running."""
        with patch.object(manager, "is_running", return_value=False):
            result = manager.stop()

            assert result["success"] is False
            assert "Kein" in result["error"]

    def test_stop_terminates_process(self, manager):
        """Test stop properly terminates the process."""
        mock_process = MagicMock()
        mock_process.wait.return_value = 0

        manager.process = mock_process
        manager.pid = 12345
        manager.status = "running"

        with patch.object(manager, "is_running", return_value=True):
            with patch("scraper_control.process_manager.psutil.Process"):
                result = manager.stop()

                assert result["success"] is True
                mock_process.terminate.assert_called_once()


class TestLogEventCodes:
    """Test the structured log event codes."""

    def test_log_event_codes_exist(self):
        """Test that all expected log event codes exist."""
        from scraper_control.log_codes import LogEvent

        expected_events = [
            "SCRAPER_START",
            "SCRAPER_STOP",
            "SCRAPER_CRASH",
            "CRAWL_START",
            "CRAWL_COMPLETE",
            "EXTRACTION_SUCCESS",
            "EXTRACTION_FAIL",
            "HTTP_ERROR",
            "HTTP_TIMEOUT",
            "HTTP_RATE_LIMIT",
            "CB_TRIGGERED",
            "CB_RESET",
            "LEAD_SAVED",
            "VALIDATION_FAIL",
        ]

        for event_name in expected_events:
            assert hasattr(LogEvent, event_name), f"LogEvent.{event_name} should exist"

    def test_log_event_has_code_property(self):
        """Test that LogEvent has code property."""
        from scraper_control.log_codes import LogEvent

        event = LogEvent.CRAWL_START
        assert event.code == "CRAWL_START"

    def test_log_event_has_level_property(self):
        """Test that LogEvent has level property."""
        from scraper_control.log_codes import LogEvent, LogLevel

        event = LogEvent.EXTRACTION_FAIL
        assert event.level == LogLevel.ERROR

    def test_log_event_has_category_property(self):
        """Test that LogEvent has category property."""
        from scraper_control.log_codes import LogEvent, LogCategory

        event = LogEvent.HTTP_TIMEOUT
        assert event.category == LogCategory.NETWORK

    def test_format_structured_log(self):
        """Test format_structured_log helper function."""
        from scraper_control.log_codes import LogEvent, format_structured_log

        log_data = format_structured_log(
            LogEvent.EXTRACTION_FAIL,
            "Could not parse contact info",
            portal="stepstone",
            url="https://example.com/job/123",
        )

        assert log_data["event_code"] == "EXTRACTION_FAIL"
        assert "[EXTRACTION_FAIL]" in log_data["message"]
        assert log_data["portal"] == "stepstone"
        assert log_data["url"] == "https://example.com/job/123"
        assert log_data["level"] == "ERROR"
        assert log_data["event_category"] == "EXTRACTION"

    def test_format_structured_log_with_extra(self):
        """Test format_structured_log with extra data."""
        from scraper_control.log_codes import LogEvent, format_structured_log

        log_data = format_structured_log(
            LogEvent.LEAD_SAVED,
            "New lead saved",
            extra={"lead_id": 123, "score": 85},
        )

        assert log_data["lead_id"] == 123
        assert log_data["score"] == 85
