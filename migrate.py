"""
Database Migration Runner

This script runs all pending migrations in order or reverts them.
"""

import os
import glob
import importlib.util
import argparse
import sqlite3

from app.database import DATABASE_PATH


def get_migration_files():
    """Get all migration files sorted by version number."""
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    pattern = os.path.join(migrations_dir, "[0-9][0-9][0-9]_*.py")
    files = glob.glob(pattern)
    return sorted(files)


def load_migration_module(filepath):
    """Dynamically load a migration module."""
    module_name = os.path.basename(filepath).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_migrations(action="upgrade"):
    """Run all migrations."""
    migration_files = get_migration_files()
    
    if action == "downgrade":
        migration_files = reversed(migration_files)
    
    for filepath in migration_files:
        module = load_migration_module(filepath)
        if action == "upgrade":
            module.upgrade()
        elif action == "downgrade":
            module.downgrade()


def list_migrations():
    """List all migrations and their status."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Ensure migrations table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Get applied migrations
    cursor.execute("SELECT name, applied_at FROM _migrations ORDER BY id")
    applied = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    
    # Get all migration files
    migration_files = get_migration_files()
    
    print("\nMigrations Status:")
    print("-" * 60)
    
    for filepath in migration_files:
        name = os.path.basename(filepath).replace(".py", "")
        if name in applied:
            print(f"[APPLIED] {name} (at {applied[name]})")
        else:
            print(f"[PENDING] {name}")
    
    print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database migration runner")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade", "list"],
        help="Migration action: upgrade (apply all), downgrade (revert all), list (show status)"
    )
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_migrations()
    else:
        run_migrations(args.action)
