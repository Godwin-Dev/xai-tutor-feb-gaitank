"""
Migration: Create invoicing tables
Version: 002
Description: Creates clients, products, invoices, and invoice_items tables with seed data.
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
    
    # Check if this migration has already been applied
    cursor.execute("SELECT 1 FROM _migrations WHERE name = ?", ("002_create_invoicing_tables",))
    if cursor.fetchone():
        print("Migration 002_create_invoicing_tables already applied. Skipping.")
        conn.close()
        return

    # Create clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            company_reg_no TEXT NOT NULL
        )
    """)

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Create invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL UNIQUE,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            client_id INTEGER NOT NULL,
            tax_amount REAL NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)

    # Create invoice_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # Seed Clients
    seed_clients = [
        ("Acme Corp", "123 Business Rd, Tech City", "REG123456"),
        ("Globex Inc", "456 Global Way, World Town", "REG654321"),
        ("Soylent Corp", "789 Green St, Eco City", "REG987654")
    ]
    cursor.executemany("INSERT INTO clients (name, address, company_reg_no) VALUES (?, ?, ?)", seed_clients)

    # Seed Products
    seed_products = [
        ("Widget A", 10.0),
        ("Widget B", 25.50),
        ("Gadget X", 50.0),
        ("Gadget Y", 99.99),
        ("Service Hour", 150.0)
    ]
    cursor.executemany("INSERT INTO products (name, price) VALUES (?, ?)", seed_products)
    
    # Record this migration
    cursor.execute("INSERT INTO _migrations (name) VALUES (?)", ("002_create_invoicing_tables",))
    
    conn.commit()
    conn.close()
    print("Migration 002_create_invoicing_tables applied successfully.")


def downgrade():
    """Revert the migration."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Drop tables in reverse order of dependencies
    cursor.execute("DROP TABLE IF EXISTS invoice_items")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS clients")
    
    # Remove migration record
    cursor.execute("DELETE FROM _migrations WHERE name = ?", ("002_create_invoicing_tables",))
    
    conn.commit()
    conn.close()
    print("Migration 002_create_invoicing_tables reverted successfully.")
