#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple cleanup script for removing test/invalid leads.

Uses parametrized queries to prevent SQL injection.
"""

import sqlite3
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = 'scraper.db'

logger.info(f"Opening database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Count before cleanup
c.execute("SELECT COUNT(*) FROM leads")
vorher = c.fetchone()[0]
logger.info(f"Leads before cleanup: {vorher}")

# Delete invalid leads using parametrized queries
logger.info("Deleting test/probe entries...")
c.execute("DELETE FROM leads WHERE name LIKE ?", ('%_probe_%',))
deleted_probe = c.rowcount

logger.info("Deleting leads with fake phone numbers...")
c.execute("DELETE FROM leads WHERE telefon LIKE ?", ('%1234567890%',))
deleted_fake = c.rowcount

logger.info("Deleting leads without phone numbers...")
c.execute("DELETE FROM leads WHERE telefon IS NULL OR telefon = ?", ('',))
deleted_no_phone = c.rowcount

logger.info("Deleting leads with too short phone numbers...")
c.execute("DELETE FROM leads WHERE LENGTH(telefon) < ?", (12,))
deleted_short = c.rowcount

conn.commit()

# Count after cleanup
c.execute("SELECT COUNT(*) FROM leads")
nachher = c.fetchone()[0]

logger.info(f"\n{'='*50}")
logger.info(f"CLEANUP COMPLETE")
logger.info(f"{'='*50}")
logger.info(f"Leads before:        {vorher}")
logger.info(f"Leads after:         {nachher}")
logger.info(f"Total deleted:       {vorher - nachher}")
logger.info(f"  - Probe entries:   {deleted_probe}")
logger.info(f"  - Fake phones:     {deleted_fake}")
logger.info(f"  - No phone:        {deleted_no_phone}")
logger.info(f"  - Short phones:    {deleted_short}")
logger.info(f"{'='*50}")

conn.close()
logger.info("Database closed")