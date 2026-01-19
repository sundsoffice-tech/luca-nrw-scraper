"""
Test security configuration defaults for SSL validation.
Verifies that secure defaults are set for SSL certificate validation.
"""

import os
import pytest


class TestSSLSecurityDefaults:
    """Test that SSL security settings have secure defaults."""
    
    def test_allow_insecure_ssl_defaults_to_false(self):
        """Test that ALLOW_INSECURE_SSL defaults to False (secure)."""
        # Clear environment variable if set
        original_value = os.environ.get("ALLOW_INSECURE_SSL")
        if "ALLOW_INSECURE_SSL" in os.environ:
            del os.environ["ALLOW_INSECURE_SSL"]
        
        try:
            # Re-import to get fresh default
            import importlib
            import scriptname
            importlib.reload(scriptname)
            
            # Verify secure default (False/0)
            assert scriptname.ALLOW_INSECURE_SSL is False, \
                "ALLOW_INSECURE_SSL should default to False (secure mode)"
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["ALLOW_INSECURE_SSL"] = original_value
            elif "ALLOW_INSECURE_SSL" in os.environ:
                del os.environ["ALLOW_INSECURE_SSL"]
    
    def test_allow_insecure_ssl_can_be_enabled_explicitly(self):
        """Test that insecure SSL can be explicitly enabled for development."""
        # Set environment variable
        os.environ["ALLOW_INSECURE_SSL"] = "1"
        
        try:
            # Re-import to pick up environment change
            import importlib
            import scriptname
            importlib.reload(scriptname)
            
            # Verify it can be enabled when explicitly set
            assert scriptname.ALLOW_INSECURE_SSL is True, \
                "ALLOW_INSECURE_SSL should be True when explicitly set to '1'"
        finally:
            # Clean up
            del os.environ["ALLOW_INSECURE_SSL"]
    
    def test_scraper_config_defaults_to_secure(self):
        """Test that ScraperConfig dataclass defaults to secure SSL."""
        # Clear environment variable
        original_value = os.environ.get("ALLOW_INSECURE_SSL")
        if "ALLOW_INSECURE_SSL" in os.environ:
            del os.environ["ALLOW_INSECURE_SSL"]
        
        try:
            # Re-import
            import importlib
            import scriptname
            importlib.reload(scriptname)
            
            # Check CFG instance
            cfg = scriptname.ScraperConfig()
            assert cfg.allow_insecure_ssl is False, \
                "ScraperConfig.allow_insecure_ssl should default to False"
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["ALLOW_INSECURE_SSL"] = original_value


class TestProxyConfiguration:
    """Test proxy configuration security."""
    
    def test_proxy_env_vars_list_exists(self):
        """Test that proxy environment variables list is defined."""
        import scriptname
        
        assert hasattr(scriptname, "PROXY_ENV_VARS"), \
            "PROXY_ENV_VARS should be defined"
        
        assert isinstance(scriptname.PROXY_ENV_VARS, list), \
            "PROXY_ENV_VARS should be a list"
        
        # Check for common proxy variables
        expected_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
        for var in expected_vars:
            assert var in scriptname.PROXY_ENV_VARS, \
                f"PROXY_ENV_VARS should include {var}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
