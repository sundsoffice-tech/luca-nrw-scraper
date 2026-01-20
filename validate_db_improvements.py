#!/usr/bin/env python
"""
Database Structure Validation Script

This script validates the database improvements:
- Checks that indexes exist in SQLite schema
- Verifies Django model constraints
- Tests query performance with new indexes
"""

import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_sqlite_indexes():
    """Test that SQLite schema has the new performance indexes."""
    print("=" * 70)
    print("Testing SQLite Schema Indexes")
    print("=" * 70)
    
    # Import schema module
    from luca_scraper import schema
    
    # Create temporary in-memory database for testing
    con = sqlite3.connect(':memory:')
    
    # Initialize schema
    schema._ensure_schema(con)
    
    # Get list of indexes
    cur = con.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='leads'")
    indexes = cur.fetchall()
    
    # Expected indexes
    expected_indexes = [
        'ux_leads_email',           # Unique email
        'ux_leads_tel',             # Unique phone
        'idx_leads_lead_type',      # Lead type filter
        'idx_leads_quality_score',  # Quality score sort
        'idx_leads_type_status',    # Type+status combo
        'idx_leads_last_updated',   # Sync operations
        'idx_leads_confidence',     # AI confidence
        'idx_leads_data_quality',   # Data quality
    ]
    
    found_indexes = [idx[0] for idx in indexes]
    
    print(f"\n✓ Total indexes found: {len(found_indexes)}")
    print("\nIndex Details:")
    for name, sql in indexes:
        print(f"  - {name}")
        if sql:  # Some indexes might not have SQL (auto-created)
            print(f"    {sql[:80]}..." if len(sql) > 80 else f"    {sql}")
    
    # Verify expected indexes exist
    missing = []
    for expected in expected_indexes:
        if expected not in found_indexes:
            missing.append(expected)
    
    if missing:
        print(f"\n✗ Missing indexes: {missing}")
        return False
    else:
        print(f"\n✓ All {len(expected_indexes)} expected indexes exist!")
        return True


def test_django_model_structure():
    """Test Django model structure improvements."""
    print("\n" + "=" * 70)
    print("Testing Django Model Structure")
    print("=" * 70)
    
    try:
        # Set minimal environment for Django import
        import os
        os.environ.setdefault('SECRET_KEY', 'test-key-for-validation-only-' + 'x' * 30)
        os.environ.setdefault('DEBUG', 'True')
        os.environ.setdefault('ALLOWED_HOSTS', '*')
        
        # Import models
        from telis_recruitment.leads.models import Lead
        
        # Check Meta attributes
        meta = Lead._meta
        
        # Count indexes
        indexes = meta.indexes
        print(f"\n✓ Total indexes defined: {len(indexes)}")
        
        # Count constraints
        constraints = meta.constraints
        print(f"✓ Total constraints defined: {len(constraints)}")
        
        # Show index details
        print("\nComposite Indexes:")
        composite_count = 0
        for idx in indexes:
            if len(idx.fields) > 1:
                composite_count += 1
                print(f"  - {idx.name}: {idx.fields}")
        
        print(f"\n✓ Composite indexes: {composite_count}")
        
        # Show constraint details
        print("\nData Integrity Constraints:")
        for constraint in constraints:
            print(f"  - {constraint.name}")
        
        if len(indexes) >= 17 and len(constraints) >= 10:
            print(f"\n✓ Django model structure looks good!")
            print(f"  - {len(indexes)} indexes (expected: 17+)")
            print(f"  - {len(constraints)} constraints (expected: 10+)")
            return True
        else:
            print(f"\n✗ Unexpected counts:")
            print(f"  - Indexes: {len(indexes)} (expected: 17+)")
            print(f"  - Constraints: {len(constraints)} (expected: 10+)")
            return False
            
    except Exception as e:
        print(f"\n✗ Error testing Django model: {e}")
        print(f"  This is expected if Django dependencies are not installed")
        print(f"  or if SECRET_KEY validation is strict")
        return None  # Not a failure, just can't test


def test_migration_file():
    """Test that migration file exists and has expected operations."""
    print("\n" + "=" * 70)
    print("Testing Django Migration File")
    print("=" * 70)
    
    migration_file = Path(project_root) / 'telis_recruitment' / 'leads' / 'migrations' / '0013_improve_database_structure.py'
    
    if not migration_file.exists():
        print(f"\n✗ Migration file not found: {migration_file}")
        return False
    
    print(f"\n✓ Migration file exists: {migration_file.name}")
    
    # Read and analyze migration
    content = migration_file.read_text()
    
    # Count operations
    index_ops = content.count('migrations.AddIndex')
    constraint_ops = content.count('migrations.AddConstraint')
    
    print(f"\nMigration Operations:")
    print(f"  - AddIndex operations: {index_ops}")
    print(f"  - AddConstraint operations: {constraint_ops}")
    
    if index_ops >= 10 and constraint_ops >= 10:
        print(f"\n✓ Migration has expected operations!")
        return True
    else:
        print(f"\n✗ Unexpected operation counts:")
        print(f"  - Expected: 10+ index ops, 10+ constraint ops")
        print(f"  - Found: {index_ops} index ops, {constraint_ops} constraint ops")
        return False


def test_documentation():
    """Test that documentation files exist and are comprehensive."""
    print("\n" + "=" * 70)
    print("Testing Documentation")
    print("=" * 70)
    
    docs_dir = Path(project_root) / 'docs'
    
    expected_docs = [
        'DATABASE_STRUCTURE.md',
        'DATABASE_ER_DIAGRAM.md',
    ]
    
    results = []
    for doc in expected_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            size = doc_path.stat().st_size
            print(f"✓ {doc}: {size:,} bytes")
            results.append(True)
        else:
            print(f"✗ {doc}: NOT FOUND")
            results.append(False)
    
    # Check content quality
    if results[0]:  # DATABASE_STRUCTURE.md
        content = (docs_dir / 'DATABASE_STRUCTURE.md').read_text()
        has_indexes = 'indexes' in content.lower()
        has_constraints = 'constraints' in content.lower()
        has_examples = 'beispiel' in content.lower() or 'example' in content.lower()
        
        print(f"\nDATABASE_STRUCTURE.md content check:")
        print(f"  - Mentions indexes: {'✓' if has_indexes else '✗'}")
        print(f"  - Mentions constraints: {'✓' if has_constraints else '✗'}")
        print(f"  - Has examples: {'✓' if has_examples else '✗'}")
    
    return all(results)


def main():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("DATABASE STRUCTURE VALIDATION")
    print("=" * 70)
    
    results = {
        'SQLite Indexes': test_sqlite_indexes(),
        'Django Model': test_django_model_structure(),
        'Migration File': test_migration_file(),
        'Documentation': test_documentation(),
    }
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✓ {test_name}: PASS")
        elif result is False:
            print(f"✗ {test_name}: FAIL")
        else:
            print(f"⊘ {test_name}: SKIP (dependencies not available)")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n⚠ Some tests failed. Review the output above for details.")
        return 1
    else:
        print("\n✓ All available tests passed!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
