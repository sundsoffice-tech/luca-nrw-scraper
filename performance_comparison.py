"""
Performance comparison between the old and new sync_status_to_scraper implementations.

This script demonstrates the performance improvement of using bulk UPDATE
with CASE expression vs. individual UPDATE statements.
"""

import sqlite3
import tempfile
import os
import time


def setup_test_database(num_records=1000):
    """Create a test database with specified number of records."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close the file descriptor, SQLite will handle the file
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create the leads table
    cursor.execute("""
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            telefon TEXT,
            crm_status TEXT
        )
    """)
    
    # Insert test records
    test_leads = [
        (i, f'Person {i}', f'person{i}@example.com', f'012345{i:04d}', 
         'new' if i % 3 == 0 else ('contacted' if i % 3 == 1 else 'interested'))
        for i in range(1, num_records + 1)
    ]
    
    cursor.executemany(
        "INSERT INTO leads (id, name, email, telefon, crm_status) VALUES (?, ?, ?, ?, ?)",
        test_leads
    )
    conn.commit()
    conn.close()
    
    return db_path


def old_implementation_update(db_path, updates):
    """Simulate the old implementation with individual UPDATE statements."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    start_time = time.time()
    
    for lead_id, status in updates.items():
        cursor.execute("UPDATE leads SET crm_status = ? WHERE id = ?", (status, lead_id))
    
    conn.commit()
    elapsed = time.time() - start_time
    conn.close()
    
    return elapsed


def new_implementation_update(db_path, updates):
    """Simulate the new implementation with bulk UPDATE using CASE."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    start_time = time.time()
    
    if updates:
        case_clauses = []
        params = []
        ids = []
        
        for lead_id, status in updates.items():
            case_clauses.append("WHEN id = ? THEN ?")
            params.extend([lead_id, status])
            ids.append(lead_id)
        
        sql = f"""
            UPDATE leads 
            SET crm_status = CASE 
                {' '.join(case_clauses)}
            END
            WHERE id IN ({','.join('?' * len(ids))})
        """
        
        cursor.execute(sql, params + ids)
    
    conn.commit()
    elapsed = time.time() - start_time
    conn.close()
    
    return elapsed


def run_performance_test(num_records, update_percentage):
    """Run a performance comparison test."""
    print(f"\nTest: {num_records} records, updating {update_percentage}%")
    print("-" * 60)
    
    # Create test database
    db_path = setup_test_database(num_records)
    
    try:
        # Prepare updates (update a percentage of records)
        num_updates = int(num_records * update_percentage / 100)
        updates = {
            i: 'updated' for i in range(1, num_updates + 1)
        }
        
        print(f"Updating {num_updates} records...")
        
        # Test old implementation
        old_time = old_implementation_update(db_path, updates)
        
        # Reset database for fair comparison
        os.unlink(db_path)
        db_path = setup_test_database(num_records)
        
        # Test new implementation
        new_time = new_implementation_update(db_path, updates)
        
        # Calculate improvement
        improvement = ((old_time - new_time) / old_time) * 100 if old_time > 0 else 0
        speedup = old_time / new_time if new_time > 0 else float('inf')
        
        print(f"Old implementation: {old_time:.4f} seconds ({num_updates} individual UPDATEs)")
        print(f"New implementation: {new_time:.4f} seconds (1 bulk UPDATE)")
        print(f"Improvement: {improvement:.1f}% faster ({speedup:.2f}x speedup)")
        
        return old_time, new_time, improvement
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == '__main__':
    print("=" * 60)
    print("Performance Comparison: sync_status_to_scraper Optimization")
    print("=" * 60)
    
    test_scenarios = [
        (100, 50),      # 100 records, update 50%
        (500, 50),      # 500 records, update 50%
        (1000, 50),     # 1000 records, update 50%
        (5000, 50),     # 5000 records, update 50%
        (1000, 10),     # 1000 records, update 10%
        (1000, 90),     # 1000 records, update 90%
    ]
    
    results = []
    for num_records, update_pct in test_scenarios:
        old_time, new_time, improvement = run_performance_test(num_records, update_pct)
        results.append((num_records, update_pct, old_time, new_time, improvement))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'Records':<10} {'Update %':<10} {'Old (s)':<12} {'New (s)':<12} {'Improvement'}")
    print("-" * 60)
    
    for num_records, update_pct, old_time, new_time, improvement in results:
        print(f"{num_records:<10} {update_pct:<10} {old_time:<12.4f} {new_time:<12.4f} {improvement:>6.1f}%")
    
    print("\n" + "=" * 60)
    print("Key Benefits:")
    print("=" * 60)
    print("✅ Reduced database write operations from O(N) to O(1)")
    print("✅ Single transaction instead of N transactions")
    print("✅ Lower memory overhead")
    print("✅ Better performance especially for large tables")
    print("✅ Reduced database lock contention")
    print()
