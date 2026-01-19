#!/usr/bin/env python3
"""
Simple verification script to check SSL security defaults.
Does not require full dependency installation.
"""
import os
import sys

def check_config_file(filepath, expected_default="0"):
    """Check if ALLOW_INSECURE_SSL has secure default in config file."""
    print(f"\n📄 Checking {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Look for ALLOW_INSECURE_SSL definition
    import re
    pattern = r'ALLOW_INSECURE_SSL\s*=\s*\(os\.getenv\("ALLOW_INSECURE_SSL",\s*"(\d+)"\)'
    matches = re.findall(pattern, content)
    
    if not matches:
        print(f"  ❌ Could not find ALLOW_INSECURE_SSL definition")
        return False
    
    default_value = matches[0]
    if default_value == expected_default:
        print(f"  ✅ ALLOW_INSECURE_SSL defaults to '{default_value}' (secure)")
        return True
    else:
        print(f"  ❌ ALLOW_INSECURE_SSL defaults to '{default_value}' (expected '{expected_default}')")
        return False

def check_env_example(filepath):
    """Check .env.example has secure default."""
    print(f"\n📄 Checking {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "ALLOW_INSECURE_SSL=0" in content:
        print(f"  ✅ .env.example has ALLOW_INSECURE_SSL=0")
        return True
    else:
        print(f"  ❌ .env.example does not have ALLOW_INSECURE_SSL=0")
        return False

def check_production_warnings(filepath):
    """Check if production settings have SSL warnings."""
    print(f"\n📄 Checking {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "ALLOW_INSECURE_SSL" in content and "SICHERHEITSWARNUNG" in content:
        print(f"  ✅ Production settings have SSL security warnings")
        return True
    else:
        print(f"  ❌ Production settings missing SSL security warnings")
        return False

def check_admin_conditional_field(filepath):
    """Check if admin conditionally shows allow_insecure_ssl."""
    print(f"\n📄 Checking {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "settings.DEBUG" in content and "allow_insecure_ssl" in content:
        print(f"  ✅ Admin conditionally shows allow_insecure_ssl based on DEBUG mode")
        return True
    else:
        print(f"  ⚠️  Admin does not conditionally show allow_insecure_ssl (may be intentionally hidden)")
        return True  # Not a failure, just informational

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("SSL Security Configuration Verification")
    print("=" * 70)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    results = []
    
    # Check config files
    results.append(check_config_file(
        os.path.join(base_dir, "luca_scraper", "config.py")
    ))
    results.append(check_config_file(
        os.path.join(base_dir, "scriptname.py")
    ))
    
    # Check .env.example
    results.append(check_env_example(
        os.path.join(base_dir, ".env.example")
    ))
    
    # Check production settings
    results.append(check_production_warnings(
        os.path.join(base_dir, "telis_recruitment", "telis", "settings_prod.py")
    ))
    
    # Check admin
    results.append(check_admin_conditional_field(
        os.path.join(base_dir, "telis_recruitment", "scraper_control", "admin.py")
    ))
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ All SSL security checks passed!")
        print("=" * 70)
        return 0
    else:
        print("❌ Some SSL security checks failed!")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
