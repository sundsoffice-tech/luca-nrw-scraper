"""
CSV Import utilities for leads.

Centralizes CSV import logic to avoid code duplication between
the Django management command and the API endpoint.
"""

import csv
import io
import logging
from typing import Dict, List, Optional, Union, BinaryIO, TextIO
from pathlib import Path

from django.db import transaction

logger = logging.getLogger(__name__)


class CSVImporter:
    """
    Centralized CSV import logic for leads.
    
    This class handles:
    - CSV delimiter detection
    - Field mapping (various column name formats)
    - Deduplication based on email/phone
    - Score-based updates
    - Statistics tracking
    
    Usage:
        importer = CSVImporter(dry_run=False, force_update=False)
        stats = importer.import_from_file('/path/to/file.csv')
        print(f"Imported: {stats['imported']}, Updated: {stats['updated']}")
    """
    
    def __init__(self, dry_run: bool = False, force_update: bool = False):
        """
        Initialize the CSV importer.
        
        Args:
            dry_run: If True, only validate without saving to database
            force_update: If True, update leads even if score is lower
        """
        self.dry_run = dry_run
        self.force_update = force_update
        self.stats = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
    
    def detect_delimiter(self, sample: str) -> str:
        """
        Automatically detect CSV delimiter from sample.
        
        Args:
            sample: First few lines of CSV file
            
        Returns:
            Detected delimiter character (';' or ',')
        """
        # If semicolon is present but comma is not, use semicolon
        if ';' in sample and ',' not in sample:
            return ';'
        return ','
    
    def parse_row(self, row: Dict[str, str]) -> Optional[Dict[str, any]]:
        """
        Parse a CSV row with field mapping.
        
        Handles multiple column name formats and extracts relevant fields.
        
        Args:
            row: Dictionary from csv.DictReader
            
        Returns:
            Dictionary with normalized field names, or None if no contact info
        """
        # Field mapping - support multiple column name variants
        email = (
            row.get('email') or 
            row.get('Email') or 
            row.get('E-Mail') or 
            ''
        ).strip() or None
        
        telefon = (
            row.get('telefon') or 
            row.get('Telefon') or 
            row.get('phone') or 
            ''
        ).strip() or None
        
        name = (
            row.get('name') or 
            row.get('Name') or 
            'Unbekannt'
        ).strip()
        
        # Skip if no contact info
        if not email and not telefon:
            return None
        
        # Parse score
        try:
            score_raw = (
                row.get('score') or 
                row.get('Score') or 
                row.get('quality_score') or 
                '50'
            )
            score = int(score_raw) if score_raw else 50
            score = max(0, min(100, score))  # Clamp to 0-100
        except (ValueError, TypeError):
            score = 50
        
        # Lead type mapping
        lead_type_raw = row.get('lead_type') or row.get('Lead-Typ') or ''
        
        # Additional fields
        company = (
            row.get('company_name') or 
            row.get('firma') or 
            row.get('Firma') or 
            ''
        ).strip()[:255] or None
        
        role = (
            row.get('rolle') or 
            row.get('position') or 
            row.get('Position') or 
            ''
        ).strip()[:255] or None
        
        location = (
            row.get('region') or 
            row.get('standort') or 
            row.get('Standort') or 
            ''
        ).strip()[:255] or None
        
        source_url = (
            row.get('quelle') or 
            row.get('source_url') or 
            ''
        ).strip()[:200] or None
        
        # Social profiles
        social_profile = row.get('social_profile_url') or ''
        linkedin_url = social_profile if 'linkedin' in social_profile.lower() else None
        xing_url = social_profile if 'xing' in social_profile.lower() else None
        
        return {
            'name': name,
            'email': email,
            'telefon': telefon,
            'quality_score': score,
            'lead_type': lead_type_raw,
            'company': company,
            'role': role,
            'location': location,
            'source_url': source_url,
            'linkedin_url': linkedin_url,
            'xing_url': xing_url,
        }
    
    def process_lead(self, data: Dict[str, any]) -> str:
        """
        Process a single lead (create or update).
        
        Args:
            data: Parsed lead data from parse_row()
            
        Returns:
            'imported', 'updated', or 'skipped'
        """
        # Import here to avoid circular imports
        from leads.models import Lead
        
        email = data['email']
        telefon = data['telefon']
        score = data['quality_score']
        
        # Check for existing lead (deduplication)
        existing = None
        if email:
            existing = Lead.objects.filter(email=email).first()
        if not existing and telefon:
            existing = Lead.objects.filter(telefon=telefon).first()
        
        if existing:
            # Update if score is better or force_update is True
            if self.force_update or score > existing.quality_score:
                if not self.dry_run:
                    existing.quality_score = score
                    
                    # Update other fields if better data available
                    if not existing.company and data.get('company'):
                        existing.company = data['company']
                    if not existing.role and data.get('role'):
                        existing.role = data['role']
                    if not existing.location and data.get('location'):
                        existing.location = data['location']
                    
                    existing.save()
                
                return 'updated'
            else:
                return 'skipped'
        else:
            # Create new lead
            if not self.dry_run:
                # Validate lead_type
                lead_type = data['lead_type']
                if lead_type not in dict(Lead.LeadType.choices):
                    lead_type = Lead.LeadType.UNKNOWN
                
                Lead.objects.create(
                    name=data['name'],
                    email=email,
                    telefon=telefon,
                    source=Lead.Source.SCRAPER,
                    source_url=data['source_url'],
                    quality_score=score,
                    lead_type=lead_type,
                    company=data['company'],
                    role=data['role'],
                    location=data['location'],
                    linkedin_url=data['linkedin_url'],
                    xing_url=data['xing_url'],
                )
            
            return 'imported'
    
    def import_from_file(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """
        Import leads from a CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Statistics dictionary with counts and errors
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Reset stats
        self.stats = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Try UTF-8 first, fallback to Latin-1
        encodings = ['utf-8', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Detect delimiter
                    sample = f.read(1024)
                    f.seek(0)
                    delimiter = self.detect_delimiter(sample)
                    
                    # Process CSV
                    reader = csv.DictReader(f, delimiter=delimiter)
                    
                    with transaction.atomic():
                        for i, row in enumerate(reader, 1):
                            try:
                                parsed = self.parse_row(row)
                                if parsed is None:
                                    self.stats['skipped'] += 1
                                    continue
                                
                                result = self.process_lead(parsed)
                                self.stats[result] += 1
                                
                            except Exception as e:
                                error_msg = f"Row {i}: {str(e)}"
                                self.stats['errors'].append(error_msg)
                                logger.error(error_msg)
                        
                        # Rollback if dry run
                        if self.dry_run:
                            transaction.set_rollback(True)
                
                return self.stats
                
            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    # Last encoding failed, re-raise
                    raise
                # Try next encoding
                continue
    
    def import_from_stream(self, stream: Union[BinaryIO, TextIO, str]) -> Dict[str, any]:
        """
        Import leads from a file stream or string.
        
        Useful for API endpoints that receive uploaded files.
        
        Args:
            stream: File stream (BinaryIO), text stream (TextIO), or string
            
        Returns:
            Statistics dictionary with counts and errors
        """
        # Reset stats
        self.stats = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Convert to string if needed
        if isinstance(stream, bytes):
            content = stream.decode('utf-8')
        elif hasattr(stream, 'read'):
            if hasattr(stream, 'mode') and 'b' in stream.mode:
                # Binary stream
                content = stream.read().decode('utf-8')
            else:
                # Text stream
                content = stream.read()
        else:
            content = stream
        
        # Detect delimiter
        sample = content[:1024]
        delimiter = self.detect_delimiter(sample)
        
        # Process CSV
        io_string = io.StringIO(content)
        reader = csv.DictReader(io_string, delimiter=delimiter)
        
        try:
            with transaction.atomic():
                for i, row in enumerate(reader, 1):
                    try:
                        parsed = self.parse_row(row)
                        if parsed is None:
                            self.stats['skipped'] += 1
                            continue
                        
                        result = self.process_lead(parsed)
                        self.stats[result] += 1
                        
                    except Exception as e:
                        error_msg = f"Row {i}: {str(e)}"
                        self.stats['errors'].append(error_msg)
                        logger.error(error_msg)
                
                # Rollback if dry run
                if self.dry_run:
                    transaction.set_rollback(True)
        
        except UnicodeDecodeError:
            # Try with Latin-1 encoding
            io_string = io.StringIO(content.encode('utf-8').decode('latin-1'))
            reader = csv.DictReader(io_string, delimiter=delimiter)
            
            with transaction.atomic():
                for i, row in enumerate(reader, 1):
                    try:
                        parsed = self.parse_row(row)
                        if parsed is None:
                            self.stats['skipped'] += 1
                            continue
                        
                        result = self.process_lead(parsed)
                        self.stats[result] += 1
                        
                    except Exception as e:
                        error_msg = f"Row {i}: {str(e)}"
                        self.stats['errors'].append(error_msg)
                        logger.error(error_msg)
                
                # Rollback if dry run
                if self.dry_run:
                    transaction.set_rollback(True)
        
        return self.stats
