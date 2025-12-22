#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-time cleanup script to remove invalid leads from the database.

This script:
1. Identifies leads with invalid phone numbers
2. Identifies leads from blocked sources
3. Identifies test/probe entries
4. Removes all identified bad leads
5. Reports statistics before and after cleanup

Usage:
    python cleanup_bad_leads.py [--db DATABASE_PATH] [--dry-run]
"""

import sqlite3
import re
import sys
import argparse
from pathlib import Path


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


def cleanup_database(db_path: str, dry_run: bool = False):
    """
    Clean up invalid leads from database.
    
    Args:
        db_path: Path to SQLite database
        dry_run: If True, only report what would be deleted without actually deleting
    """
    print(f"Opening database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
    except sqlite3.Error as e:
        print(f"ERROR: Could not open database: {e}")
        return 1
    
    # Count leads before cleanup
    c.execute("SELECT COUNT(*) FROM leads")
    before = c.fetchone()[0]
    print(f"\n{'='*60}")
    print(f"Leads before cleanup: {before}")
    print(f"{'='*60}\n")
    
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
    
    print(f"\n{'='*60}")
    print(f"Leads to delete: {len(to_delete)}")
    print(f"{'='*60}\n")
    
    if to_delete:
        print("Details of leads to be deleted:\n")
        for lead_id, reason in to_delete[:20]:  # Show first 20
            print(f"  DELETE id={lead_id}: {reason}")
        
        if len(to_delete) > 20:
            print(f"  ... and {len(to_delete) - 20} more")
    
    # Perform deletion if not dry run
    if not dry_run:
        print(f"\n{'='*60}")
        print("Performing deletion...")
        print(f"{'='*60}\n")
        
        for lead_id, _ in to_delete:
            c.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        
        conn.commit()
        
        # Count leads after cleanup
        c.execute("SELECT COUNT(*) FROM leads")
        after = c.fetchone()[0]
        
        print(f"\n{'='*60}")
        print(f"CLEANUP COMPLETE")
        print(f"{'='*60}")
        print(f"Leads before:  {before}")
        print(f"Leads after:   {after}")
        print(f"Deleted:       {before - after}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("DRY RUN - No changes made")
        print(f"{'='*60}")
        print(f"Would delete:  {len(to_delete)} leads")
        print(f"Would remain:  {before - len(to_delete)} leads")
        print(f"{'='*60}\n")
    
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
    
    args = parser.parse_args()
    
    # Check if database exists
    if not Path(args.db).exists():
        print(f"ERROR: Database not found: {args.db}")
        return 1
    
    return cleanup_database(args.db, args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
