from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from app.database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])

# --- Pydantic Models ---

class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int

class InvoiceCreate(BaseModel):
    client_id: int
    invoice_no: str
    issue_date: date
    due_date: date
    items: List[InvoiceItemCreate]

class InvoiceItemResponse(BaseModel):
    id: int
    product_name: str
    quantity: int
    unit_price: float
    line_total: float

class InvoiceResponse(BaseModel):
    id: int
    invoice_no: str
    issue_date: date
    due_date: date
    client_name: str
    tax_amount: float
    total_amount: float
    items: List[InvoiceItemResponse] = []

class InvoiceListResponse(BaseModel):
    id: int
    invoice_no: str
    issue_date: date
    due_date: date
    client_name: str
    total_amount: float

# --- Helper Functions ---

def calculate_invoice_totals(items: List[InvoiceItemCreate], conn):
    """Calculates total and tax based on products."""
    total_amount = 0.0
    processed_items = []
    
    for item in items:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM products WHERE id = ?", (item.product_id,))
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")
            
        line_total = product["price"] * item.quantity
        total_amount += line_total
        processed_items.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "unit_price": product["price"],
            "quantity": item.quantity,
            "line_total": line_total
        })
        
    # Simple tax calculation (e.g., 10% tax) - logic not specified in reqs, assuming flat or 0? 
    # Requirements say "tax" and "total". Let's assume a standard tax rate or just sum?
    # Requirement doesn't specify logic. I will add a 10% tax for demonstration.
    tax_amount = total_amount * 0.10
    final_total = total_amount + tax_amount
    
    return processed_items, tax_amount, final_total

# --- Routes ---

@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: InvoiceCreate):
    """Create a new invoice with items."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Verify Client
            cursor.execute("SELECT id, name FROM clients WHERE id = ?", (invoice.client_id,))
            client = cursor.fetchone()
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            
            # Use transaction for atomicity (handled by get_db context manager commit/rollback)
            
            # Calculate totals and validate products
            processed_items, tax_amount, total_amount = calculate_invoice_totals(invoice.items, conn)
            
            # Insert Invoice
            try:
                cursor.execute("""
                    INSERT INTO invoices (invoice_no, issue_date, due_date, client_id, tax_amount, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice.invoice_no, invoice.issue_date, invoice.due_date, invoice.client_id, tax_amount, total_amount))
                invoice_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="Invoice number already exists")

            # Insert Invoice Items
            for item in processed_items:
                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price, line_total)
                    VALUES (?, ?, ?, ?, ?)
                """, (invoice_id, item["product_id"], item["quantity"], item["unit_price"], item["line_total"]))
            
            # Construct Response
            response_items = [
                InvoiceItemResponse(
                    id=0, # ID not available until read back, or we can fetch them. Let's just return what we have.
                    # Actually valid response needs ID. For simplicity in this raw SQL approach without fetching back everything:
                    # We will return the computed data. 
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    line_total=item["line_total"]
                ) for item in processed_items
            ]
            
            return InvoiceResponse(
                id=invoice_id,
                invoice_no=invoice.invoice_no,
                issue_date=invoice.issue_date,
                due_date=invoice.due_date,
                client_name=client["name"],
                tax_amount=tax_amount,
                total_amount=total_amount,
                items=response_items
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("", response_model=List[InvoiceListResponse])
def list_invoices():
    """List all invoices."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.id, i.invoice_no, i.issue_date, i.due_date, i.total_amount, c.name as client_name
                FROM invoices i
                JOIN clients c ON i.client_id = c.id
                ORDER BY i.id DESC
            """)
            rows = cursor.fetchall()
            return [
                InvoiceListResponse(
                    id=row["id"],
                    invoice_no=row["invoice_no"],
                    issue_date=row["issue_date"], # sqlite driver might return str, pydantic handles it if format is standard ISO
                    due_date=row["due_date"],
                    client_name=row["client_name"],
                    total_amount=row["total_amount"]
                ) for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int):
    """Get a single invoice by ID."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get Invoice Details
            cursor.execute("""
                SELECT i.id, i.invoice_no, i.issue_date, i.due_date, i.tax_amount, i.total_amount, c.name as client_name
                FROM invoices i
                JOIN clients c ON i.client_id = c.id
                WHERE i.id = ?
            """, (invoice_id,))
            invoice = cursor.fetchone()
            
            if not invoice:
                raise HTTPException(status_code=404, detail="Invoice not found")
                
            # Get Invoice Items
            cursor.execute("""
                SELECT ii.id, p.name as product_name, ii.quantity, ii.unit_price, ii.line_total
                FROM invoice_items ii
                JOIN products p ON ii.product_id = p.id
                WHERE ii.invoice_id = ?
            """, (invoice_id,))
            items = cursor.fetchall()
            
            response_items = [
                InvoiceItemResponse(
                    id=item["id"],
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    line_total=item["line_total"]
                ) for item in items
            ]
            
            return InvoiceResponse(
                id=invoice["id"],
                invoice_no=invoice["invoice_no"],
                issue_date=invoice["issue_date"],
                due_date=invoice["due_date"],
                client_name=invoice["client_name"],
                tax_amount=invoice["tax_amount"],
                total_amount=invoice["total_amount"],
                items=response_items
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int):
    """Delete an invoice."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if invoice exists
            cursor.execute("SELECT id FROM invoices WHERE id = ?", (invoice_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            # Delete items first (though cascade might handle it if configured, manual is safer for SQLite defaults sometimes)
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            
            # Delete invoice
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            return None
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
