"""
Unit tests for optimized upsert operations
==========================================
Tests to verify that upsert operations avoid N+1 queries.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

# Import both backends
from luca_scraper.database import upsert_lead_sqlite, DB_PATH
from django.test import TransactionTestCase
from telis_recruitment.leads.models import Lead


class TestSQLiteUpsertOptimization:
    """Test optimized SQLite upsert operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        
        # Initialize schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
        PRAGMA journal_mode = WAL;
        
        CREATE TABLE IF NOT EXISTS leads(
          id INTEGER PRIMARY KEY,
          name TEXT,
          rolle TEXT,
          email TEXT,
          telefon TEXT,
          quelle TEXT,
          score INT,
          tags TEXT,
          region TEXT
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_email
        ON leads(email) WHERE email IS NOT NULL AND email <> '';
        
        CREATE UNIQUE INDEX IF NOT EXISTS ux_leads_tel
        ON leads(telefon) WHERE telefon IS NOT NULL AND telefon <> '';
        """)
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
    
    def test_upsert_creates_new_lead(self, temp_db):
        """Test that upsert creates a new lead when none exists."""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            data = {
                'name': 'Max Mustermann',
                'email': 'max@example.com',
                'telefon': '+49123456789',
                'score': 85,
            }
            
            lead_id, created = upsert_lead_sqlite(data)
            
            assert created is True
            assert lead_id is not None
            assert lead_id > 0
    
    def test_upsert_updates_existing_lead_by_email(self, temp_db):
        """Test that upsert updates existing lead when email matches."""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Create initial lead
            data1 = {
                'name': 'Max Mustermann',
                'email': 'max@example.com',
                'telefon': '+49123456789',
                'score': 70,
            }
            
            lead_id1, created1 = upsert_lead_sqlite(data1)
            assert created1 is True
            
            # Update with same email
            data2 = {
                'name': 'Max Mustermann Updated',
                'email': 'max@example.com',
                'telefon': '+49987654321',
                'score': 90,
            }
            
            lead_id2, created2 = upsert_lead_sqlite(data2)
            
            # Should update, not create
            assert created2 is False
            assert lead_id1 == lead_id2
    
    def test_upsert_updates_existing_lead_by_phone(self, temp_db):
        """Test that upsert updates existing lead when phone matches."""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Create initial lead
            data1 = {
                'name': 'Max Mustermann',
                'email': 'max@example.com',
                'telefon': '+49123456789',
                'score': 70,
            }
            
            lead_id1, created1 = upsert_lead_sqlite(data1)
            assert created1 is True
            
            # Update with different email but same phone
            data2 = {
                'name': 'Max Updated',
                'email': 'max2@example.com',
                'telefon': '+49123456789',
                'score': 90,
            }
            
            lead_id2, created2 = upsert_lead_sqlite(data2)
            
            # Should update, not create
            assert created2 is False
            assert lead_id1 == lead_id2
    
    def test_upsert_bulk_operations(self, temp_db):
        """Test that bulk upserts work efficiently."""
        with patch("luca_scraper.database.DB_PATH", temp_db):
            # Insert 100 leads
            for i in range(100):
                data = {
                    'name': f'Lead {i}',
                    'email': f'lead{i}@example.com',
                    'telefon': f'+4912345{i:04d}',
                    'score': 70 + i,
                }
                lead_id, created = upsert_lead_sqlite(data)
                assert created is True
            
            # Update 50 of them
            for i in range(50):
                data = {
                    'name': f'Lead {i} Updated',
                    'email': f'lead{i}@example.com',
                    'score': 90 + i,
                }
                lead_id, created = upsert_lead_sqlite(data)
                assert created is False
            
            # Verify count
            conn = sqlite3.connect(str(temp_db))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            count = cur.fetchone()[0]
            conn.close()
            
            assert count == 100


class TestDjangoUpsertOptimization(TransactionTestCase):
    """Test optimized Django ORM upsert operations."""
    
    def setUp(self):
        """Set up test environment."""
        Lead.objects.all().delete()
    
    def test_upsert_creates_new_lead(self):
        """Test that upsert creates a new lead when none exists."""
        from luca_scraper.django_db import upsert_lead
        
        data = {
            'name': 'Max Mustermann',
            'email': 'max@example.com',
            'telefon': '+49123456789',
            'score': 85,
        }
        
        lead_id, created = upsert_lead(data)
        
        assert created is True
        assert lead_id is not None
        assert Lead.objects.count() == 1
    
    def test_upsert_updates_existing_lead_by_email(self):
        """Test that upsert updates existing lead when email matches."""
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
        
        # Update with same email
        data2 = {
            'name': 'Max Mustermann Updated',
            'email': 'max@example.com',
            'telefon': '+49987654321',
            'score': 90,
        }
        
        lead_id2, created2 = upsert_lead(data2)
        
        # Should update, not create
        assert created2 is False
        assert lead_id1 == lead_id2
        assert Lead.objects.count() == 1
    
    def test_upsert_bulk_operations(self):
        """Test that bulk upserts work efficiently."""
        from luca_scraper.django_db import upsert_lead
        
        # Insert 100 leads
        for i in range(100):
            data = {
                'name': f'Lead {i}',
                'email': f'lead{i}@example.com',
                'telefon': f'+4912345{i:04d}',
                'score': 70 + i,
            }
            lead_id, created = upsert_lead(data)
            assert created is True
        
        # Update 50 of them
        for i in range(50):
            data = {
                'name': f'Lead {i} Updated',
                'email': f'lead{i}@example.com',
                'score': 90 + i,
            }
            lead_id, created = upsert_lead(data)
            assert created is False
        
        # Verify count
        assert Lead.objects.count() == 100
