"""
Centralized CSV Import Utility

This module provides a reusable CSV import utility to avoid code duplication
between the management command and API endpoint.
"""
import csv
import logging
from typing import Dict, List, Optional, Tuple
from io import StringIO
from pathlib import Path

from django.db import transaction
from leads.models import Lead


logger = logging.getLogger(__name__)


class CSVImporter:
    """
    Centralized CSV import logic for Leads.
    
    Handles:
    - CSV delimiter detection
    - Field mapping (multiple column name variations)
    - Row parsing and validation
    - Lead creation/update with deduplication
    - Error tracking and reporting
    """
    
    def __init__(self, dry_run=False, force_update=False):
        """
        Initialize the CSV importer.
        
        Args:
            dry_run: If True, don't actually save changes to database
            force_update: If True, update existing leads even if score is lower
        """
        self.dry_run = dry_run
        self.force_update = force_update
        self.stats = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        self.error_details = []
    
    def detect_delimiter(self, sample: str) -> str:
        """
        Detect CSV delimiter automatically from a sample.
        
        Args:
            sample: First 1024 bytes of the CSV file
            
        Returns:
            str: Detected delimiter (';', ',', or '\t')
        """
        # Check for semicolon (common in European CSVs)
        if ';' in sample and ',' not in sample:
            return ';'
        
        # Check for tab
        if '\t' in sample:
            return '\t'
        
        # Default to comma
        return ','
    
    def parse_row(self, row: Dict[str, str]) -> Optional[Dict[str, any]]:
        """
        Parse a CSV row with field mapping.
        
        Maps various column names to standardized field names.
        
        Args:
            row: Dictionary from CSV DictReader
            
        Returns:
            Dict with parsed data, or None if row should be skipped
        """
        # Extract and normalize fields with multiple possible column names
        email = (
            row.get('email') or 
            row.get('Email') or 
            row.get('E-Mail') or 
            row.get('e-mail') or 
            ''
        ).strip() or None
        
        telefon = (
            row.get('telefon') or 
            row.get('Telefon') or 
            row.get('phone') or 
            row.get('Phone') or 
            row.get('Handy') or 
            ''
        ).strip() or None
        
        name = (
            row.get('name') or 
            row.get('Name') or 
            'Unbekannt'
        ).strip()
        
        # Skip if no contact information
        if not email and not telefon:
            return None
        
        # Parse score with better logging
        score_raw = (
            row.get('score') or 
            row.get('Score') or 
            row.get('quality_score') or 
            '50'
        )
        try:
            score = int(score_raw) if score_raw else 50
            score = max(0, min(100, score))  # Clamp to 0-100
        except (ValueError, TypeError):
            logger.warning(f"Invalid score value '{score_raw}' for {name}, defaulting to 50")
            score = 50
        
        # Extract other fields
        company = (
            row.get('company_name') or 
            row.get('firma') or 
            row.get('Firma') or 
            row.get('company') or 
            ''
        ).strip()[:255] or None
        
        role = (
            row.get('rolle') or 
            row.get('position') or 
            row.get('Position') or 
            row.get('role') or 
            ''
        ).strip()[:255] or None
        
        location = (
            row.get('region') or 
            row.get('standort') or 
            row.get('Standort') or 
            row.get('location') or 
            ''
        ).strip()[:255] or None
        
        source_url = (
            row.get('quelle') or 
            row.get('source_url') or 
            row.get('url') or 
            ''
        ).strip()[:200] or None
        
        # Lead type mapping
        lead_type_raw = (
            row.get('lead_type') or 
            row.get('Lead-Typ') or 
            ''
        ).strip()
        
        if lead_type_raw in dict(Lead.LeadType.choices):
            lead_type = lead_type_raw
        else:
            lead_type = Lead.LeadType.UNKNOWN
        
        # Social profile URLs
        social_profile = row.get('social_profile_url', '')
        linkedin_url = None
        xing_url = None
        
        if 'linkedin' in social_profile.lower():
            linkedin_url = social_profile
        elif 'xing' in social_profile.lower():
            xing_url = social_profile
        
        return {
            'name': name[:255],
            'email': email,
            'telefon': telefon,
            'quality_score': score,
            'lead_type': lead_type,
            'company': company,
            'role': role,
            'location': location,
            'source_url': source_url,
            'linkedin_url': linkedin_url,
            'xing_url': xing_url,
        }
    
    def process_lead(self, data: Dict[str, any], row_index: int) -> str:
        """
        Process a lead (create or update).
        
        Args:
            data: Parsed lead data
            row_index: Row number for error reporting
            
        Returns:
            str: 'imported', 'updated', or 'skipped'
        """
        try:
            # Check for existing lead (deduplicate by email or phone)
            existing = None
            if data['email']:
                existing = Lead.objects.filter(email=data['email']).first()
            if not existing and data['telefon']:
                existing = Lead.objects.filter(telefon=data['telefon']).first()
            
            if existing:
                # Update existing lead if score is higher or force_update is True
                if self.force_update or data['quality_score'] > existing.quality_score:
                    if not self.dry_run:
                        existing.quality_score = data['quality_score']
                        
                        # Update other fields only if they're empty
                        if not existing.company and data.get('company'):
                            existing.company = data['company']
                        if not existing.role and data.get('role'):
                            existing.role = data['role']
                        if not existing.location and data.get('location'):
                            existing.location = data['location']
                        if not existing.linkedin_url and data.get('linkedin_url'):
                            existing.linkedin_url = data['linkedin_url']
                        if not existing.xing_url and data.get('xing_url'):
                            existing.xing_url = data['xing_url']
                        
                        existing.save()
                    
                    logger.info(
                        f"Updated lead: {data['name']} "
                        f"(Score: {existing.quality_score} → {data['quality_score']})"
                    )
                    return 'updated'
                else:
                    logger.debug(f"Skipped existing lead with higher/equal score: {data['name']}")
                    return 'skipped'
            else:
                # Create new lead
                if not self.dry_run:
                    Lead.objects.create(
                        name=data['name'],
                        email=data['email'],
                        telefon=data['telefon'],
                        source=Lead.Source.SCRAPER,
                        source_url=data['source_url'],
                        quality_score=data['quality_score'],
                        lead_type=data['lead_type'],
                        company=data['company'],
                        role=data['role'],
                        location=data['location'],
                        linkedin_url=data['linkedin_url'],
                        xing_url=data['xing_url'],
                    )
                
                logger.info(
                    f"Imported new lead: {data['name']} "
                    f"({data['email'] or data['telefon']}) [Score: {data['quality_score']}]"
                )
                return 'imported'
        
        except Exception as e:
            error_msg = f"Row {row_index}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.stats['errors'].append(error_msg)
            self.error_details.append({
                'row': row_index,
                'data': data,
                'error': str(e)
            })
            raise
    
    def import_from_file(self, file_path: str) -> Dict[str, int]:
        """
        Import leads from a CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Dict with import statistics
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try UTF-8 encoding first
        encodings = ['utf-8', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return self._import_from_stream(f, encoding)
            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    raise
                logger.warning(f"Failed to read with {encoding}, trying next encoding")
                continue
    
    def import_from_stream(self, stream, encoding='utf-8') -> Dict[str, int]:
        """
        Import leads from a file-like stream.
        
        Args:
            stream: File-like object containing CSV data
            encoding: Character encoding
            
        Returns:
            Dict with import statistics
        """
        return self._import_from_stream(stream, encoding)
    
    def _import_from_stream(self, stream, encoding='utf-8') -> Dict[str, int]:
        """
        Internal method to import from a stream.
        
        Args:
            stream: File-like object
            encoding: Character encoding
            
        Returns:
            Dict with statistics
        """
        # Detect delimiter
        sample = stream.read(1024)
        stream.seek(0)
        delimiter = self.detect_delimiter(sample)
        
        logger.info(f"Detected delimiter: '{delimiter}', encoding: {encoding}")
        
        reader = csv.DictReader(stream, delimiter=delimiter)
        rows = list(reader)
        
        logger.info(f"Processing {len(rows)} rows")
        
        with transaction.atomic():
            for i, row in enumerate(rows, 1):
                try:
                    # Parse row
                    data = self.parse_row(row)
                    if data is None:
                        self.stats['skipped'] += 1
                        logger.debug(f"Row {i}: Skipped (no contact info)")
                        continue
                    
                    # Process lead
                    result = self.process_lead(data, i)
                    if result == 'imported':
                        self.stats['imported'] += 1
                    elif result == 'updated':
                        self.stats['updated'] += 1
                    else:
                        self.stats['skipped'] += 1
                
                except Exception as e:
                    # Error already logged in process_lead
                    pass
            
            if self.dry_run:
                # Rollback transaction in dry run mode
                transaction.set_rollback(True)
        
        return self.stats
    
    def get_error_report(self) -> str:
        """
        Generate a detailed error report.
        
        Returns:
            str: Formatted error report
        """
        if not self.error_details:
            return "No errors occurred during import."
        
        report = ["CSV Import Errors:", "=" * 60, ""]
        
        for error in self.error_details[:10]:  # Limit to first 10 errors
            report.append(f"Row {error['row']}:")
            report.append(f"  Data: {error['data']}")
            report.append(f"  Error: {error['error']}")
            report.append("")
        
        if len(self.error_details) > 10:
            report.append(f"... and {len(self.error_details) - 10} more errors")
        
        return "\n".join(report)
