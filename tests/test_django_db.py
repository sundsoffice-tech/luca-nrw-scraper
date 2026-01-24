"""
Unit tests for Django ORM adapter (luca_scraper/django_db.py)
==============================================================
Tests the Django ORM adapter functions using Django TestCase.
"""

import pytest
from django.test import TestCase, TransactionTestCase
from telis_recruitment.leads.models import Lead


class TestDjangoDBAdapter(TransactionTestCase):
    """Test Django ORM adapter functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear all leads before each test
        Lead.objects.all().delete()
    
    def test_django_setup(self):
        """Test that Django is properly set up."""
        from luca_scraper import django_db
        
        # Should be able to access Django models
        assert Lead.objects is not None
    
    def test_upsert_lead_create_new(self):
        """Test creating a new lead via upsert."""
        from luca_scraper.django_db import upsert_lead
        
        data = {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'telefon': '+49123456789',
            'rolle': 'Sales Manager',
            'company_name': 'Example GmbH',
            'region': 'Köln',
            'score': 85,
        }
        
        lead_id, created = upsert_lead(data)
        
        assert created is True
        assert lead_id is not None
        
        # Verify lead was created
        lead = Lead.objects.get(id=lead_id)
        assert lead.name == 'Max Mustermann'
        assert lead.email == 'max@example.com'
        assert lead.telefon == '+49123456789'
        assert lead.role == 'Sales Manager'
        assert lead.company == 'Example GmbH'
        assert lead.location == 'Köln'
        assert lead.quality_score == 85
    
    def test_upsert_lead_deduplicate_by_email(self):
        """Test that upsert deduplicates by email."""
        from luca_scraper.django_db import upsert_lead
        
        # Create initial lead
        data1 = {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'telefon': '+49123456789',
            'score': 70,
        }
        
        lead_id1, created1 = upsert_lead(data1)
        assert created1 is True
        
        # Try to insert same email with different data
        data2 = {
            'name': 'Max Mustermann Updated',
            'email': 'MAX@EXAMPLE.COM',  # Different case
            'telefon': '+49987654321',
            'score': 90,
        }
        
        lead_id2, created2 = upsert_lead(data2)
        
        # Should update existing lead, not create new one
        assert created2 is False
        assert lead_id1 == lead_id2
        
        # Verify lead was updated
        lead = Lead.objects.get(id=lead_id1)
        assert lead.name == 'Max Mustermann Updated'
        assert lead.quality_score == 90
        
        # Verify only one lead exists
        assert Lead.objects.count() == 1
    
    def test_upsert_lead_deduplicate_by_phone(self):
        """Test that upsert deduplicates by phone when email not found."""
        from luca_scraper.django_db import upsert_lead
        
        # Create initial lead
        data1 = {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'telefon': '+49123456789',
            'score': 70,
        }
        
        lead_id1, created1 = upsert_lead(data1)
        assert created1 is True
        
        # Try to insert with different email but same phone
        data2 = {
            'name': 'Max Updated',
            'email': 'max2@example.com',
            'telefon': '0049123456789',  # Same phone, different format
            'score': 90,
        }
        
        lead_id2, created2 = upsert_lead(data2)
        
        # Should update existing lead
        assert created2 is False
        assert lead_id1 == lead_id2
        
        # Verify only one lead exists
        assert Lead.objects.count() == 1
    
    def test_upsert_lead_field_mapping(self):
        """Test that field mapping works correctly."""
        from luca_scraper.django_db import upsert_lead
        
        data = {
            'name': 'Test Person',
            'email': 'test@example.com',
            'rolle': 'Developer',  # Scraper field name
            'company_name': 'Tech Corp',  # Scraper field name
            'region': 'Düsseldorf',  # Scraper field name
            'quelle': 'https://example.com',  # Scraper field name
        }
        
        lead_id, created = upsert_lead(data)
        assert created is True
        
        # Verify Django fields were mapped correctly
        lead = Lead.objects.get(id=lead_id)
        assert lead.role == 'Developer'
        assert lead.company == 'Tech Corp'
        assert lead.location == 'Düsseldorf'
        assert lead.source_url == 'https://example.com'
    
    def test_upsert_lead_json_fields(self):
        """Test handling of JSON array fields."""
        from luca_scraper.django_db import upsert_lead
        
        data = {
            'name': 'Test Person',
            'email': 'test@example.com',
            'tags': ['tag1', 'tag2', 'tag3'],
            'skills': ['Python', 'Django', 'SQL'],
        }
        
        lead_id, created = upsert_lead(data)
        assert created is True
        
        # Verify JSON fields were stored correctly
        lead = Lead.objects.get(id=lead_id)
        assert lead.tags == ['tag1', 'tag2', 'tag3']
        assert lead.skills == ['Python', 'Django', 'SQL']
    
    def test_upsert_lead_json_string_conversion(self):
        """Test conversion of JSON strings to arrays."""
        from luca_scraper.django_db import upsert_lead
        
        data = {
            'name': 'Test Person',
            'email': 'test@example.com',
            'tags': '["tag1", "tag2"]',  # JSON string
        }
        
        lead_id, created = upsert_lead(data)
        assert created is True
        
        # Verify JSON string was parsed correctly
        lead = Lead.objects.get(id=lead_id)
        assert lead.tags == ['tag1', 'tag2']
    
    def test_get_lead_count(self):
        """Test getting lead count."""
        from luca_scraper.django_db import get_lead_count, upsert_lead
        
        # Initially should be 0
        assert get_lead_count() == 0
        
        # Create some leads
        upsert_lead({'name': 'Lead 1', 'email': 'lead1@example.com'})
        assert get_lead_count() == 1
        
        upsert_lead({'name': 'Lead 2', 'email': 'lead2@example.com'})
        assert get_lead_count() == 2
        
        upsert_lead({'name': 'Lead 3', 'email': 'lead3@example.com'})
        assert get_lead_count() == 3
    
    def test_lead_exists_by_email(self):
        """Test checking if lead exists by email."""
        from luca_scraper.django_db import lead_exists, upsert_lead
        
        # Should not exist initially
        assert lead_exists(email='test@example.com') is False
        
        # Create lead
        upsert_lead({'name': 'Test', 'email': 'test@example.com'})
        
        # Should exist now
        assert lead_exists(email='test@example.com') is True
        assert lead_exists(email='TEST@EXAMPLE.COM') is True  # Case insensitive
        
        # Different email should not exist
        assert lead_exists(email='other@example.com') is False
    
    def test_lead_exists_by_phone(self):
        """Test checking if lead exists by phone."""
        from luca_scraper.django_db import lead_exists, upsert_lead
        
        # Should not exist initially
        assert lead_exists(telefon='+49123456789') is False
        
        # Create lead
        upsert_lead({'name': 'Test', 'telefon': '+49123456789'})
        
        # Should exist now
        assert lead_exists(telefon='+49123456789') is True
        assert lead_exists(telefon='0049123456789') is True  # Different format
        
        # Different phone should not exist
        assert lead_exists(telefon='+49987654321') is False

    def test_lead_normalized_fields_are_set(self):
        """Ensure normalized email/phone fields are populated."""
        from luca_scraper.django_db import upsert_lead

        data = {
            'name': 'Normalized Lead',
            'email': 'NORM@Example.COM ',
            'telefon': '+49 (123) 456-789',
        }
        lead_id, _ = upsert_lead(data)

        lead = Lead.objects.get(id=lead_id)
        assert lead.email_normalized == 'norm@example.com'
        assert lead.normalized_phone == '49123456789'
    
    def test_lead_exists_no_params(self):
        """Test that lead_exists returns False when no params provided."""
        from luca_scraper.django_db import lead_exists
        
        assert lead_exists() is False
        assert lead_exists(email=None, telefon=None) is False
    
    def test_get_lead_by_id(self):
        """Test retrieving lead by ID."""
        from luca_scraper.django_db import get_lead_by_id, upsert_lead
        
        # Create lead
        data = {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'telefon': '+49123456789',
            'rolle': 'Sales Manager',
            'score': 85,
        }
        
        lead_id, _ = upsert_lead(data)
        
        # Retrieve lead
        lead_data = get_lead_by_id(lead_id)
        
        assert lead_data is not None
        assert lead_data['id'] == lead_id
        assert lead_data['name'] == 'Max Mustermann'
        assert lead_data['email'] == 'max@example.com'
        assert lead_data['telefon'] == '+49123456789'
        assert lead_data['rolle'] == 'Sales Manager'
        assert lead_data['score'] == 85
    
    def test_get_lead_by_id_not_found(self):
        """Test that get_lead_by_id returns None for non-existent lead."""
        from luca_scraper.django_db import get_lead_by_id
        
        # Non-existent ID
        lead_data = get_lead_by_id(99999)
        
        assert lead_data is None
    
    def test_update_lead(self):
        """Test updating an existing lead."""
        from luca_scraper.django_db import update_lead, upsert_lead, get_lead_by_id
        
        # Create lead
        data = {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'score': 70,
        }
        
        lead_id, _ = upsert_lead(data)
        
        # Update lead
        update_data = {
            'name': 'Max Updated',
            'score': 95,
            'rolle': 'Senior Manager',
        }
        
        result = update_lead(lead_id, update_data)
        
        assert result is True
        
        # Verify update
        lead_data = get_lead_by_id(lead_id)
        assert lead_data['name'] == 'Max Updated'
        assert lead_data['score'] == 95
        assert lead_data['rolle'] == 'Senior Manager'
    
    def test_update_lead_not_found(self):
        """Test that update_lead returns False for non-existent lead."""
        from luca_scraper.django_db import update_lead
        
        # Non-existent ID
        result = update_lead(99999, {'name': 'Test'})
        
        assert result is False
    
    def test_integer_field_conversion(self):
        """Test that integer fields are properly converted."""
        from luca_scraper.django_db import upsert_lead, get_lead_by_id
        
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            'score': '85',  # String should be converted to int
            'experience_years': '5',
            'confidence_score': '90',
        }
        
        lead_id, _ = upsert_lead(data)
        
        # Verify integers were converted
        lead_data = get_lead_by_id(lead_id)
        assert isinstance(lead_data['score'], int)
        assert lead_data['score'] == 85
        assert isinstance(lead_data['experience_years'], int)
        assert lead_data['experience_years'] == 5
    
    def test_boolean_field_conversion(self):
        """Test that boolean fields are properly converted."""
        from luca_scraper.django_db import upsert_lead, get_lead_by_id
        
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            'name_validated': 'true',  # String should be converted to bool
        }
        
        lead_id, _ = upsert_lead(data)
        
        # Verify boolean was converted
        lead_data = get_lead_by_id(lead_id)
        assert lead_data['name_validated'] is True
    
    def test_source_defaults_to_scraper(self):
        """Test that source is set to SCRAPER by default."""
        from luca_scraper.django_db import upsert_lead
        
        data = {
            'name': 'Test',
            'email': 'test@example.com',
        }
        
        lead_id, _ = upsert_lead(data)
        
        # Verify source was set
        lead = Lead.objects.get(id=lead_id)
        assert lead.source == Lead.Source.SCRAPER


@pytest.mark.django
class TestDjangoDBIntegration(TransactionTestCase):
    """Integration tests for Django ORM adapter."""
    
    def test_concurrent_upserts(self):
        """Test that concurrent upserts handle deduplication correctly."""
        from luca_scraper.django_db import upsert_lead, get_lead_count
        
        # Simulate concurrent upserts of same lead
        data = {
            'name': 'Concurrent Test',
            'email': 'concurrent@example.com',
        }
        
        lead_id1, created1 = upsert_lead(data)
        lead_id2, created2 = upsert_lead(data)
        
        # Should have same ID and only one should be created
        assert lead_id1 == lead_id2
        assert created1 is True
        assert created2 is False
        assert get_lead_count() == 1
    
    def test_empty_values_handling(self):
        """Test that empty strings and None values are handled correctly."""
        from luca_scraper.django_db import upsert_lead, get_lead_by_id
        
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            'rolle': '',  # Empty string
            'company_name': None,  # None value
            'score': 80,
        }
        
        lead_id, _ = upsert_lead(data)
        
        # Verify lead was created and empty values ignored
        lead_data = get_lead_by_id(lead_id)
        assert lead_data['name'] == 'Test'
        assert lead_data['score'] == 80
        # Empty/None values should either be omitted from result or set to None
        # Both are acceptable behaviors
        if 'rolle' in lead_data:
            assert lead_data['rolle'] is None or lead_data['rolle'] == ''


@pytest.mark.django
class TestDjangoDBTTLFunctionality(TransactionTestCase):
    """Tests for TTL and cleanup functionality in Django ORM adapter."""
    
    def setUp(self):
        """Set up test environment."""
        from telis_recruitment.scraper_control.models import QueryDone, UrlSeen
        # Clear all queries and URLs before each test
        QueryDone.objects.all().delete()
        UrlSeen.objects.all().delete()
    
    def test_is_query_done_with_ttl(self):
        """Test that is_query_done respects TTL parameter."""
        from luca_scraper.django_db import is_query_done, mark_query_done
        
        # Mark a query as done
        mark_query_done("test query")
        
        # Should be found with default TTL (48 hours)
        assert is_query_done("test query", ttl_hours=48) is True
        
        # Should be found with shorter TTL (1 hour)
        assert is_query_done("test query", ttl_hours=1) is True
    
    def test_is_query_done_expired(self):
        """Test that expired queries are not found."""
        from luca_scraper.django_db import is_query_done, mark_query_done
        from telis_recruitment.scraper_control.models import QueryDone
        from django.utils import timezone
        from datetime import timedelta
        
        # Mark a query as done
        mark_query_done("old query")
        
        # Backdate the query to make it expired
        old_query = QueryDone.objects.get(query="old query")
        old_query.last_executed_at = timezone.now() - timedelta(hours=72)
        old_query.save()
        
        # Should NOT be found with TTL of 48 hours
        assert is_query_done("old query", ttl_hours=48) is False
        
        # Should be found with TTL of 100 hours
        assert is_query_done("old query", ttl_hours=100) is True
    
    def test_mark_query_done_updates_timestamp(self):
        """Test that mark_query_done updates timestamp on subsequent calls."""
        from luca_scraper.django_db import mark_query_done
        from telis_recruitment.scraper_control.models import QueryDone
        from django.utils import timezone
        from datetime import timedelta
        import time
        
        # Mark query as done
        mark_query_done("update test query")
        
        # Get first timestamp
        query = QueryDone.objects.get(query="update test query")
        first_timestamp = query.last_executed_at
        
        # Wait a moment to ensure timestamp difference
        time.sleep(0.1)
        
        # Mark it again
        mark_query_done("update test query")
        
        # Get updated timestamp
        query.refresh_from_db()
        second_timestamp = query.last_executed_at
        
        # Second timestamp should be newer
        assert second_timestamp > first_timestamp
    
    def test_cleanup_expired_queries(self):
        """Test cleanup of expired query cache entries."""
        from luca_scraper.django_db import cleanup_expired_queries, mark_query_done
        from telis_recruitment.scraper_control.models import QueryDone
        from django.utils import timezone
        from datetime import timedelta
        
        # Create recent query
        mark_query_done("recent query")
        
        # Create old query and backdate it
        mark_query_done("old query")
        old_query = QueryDone.objects.get(query="old query")
        old_query.last_executed_at = timezone.now() - timedelta(hours=100)
        old_query.save()
        
        # Verify we have 2 queries
        assert QueryDone.objects.count() == 2
        
        # Cleanup with TTL of 48 hours should remove the old one
        deleted = cleanup_expired_queries(ttl_hours=48)
        assert deleted == 1
        
        # Verify only recent query remains
        assert QueryDone.objects.count() == 1
        assert QueryDone.objects.filter(query="recent query").exists()
        assert not QueryDone.objects.filter(query="old query").exists()
    
    def test_cleanup_expired_urls(self):
        """Test cleanup of expired URL cache entries."""
        from luca_scraper.django_db import cleanup_expired_urls, mark_url_seen
        from telis_recruitment.scraper_control.models import UrlSeen
        from django.utils import timezone
        from datetime import timedelta
        
        # Create recent URL
        mark_url_seen("https://recent.example.com")
        
        # Create old URL and backdate it
        mark_url_seen("https://old.example.com")
        old_url = UrlSeen.objects.get(url="https://old.example.com")
        old_url.created_at = timezone.now() - timedelta(hours=200)
        old_url.save()
        
        # Verify we have 2 URLs
        assert UrlSeen.objects.count() == 2
        
        # Cleanup with TTL of 168 hours (7 days) should remove the old one
        deleted = cleanup_expired_urls(ttl_hours=168)
        assert deleted == 1
        
        # Verify only recent URL remains
        assert UrlSeen.objects.count() == 1
        assert UrlSeen.objects.filter(url="https://recent.example.com").exists()
        assert not UrlSeen.objects.filter(url="https://old.example.com").exists()
    
    def test_cleanup_no_expired_entries(self):
        """Test cleanup when no entries are expired."""
        from luca_scraper.django_db import cleanup_expired_queries, cleanup_expired_urls, mark_query_done, mark_url_seen
        
        # Create recent entries
        mark_query_done("recent query")
        mark_url_seen("https://recent.example.com")
        
        # Cleanup should not remove anything
        deleted_queries = cleanup_expired_queries(ttl_hours=48)
        assert deleted_queries == 0
        
        deleted_urls = cleanup_expired_urls(ttl_hours=168)
        assert deleted_urls == 0
    
    def test_is_query_done_with_run_id(self):
        """Test that mark_query_done can associate with a run ID."""
        from luca_scraper.django_db import mark_query_done, is_query_done, start_scraper_run
        from telis_recruitment.scraper_control.models import QueryDone
        
        # Start a scraper run
        run_id = start_scraper_run()
        
        # Mark query with run ID
        mark_query_done("query with run", run_id=run_id)
        
        # Verify query was marked
        assert is_query_done("query with run", ttl_hours=48) is True
        
        # Verify run ID was stored
        query = QueryDone.objects.get(query="query with run")
        assert query.last_run_id == run_id
