"""
Simple cleanup script for the scraper database.

This script removes low-quality leads from the scraper database:
- Leads with probe/test names
- Leads with invalid phone numbers (fake patterns, too short)
- Leads without phone numbers

Usage: python cleanup.py
"""
import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'scraper.db'

def main():
    """Main cleanup function."""
    logger.info(f"Starting cleanup of {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count leads before cleanup
        c.execute("SELECT COUNT(*) FROM leads")
        count_before = c.fetchone()[0]
        logger.info(f"Leads before cleanup: {count_before}")
        
        # Delete leads with probe/test names (parameterized query)
        logger.info("Removing test/probe entries...")
        c.execute("DELETE FROM leads WHERE name LIKE ?", ('%_probe_%',))
        deleted_probe = c.rowcount
        logger.info(f"  Deleted {deleted_probe} probe entries")
        
        # Delete leads with fake phone numbers (parameterized query)
        logger.info("Removing leads with fake phone numbers...")
        c.execute("DELETE FROM leads WHERE telefon LIKE ?", ('%1234567890%',))
        deleted_fake = c.rowcount
        logger.info(f"  Deleted {deleted_fake} leads with fake numbers")
        
        # Delete leads without phone numbers (parameterized query)
        logger.info("Removing leads without phone numbers...")
        c.execute("DELETE FROM leads WHERE telefon IS NULL OR telefon = ?", ('',))
        deleted_no_phone = c.rowcount
        logger.info(f"  Deleted {deleted_no_phone} leads without phone")
        
        # Delete leads with too short phone numbers (parameterized query)
        logger.info("Removing leads with too short phone numbers...")
        c.execute("DELETE FROM leads WHERE LENGTH(telefon) < ?", (12,))
        deleted_short = c.rowcount
        logger.info(f"  Deleted {deleted_short} leads with short phone numbers")
        
        # Commit changes
        conn.commit()
        
        # Count leads after cleanup
        c.execute("SELECT COUNT(*) FROM leads")
        count_after = c.fetchone()[0]
        total_deleted = count_before - count_after
        
        logger.info("="*60)
        logger.info("Cleanup completed successfully")
        logger.info(f"Leads before:  {count_before}")
        logger.info(f"Leads after:   {count_after}")
        logger.info(f"Total deleted: {total_deleted}")
        logger.info("="*60)
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        if conn:
            conn.close()
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())