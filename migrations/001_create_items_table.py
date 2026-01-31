"""
Migration: Create items table
Version: 001
Description: Creates the initial items table with id and name columns
"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_PATH


def upgrade():
    """Apply the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create migrations tracking table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if this migration has already been applied
    cursor.execute("SELECT 1 FROM _migrations WHERE name = ?", ("001_create_items_table",))
    if cursor.fetchone():
        print("Migration 001_create_items_table already applied. Skipping.")
        conn.close()
        return
    
    # Create items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    
    # Insert some sample data
    sample_items = [
        ("Apple",),
        ("Banana",),
        ("Cherry",),
    ]
    cursor.executemany("INSERT INTO items (name) VALUES (?)", sample_items)
    
    # Record this migration
    cursor.execute("INSERT INTO _migrations (name) VALUES (?)", ("001_create_items_table",))
    
    conn.commit()
    conn.close()
    print("Migration 001_create_items_table applied successfully.")


def downgrade():
    """Revert the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Drop items table
    cursor.execute("DROP TABLE IF EXISTS items")
    
    # Remove migration record
    cursor.execute("DELETE FROM _migrations WHERE name = ?", ("001_create_items_table",))
    
    conn.commit()
    conn.close()
    print("Migration 001_create_items_table reverted successfully.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run database migration")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade"],
        help="Migration action to perform"
    )
    
    args = parser.parse_args()
    
    if args.action == "upgrade":
        upgrade()
    elif args.action == "downgrade":
        downgrade()
