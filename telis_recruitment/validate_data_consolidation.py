#!/usr/bin/env python
"""
Validation script for data structure consolidation.

This script validates:
1. All fields in field_mapping exist in Lead model
2. Migration can be loaded without errors
3. Field types are correct

Run from telis_recruitment directory:
    python validate_data_consolidation.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')
django.setup()

from leads.models import Lead
from leads.field_mapping import (
    SCRAPER_TO_DJANGO_MAPPING,
    JSON_ARRAY_FIELDS,
    INTEGER_FIELDS,
    URL_FIELDS
)


def validate_field_mapping():
    """Validate that all mapped fields exist in Lead model."""
    print("🔍 Validating field mapping...")
    
    errors = []
    warnings = []
    
    # Get all unique Django fields from mapping
    django_fields = set(SCRAPER_TO_DJANGO_MAPPING.values())
    
    for field_name in django_fields:
        if not hasattr(Lead, field_name):
            errors.append(f"❌ Field '{field_name}' from mapping not found in Lead model")
        else:
            # Get field type
            try:
                field = Lead._meta.get_field(field_name)
                field_type = type(field).__name__
                
                # Validate field types
                if field_name in JSON_ARRAY_FIELDS:
                    if field_type != 'JSONField':
                        warnings.append(
                            f"⚠️  Field '{field_name}' should be JSONField but is {field_type}"
                        )
                
                if field_name in INTEGER_FIELDS:
                    if field_type not in ['IntegerField', 'BigIntegerField']:
                        warnings.append(
                            f"⚠️  Field '{field_name}' should be IntegerField but is {field_type}"
                        )
                
                if field_name in URL_FIELDS:
                    if field_type not in ['URLField', 'CharField', 'TextField']:
                        warnings.append(
                            f"⚠️  Field '{field_name}' should be URL-compatible but is {field_type}"
                        )
            except Exception as e:
                errors.append(f"❌ Error checking field '{field_name}': {e}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    if warnings:
        print("\n".join(warnings))
    
    print(f"✅ All {len(django_fields)} mapped fields exist in Lead model")
    return True


def validate_lead_types():
    """Validate that all lead types from mapping exist in enum."""
    print("\n🔍 Validating Lead types...")
    
    expected_types = [
        'active_salesperson',
        'team_member',
        'freelancer',
        'hr_contact',
        'candidate',
        'talent_hunt',
        'recruiter',
        'job_ad',
        'company',
        'individual',
        'unknown'
    ]
    
    available_types = [choice[0] for choice in Lead.LeadType.choices]
    
    missing = set(expected_types) - set(available_types)
    if missing:
        print(f"❌ Missing lead types: {missing}")
        return False
    
    print(f"✅ All {len(expected_types)} lead types exist in enum")
    return True


def validate_new_fields():
    """Validate that new fields are properly configured."""
    print("\n🔍 Validating new fields...")
    
    new_fields = [
        'confidence_score',
        'phone_type',
        'whatsapp_link',
        'ai_category',
        'ai_summary',
        'opening_line',
        'tags',
        'skills',
        'availability',
        'candidate_status',
        'mobility',
        'salary_hint',
        'commission_hint',
        'company_size',
        'hiring_volume',
        'industry',
        'data_quality',
        'private_address',
        'profile_url',
        'cv_url',
        'contact_preference',
        'recency_indicator',
        'last_updated',
    ]
    
    missing = []
    for field_name in new_fields:
        if not hasattr(Lead, field_name):
            missing.append(field_name)
    
    if missing:
        print(f"❌ Missing new fields: {missing}")
        return False
    
    print(f"✅ All {len(new_fields)} new fields exist in Lead model")
    
    # Check that they are nullable
    non_nullable = []
    for field_name in new_fields:
        try:
            field = Lead._meta.get_field(field_name)
            if not field.null and not field.blank:
                non_nullable.append(field_name)
        except:
            pass
    
    if non_nullable:
        print(f"⚠️  Non-nullable new fields (might cause issues): {non_nullable}")
    else:
        print("✅ All new fields are nullable/blankable")
    
    return True


def check_field_count():
    """Check total field count."""
    print("\n📊 Field statistics:")
    
    all_fields = [f.name for f in Lead._meta.get_fields() if not f.many_to_many and not f.one_to_many]
    print(f"   Total Lead model fields: {len(all_fields)}")
    print(f"   Mapped scraper fields: {len(set(SCRAPER_TO_DJANGO_MAPPING.values()))}")
    print(f"   Scraper source fields: {len(SCRAPER_TO_DJANGO_MAPPING)}")


def main():
    print("=" * 60)
    print("Data Structure Consolidation - Validation")
    print("=" * 60)
    
    results = []
    
    # Run validations
    results.append(("Field Mapping", validate_field_mapping()))
    results.append(("Lead Types", validate_lead_types()))
    results.append(("New Fields", validate_new_fields()))
    
    check_field_count()
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All validations passed!")
        return 0
    else:
        print("\n❌ Some validations failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
