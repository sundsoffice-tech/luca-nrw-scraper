"""
Simple manual test for Django ORM adapter.
Run this with: python3 test_django_db_manual.py
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis_recruitment.telis.settings')

import django
django.setup()

# Now import our module
from luca_scraper.django_db import (
    upsert_lead,
    get_lead_count,
    lead_exists,
    get_lead_by_id,
    update_lead,
)
from telis_recruitment.leads.models import Lead


def test_basic_functionality():
    """Test basic functionality of Django ORM adapter."""
    
    print("=" * 60)
    print("Testing Django ORM Adapter")
    print("=" * 60)
    
    # Clean up any test data
    Lead.objects.filter(email__contains='test-django-adapter').delete()
    
    # Test 1: Create new lead
    print("\n1. Testing upsert_lead (create new)...")
    data1 = {
        'name': 'Test Person',
        'email': 'test-django-adapter@example.com',
        'telefon': '+49123456789',
        'rolle': 'Sales Manager',
        'score': 85,
    }
    
    lead_id1, created1 = upsert_lead(data1)
    print(f"   Created: {created1}, Lead ID: {lead_id1}")
    assert created1 is True
    assert lead_id1 is not None
    print("   ✓ New lead created successfully")
    
    # Test 2: Get lead count
    print("\n2. Testing get_lead_count...")
    count = get_lead_count()
    print(f"   Total leads: {count}")
    assert count >= 1
    print("   ✓ Lead count retrieved successfully")
    
    # Test 3: Check if lead exists
    print("\n3. Testing lead_exists...")
    exists = lead_exists(email='test-django-adapter@example.com')
    print(f"   Lead exists: {exists}")
    assert exists is True
    print("   ✓ Lead existence check successful")
    
    # Test 4: Get lead by ID
    print("\n4. Testing get_lead_by_id...")
    lead_data = get_lead_by_id(lead_id1)
    print(f"   Retrieved lead: {lead_data['name']} ({lead_data['email']})")
    assert lead_data is not None
    assert lead_data['name'] == 'Test Person'
    assert lead_data['score'] == 85
    print("   ✓ Lead retrieved successfully")
    
    # Test 5: Update lead
    print("\n5. Testing update_lead...")
    update_data = {
        'name': 'Test Person Updated',
        'score': 95,
    }
    updated = update_lead(lead_id1, update_data)
    print(f"   Updated: {updated}")
    assert updated is True
    
    # Verify update
    lead_data2 = get_lead_by_id(lead_id1)
    print(f"   New name: {lead_data2['name']}, New score: {lead_data2['score']}")
    assert lead_data2['name'] == 'Test Person Updated'
    assert lead_data2['score'] == 95
    print("   ✓ Lead updated successfully")
    
    # Test 6: Deduplication by email
    print("\n6. Testing deduplication by email...")
    data2 = {
        'name': 'Different Name',
        'email': 'TEST-DJANGO-ADAPTER@EXAMPLE.COM',  # Same email, different case
        'score': 70,
    }
    lead_id2, created2 = upsert_lead(data2)
    print(f"   Created: {created2}, Lead ID: {lead_id2}")
    assert created2 is False
    assert lead_id1 == lead_id2
    print("   ✓ Email deduplication working")
    
    # Test 7: Deduplication by phone
    print("\n7. Testing deduplication by phone...")
    data3 = {
        'name': 'Another Name',
        'email': 'different@example.com',
        'telefon': '0049123456789',  # Same phone, different format
        'score': 60,
    }
    lead_id3, created3 = upsert_lead(data3)
    print(f"   Created: {created3}, Lead ID: {lead_id3}")
    assert created3 is False
    assert lead_id1 == lead_id3
    print("   ✓ Phone deduplication working")
    
    # Test 8: Field mapping
    print("\n8. Testing field mapping...")
    data4 = {
        'name': 'Mapping Test',
        'email': 'mapping-test@example.com',
        'rolle': 'Developer',  # Scraper field
        'company_name': 'Tech Corp',  # Scraper field
        'region': 'Köln',  # Scraper field
    }
    lead_id4, created4 = upsert_lead(data4)
    assert created4 is True
    
    lead = Lead.objects.get(id=lead_id4)
    assert lead.role == 'Developer'
    assert lead.company == 'Tech Corp'
    assert lead.location == 'Köln'
    print("   ✓ Field mapping working correctly")
    
    # Clean up
    print("\n9. Cleaning up test data...")
    Lead.objects.filter(email__contains='test-django-adapter').delete()
    Lead.objects.filter(email='mapping-test@example.com').delete()
    print("   ✓ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
