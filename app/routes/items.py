from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/items", tags=["items"])


class ItemCreate(BaseModel):
    name: str


class ItemUpdate(BaseModel):
    name: str


class ItemResponse(BaseModel):
    id: int
    name: str


@router.get("")
def list_items():
    """
    List all items from the database.
    Uses raw SQL query (no ORM).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM items ORDER BY id")
            rows = cursor.fetchall()
            items = [{"id": row["id"], "name": row["name"]} for row in rows]
            return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{item_id}")
def get_item(item_id: int):
    """
    Get a single item by ID.
    Uses raw SQL query (no ORM).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Item not found")
            return {"id": row["id"], "name": row["name"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("", status_code=201)
def create_item(item: ItemCreate):
    """
    Create a new item.
    Uses raw SQL query (no ORM).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items (name) VALUES (?)", (item.name,))
            item_id = cursor.lastrowid
            return {"id": item_id, "name": item.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    """
    Update an existing item.
    Uses raw SQL query (no ORM).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Check if item exists
            cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Item not found")
            # Update the item
            cursor.execute("UPDATE items SET name = ? WHERE id = ?", (item.name, item_id))
            return {"id": item_id, "name": item.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int):
    """
    Delete an item.
    Uses raw SQL query (no ORM).
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            # Check if item exists
            cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Item not found")
            # Delete the item
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
