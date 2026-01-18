#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-time cleanup script to remove invalid leads from the database.

This script:
1. Creates a backup of the database before making changes
2. Identifies leads with invalid phone numbers
3. Identifies leads from blocked sources
4. Identifies test/probe entries
5. Removes all identified bad leads using parameterized queries
6. Reports statistics before and after cleanup

Usage:
    python cleanup_bad_leads.py [--db DATABASE_PATH] [--dry-run] [--no-backup]
"""

import sqlite3
import re
import sys
import argparse
import logging
import shutil
from pathlib import Path
from datetime import datetime


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_backup(db_path: str) -> str:
    """
    Create a backup of the database before making changes.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        str: Path to the backup file
        
    Raises:
        ValueError: If the file is not a valid SQLite database
        IOError: If backup fails
    """
    db_path = Path(db_path)
    
    # Verify it's a SQLite database by trying to open it
    try:
        conn = sqlite3.connect(str(db_path))
        # Check if it has the leads table
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        if not cursor.fetchone():
            logger.warning("Database does not contain 'leads' table")
        conn.close()
    except sqlite3.Error as e:
        raise ValueError(f"Not a valid SQLite database: {e}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    
    logger.info(f"Creating backup: {backup_path}")
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backup created successfully ({backup_path.stat().st_size} bytes)")
    except Exception as e:
        raise IOError(f"Failed to create backup: {e}")
    
    return str(backup_path)


def is_valid_phone(phone):
    """
    Check if phone number is valid.
    
    Valid if:
    - Starts with mobile prefix (015, 016, 017)
    - At least 11 digits
    - No fake patterns
    """
    if not phone:
        return False
    
    digits = re.sub(r'[^\d]', '', phone)
    
    # Normalize to German format
    if digits.startswith('49'):
        digits = '0' + digits[2:]
    elif digits.startswith('0049'):
        digits = '0' + digits[4:]
    
    # Must start with mobile prefix
    if not digits.startswith(('015', '016', '017')):
        return False
    
    # Length check
    if len(digits) < 11 or len(digits) > 15:
        return False
    
    # Check for fake patterns
    if '1234567890' in digits:
        return False
    
    # Check for too many repeating digits
    if re.search(r'(\d)\1{5,}', digits):
        return False
    
    return True


def is_blocked_source(url):
    """Check if URL is from a blocked source."""
    if not url:
        return True
    
    blocked = [
        'facebook.com', 'tiktok.com', 'snapchat.com', '.pdf', 
        'googleapis.com', 'wikipedia', 'youtube', 'karriere.',
        'sporef.idu.edu', 'patentimages', 'twitter.com',
        'instagram.com', 'linkedin.com', 'xing.com',
        'stepstone.de', 'indeed.com', 'monster.de',
        'jobs.de', 'jobware.de', 'stellenanzeigen.de',
        'storage.google', 'voris.wolterskluwer',
    ]
    
    url_lower = url.lower()
    return any(b in url_lower for b in blocked)


def is_test_entry(name):
    """Check if name is a test entry."""
    if not name:
        return False
    
    test_patterns = [
        '_probe_',
        'test',
        'beispiel',
        'muster',
    ]
    
    name_lower = name.lower()
    return any(pattern in name_lower for pattern in test_patterns)


def cleanup_database(db_path: str, dry_run: bool = False, create_backup_file: bool = True):
    """
    Clean up invalid leads from database.
    
    Args:
        db_path: Path to SQLite database
        dry_run: If True, only report what would be deleted without actually deleting
        create_backup_file: If True, create a backup before making changes
    """
    logger.info(f"Opening database: {db_path}")
    
    # Create backup before making changes (unless disabled or dry run)
    if create_backup_file and not dry_run:
        try:
            backup_path = create_backup(db_path)
            logger.info(f"Backup saved to: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            logger.error("Aborting to prevent data loss")
            return 1
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
    except sqlite3.Error as e:
        logger.error(f"ERROR: Could not open database: {e}")
        return 1
    
    # Count leads before cleanup
    c.execute("SELECT COUNT(*) FROM leads")
    before = c.fetchone()[0]
    logger.info(f"\n{'='*60}")
    logger.info(f"Leads before cleanup: {before}")
    logger.info(f"{'='*60}\n")
    
    # Identify leads to delete
    c.execute("SELECT id, telefon, quelle, name FROM leads")
    to_delete = []
    
    for row in c.fetchall():
        lead_id, phone, source, name = row
        
        # Check phone validity
        if not is_valid_phone(phone):
            to_delete.append((lead_id, f"Ungültige Telefonnummer: {phone}"))
        # Check source
        elif is_blocked_source(source):
            source_preview = source[:50] if source else 'None'
            to_delete.append((lead_id, f"Geblockte Quelle: {source_preview}"))
        # Check for test entries
        elif is_test_entry(name):
            to_delete.append((lead_id, f"Test-Eintrag: {name}"))
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Leads to delete: {len(to_delete)}")
    logger.info(f"{'='*60}\n")
    
    if to_delete:
        logger.info("Details of leads to be deleted:\n")
        for lead_id, reason in to_delete[:20]:  # Show first 20
            logger.info(f"  DELETE id={lead_id}: {reason}")
        
        if len(to_delete) > 20:
            logger.info(f"  ... and {len(to_delete) - 20} more")
    
    # Perform deletion if not dry run (using parameterized queries)
    if not dry_run:
        logger.info(f"\n{'='*60}")
        logger.info("Performing deletion...")
        logger.info(f"{'='*60}\n")
        
        for lead_id, _ in to_delete:
            # Use parameterized query to prevent SQL injection
            c.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        
        conn.commit()
        
        # Count leads after cleanup
        c.execute("SELECT COUNT(*) FROM leads")
        after = c.fetchone()[0]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"CLEANUP COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Leads before:  {before}")
        logger.info(f"Leads after:   {after}")
        logger.info(f"Deleted:       {before - after}")
        logger.info(f"{'='*60}\n")
    else:
        logger.info(f"\n{'='*60}")
        logger.info("DRY RUN - No changes made")
        logger.info(f"{'='*60}")
        logger.info(f"Would delete:  {len(to_delete)} leads")
        logger.info(f"Would remain:  {before - len(to_delete)} leads")
        logger.info(f"{'='*60}\n")
    
    conn.close()
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Clean up invalid leads from database'
    )
    parser.add_argument(
        '--db',
        default='scraper.db',
        help='Path to SQLite database (default: scraper.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating a backup before deletion'
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if not Path(args.db).exists():
        logger.error(f"ERROR: Database not found: {args.db}")
        return 1
    
    return cleanup_database(args.db, args.dry_run, not args.no_backup)


if __name__ == '__main__':
    sys.exit(main())
