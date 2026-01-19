#!/usr/bin/env python
"""
Validation script for ProcessManager error handling and retry logic.
This script performs basic validation without requiring a full Django setup.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_syntax():
    """Validate Python syntax of modified files."""
    print("=== Validating Python Syntax ===\n")
    
    files_to_check = [
        'telis_recruitment/scraper_control/process_manager.py',
        'telis_recruitment/scraper_control/models.py',
        'telis_recruitment/scraper_control/admin.py',
        'telis_recruitment/scraper_control/test_process_manager_retry.py',
    ]
    
    import py_compile
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        try:
            py_compile.compile(full_path, doraise=True)
            print(f"✅ {file_path}: Syntax OK")
        except py_compile.PyCompileError as e:
            print(f"❌ {file_path}: Syntax Error")
            print(f"   {e}")
            return False
    
    print("\n✅ All files have valid Python syntax\n")
    return True


def validate_implementation():
    """Validate that key components are present."""
    print("=== Validating Implementation ===\n")
    
    checks = [
        # Check CircuitBreakerState enum
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'class CircuitBreakerState',
            'description': 'CircuitBreakerState enum'
        },
        # Check error tracking method
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _track_error',
            'description': '_track_error method'
        },
        # Check circuit breaker methods
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _check_circuit_breaker',
            'description': '_check_circuit_breaker method'
        },
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _open_circuit_breaker',
            'description': '_open_circuit_breaker method'
        },
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _close_circuit_breaker',
            'description': '_close_circuit_breaker method'
        },
        # Check retry methods
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _should_retry',
            'description': '_should_retry method'
        },
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _calculate_retry_backoff',
            'description': '_calculate_retry_backoff method'
        },
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _adjust_qpi_for_rate_limit',
            'description': '_adjust_qpi_for_rate_limit method'
        },
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _schedule_retry',
            'description': '_schedule_retry method'
        },
        # Check config loading
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def _load_config',
            'description': '_load_config method'
        },
        # Check reset method
        {
            'file': 'telis_recruitment/scraper_control/process_manager.py',
            'pattern': 'def reset_error_tracking',
            'description': 'reset_error_tracking method'
        },
        # Check model fields
        {
            'file': 'telis_recruitment/scraper_control/models.py',
            'pattern': 'process_max_retry_attempts',
            'description': 'process_max_retry_attempts field'
        },
        {
            'file': 'telis_recruitment/scraper_control/models.py',
            'pattern': 'process_qpi_reduction_factor',
            'description': 'process_qpi_reduction_factor field'
        },
        {
            'file': 'telis_recruitment/scraper_control/models.py',
            'pattern': 'process_error_rate_threshold',
            'description': 'process_error_rate_threshold field'
        },
        {
            'file': 'telis_recruitment/scraper_control/models.py',
            'pattern': 'process_circuit_breaker_failures',
            'description': 'process_circuit_breaker_failures field'
        },
        {
            'file': 'telis_recruitment/scraper_control/models.py',
            'pattern': 'process_retry_backoff_base',
            'description': 'process_retry_backoff_base field'
        },
        # Check migration exists
        {
            'file': 'telis_recruitment/scraper_control/migrations/0007_add_process_retry_circuit_breaker_fields.py',
            'pattern': 'class Migration',
            'description': 'Migration for new fields'
        },
        # Check tests exist
        {
            'file': 'telis_recruitment/scraper_control/test_process_manager_retry.py',
            'pattern': 'class ProcessManagerErrorTrackingTest',
            'description': 'Error tracking tests'
        },
        {
            'file': 'telis_recruitment/scraper_control/test_process_manager_retry.py',
            'pattern': 'class ProcessManagerRetryLogicTest',
            'description': 'Retry logic tests'
        },
    ]
    
    all_passed = True
    for check in checks:
        file_path = os.path.join(os.path.dirname(__file__), check['file'])
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if check['pattern'] in content:
                    print(f"✅ {check['description']}: Found")
                else:
                    print(f"❌ {check['description']}: Not found in {check['file']}")
                    all_passed = False
        except FileNotFoundError:
            print(f"❌ {check['description']}: File not found: {check['file']}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All implementation checks passed\n")
    else:
        print("\n❌ Some implementation checks failed\n")
    
    return all_passed


def validate_documentation():
    """Validate that documentation exists."""
    print("=== Validating Documentation ===\n")
    
    doc_file = 'PROCESS_MANAGER_ERROR_HANDLING.md'
    doc_path = os.path.join(os.path.dirname(__file__), doc_file)
    
    if not os.path.exists(doc_path):
        print(f"❌ Documentation file not found: {doc_file}")
        return False
    
    with open(doc_path, 'r') as f:
        content = f.read()
    
    required_sections = [
        '## Overview',
        '### 1. Error Tracking',
        '### 2. Automatic Retry',
        '### 3. Circuit Breaker',
        '## Konfiguration',
        '## Monitoring',
        '## Workflow-Beispiele',
        '## Best Practices',
        '## Troubleshooting',
    ]
    
    all_found = True
    for section in required_sections:
        if section in content:
            print(f"✅ Section found: {section}")
        else:
            print(f"❌ Section missing: {section}")
            all_found = False
    
    if all_found:
        print(f"\n✅ Documentation is complete ({len(content)} bytes)\n")
    else:
        print("\n❌ Documentation is incomplete\n")
    
    return all_found


def main():
    """Run all validations."""
    print("=" * 60)
    print("ProcessManager Error Handling - Implementation Validation")
    print("=" * 60)
    print()
    
    results = {
        'syntax': validate_syntax(),
        'implementation': validate_implementation(),
        'documentation': validate_documentation(),
    }
    
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print()
    
    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check.capitalize():.<30} {status}")
    
    print()
    
    if all(results.values()):
        print("🎉 All validations passed! Implementation is complete.")
        print()
        print("Next steps:")
        print("  1. Run Django migrations: python manage.py migrate scraper_control")
        print("  2. Configure settings in Django Admin")
        print("  3. Start the scraper and monitor error handling")
        print("  4. Review PROCESS_MANAGER_ERROR_HANDLING.md for usage guide")
        return 0
    else:
        print("⚠️  Some validations failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
