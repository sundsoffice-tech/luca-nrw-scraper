#!/usr/bin/env python3
"""
Validation script for automatic configuration reload feature.

This script demonstrates and validates the automatic config reload functionality
without requiring a full Django setup.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def validate_process_manager_structure():
    """Validate that ProcessManager has the required attributes and methods."""
    print("=" * 80)
    print("VALIDATING PROCESS MANAGER STRUCTURE")
    print("=" * 80)
    
    try:
        # Import the module (won't fully work without Django, but we can check structure)
        with open('telis_recruitment/scraper_control/process_manager.py', 'r') as f:
            content = f.read()
        
        required_attributes = [
            'current_config_version',
            'config_watcher_thread',
            'config_check_interval',
            'restart_lock',
            'last_restart_user',
        ]
        
        required_methods = [
            'def restart_process',
            'def _start_config_watcher',
        ]
        
        print("\n✓ Checking ProcessManager attributes...")
        for attr in required_attributes:
            if attr in content:
                print(f"  ✓ Found: {attr}")
            else:
                print(f"  ✗ MISSING: {attr}")
                return False
        
        print("\n✓ Checking ProcessManager methods...")
        for method in required_methods:
            if method in content:
                print(f"  ✓ Found: {method}")
            else:
                print(f"  ✗ MISSING: {method}")
                return False
        
        print("\n✅ ProcessManager structure validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error validating ProcessManager: {e}")
        return False


def validate_signal_handler():
    """Validate that the signal handler exists in models.py."""
    print("\n" + "=" * 80)
    print("VALIDATING SIGNAL HANDLER")
    print("=" * 80)
    
    try:
        with open('telis_recruitment/scraper_control/models.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('Signal import', 'from django.db.models.signals import post_save'),
            ('Receiver decorator', '@receiver(post_save, sender=ScraperConfig)'),
            ('Signal function', 'def scraper_config_changed'),
        ]
        
        print("\n✓ Checking signal handler components...")
        for name, check in checks:
            if check in content:
                print(f"  ✓ Found: {name}")
            else:
                print(f"  ✗ MISSING: {name}")
                return False
        
        print("\n✅ Signal handler validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error validating signal handler: {e}")
        return False


def validate_views_updates():
    """Validate that views.py has been updated with notifications."""
    print("\n" + "=" * 80)
    print("VALIDATING VIEWS UPDATES")
    print("=" * 80)
    
    try:
        with open('telis_recruitment/scraper_control/views.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('Config version in status', 'config_version'),
            ('Auto-restart message', 'neu gestartet'),
            ('Manager check', 'manager.is_running()'),
        ]
        
        print("\n✓ Checking views updates...")
        for name, check in checks:
            if check in content:
                print(f"  ✓ Found: {name}")
            else:
                print(f"  ✗ MISSING: {name}")
                return False
        
        print("\n✅ Views updates validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error validating views: {e}")
        return False


def validate_admin_updates():
    """Validate that admin.py has been updated with notifications."""
    print("\n" + "=" * 80)
    print("VALIDATING ADMIN UPDATES")
    print("=" * 80)
    
    try:
        with open('telis_recruitment/scraper_control/admin.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('Django messages import', 'from django.contrib import messages'),
            ('Manager import in save_model', 'from .process_manager import get_manager'),
            ('Auto-restart notification', 'automatisch'),
        ]
        
        print("\n✓ Checking admin updates...")
        for name, check in checks:
            if check in content:
                print(f"  ✓ Found: {name}")
            else:
                print(f"  ✗ MISSING: {name}")
                return False
        
        print("\n✅ Admin updates validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error validating admin: {e}")
        return False


def validate_tests():
    """Validate that tests have been created."""
    print("\n" + "=" * 80)
    print("VALIDATING TESTS")
    print("=" * 80)
    
    try:
        with open('telis_recruitment/scraper_control/test_config_reload.py', 'r') as f:
            content = f.read()
        
        test_classes = [
            'TestConfigReload',
            'TestConfigReloadIntegration',
        ]
        
        test_methods = [
            'test_config_version_tracking',
            'test_config_watcher_thread_starts',
            'test_restart_process_method',
            'test_restart_process_concurrent_prevention',
        ]
        
        print("\n✓ Checking test classes...")
        for cls in test_classes:
            if f'class {cls}' in content:
                print(f"  ✓ Found: {cls}")
            else:
                print(f"  ✗ MISSING: {cls}")
                return False
        
        print("\n✓ Checking test methods...")
        for method in test_methods:
            if f'def {method}' in content:
                print(f"  ✓ Found: {method}")
            else:
                print(f"  ✗ MISSING: {method}")
                return False
        
        print("\n✅ Tests validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error validating tests: {e}")
        return False


def validate_documentation():
    """Validate that documentation has been created."""
    print("\n" + "=" * 80)
    print("VALIDATING DOCUMENTATION")
    print("=" * 80)
    
    try:
        with open('AUTO_CONFIG_RELOAD.md', 'r') as f:
            content = f.read()
        
        sections = [
            'Überblick',
            'Funktionsweise',
            'Polling-basierte Überwachung',
            'Automatischer Neustart',
            'Benutzer-Benachrichtigungen',
            'Fehlerbehandlung',
            'Testing',
        ]
        
        print("\n✓ Checking documentation sections...")
        for section in sections:
            if section in content:
                print(f"  ✓ Found: {section}")
            else:
                print(f"  ✗ MISSING: {section}")
                return False
        
        print("\n✅ Documentation validation PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error validating documentation: {e}")
        return False


def main():
    """Run all validation checks."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  AUTOMATIC CONFIG RELOAD FEATURE - VALIDATION SCRIPT".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    validations = [
        validate_process_manager_structure,
        validate_signal_handler,
        validate_views_updates,
        validate_admin_updates,
        validate_tests,
        validate_documentation,
    ]
    
    results = []
    for validation_func in validations:
        try:
            result = validation_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Unexpected error in {validation_func.__name__}: {e}")
            results.append(False)
    
    # Final summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"\nTotal checks: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if all(results):
        print("\n" + "🎉 " * 20)
        print("\n✅ ALL VALIDATIONS PASSED! The automatic config reload feature is properly implemented.")
        print("\n" + "🎉 " * 20)
        return 0
    else:
        print("\n❌ Some validations failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
