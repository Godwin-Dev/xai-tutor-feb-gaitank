import requests
import json
import time

BASE_URL = "http://localhost:8000"

def log(msg):
    print(f"[TEST] {msg}")

def test_invoices():
    # Wait for service to be up
    log("Waiting for service to be ready...")
    for _ in range(10):
        try:
            resp = requests.get(f"{BASE_URL}/docs")
            if resp.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        log("Service not reachable. Exiting.")
        return

    # 1. List Invoices (Should be empty initially)
    log("1. Listing Invoices...")
    resp = requests.get(f"{BASE_URL}/invoices")
    print(f"Status: {resp.status_code}, Body: {resp.json()}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    # 2. Create Invoice
    log("2. Creating Invoice...")
    payload = {
        "client_id": 1,  # Acme Corp
        "invoice_no": "INV-001",
        "issue_date": "2023-10-27",
        "due_date": "2023-11-27",
        "items": [
            {"product_id": 1, "quantity": 2},  # 2 * Widget A (10.0) = 20.0
            {"product_id": 3, "quantity": 1}   # 1 * Gadget X (50.0) = 50.0
        ]
    }
    # Total should be 70.0 + 10% tax = 77.0
    resp = requests.post(f"{BASE_URL}/invoices", json=payload)
    print(f"Status: {resp.status_code}, Body: {resp.json()}")
    assert resp.status_code == 201
    invoice_id = resp.json()["id"]
    assert resp.json()["total_amount"] == 77.0

    # 3. Get Invoice
    log(f"3. Getting Invoice {invoice_id}...")
    resp = requests.get(f"{BASE_URL}/invoices/{invoice_id}")
    print(f"Status: {resp.status_code}, Body: {resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["invoice_no"] == "INV-001"
    assert len(resp.json()["items"]) == 2

    # 4. List Invoices again
    log("4. Listing Invoices again...")
    resp = requests.get(f"{BASE_URL}/invoices")
    print(f"Status: {resp.status_code}, Body: {resp.json()}")
    assert len(resp.json()) >= 1

    # 5. Delete Invoice
    log(f"5. Deleting Invoice {invoice_id}...")
    resp = requests.delete(f"{BASE_URL}/invoices/{invoice_id}")
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 204

    # 6. Verify Deletion
    log("6. Verifying Deletion...")
    resp = requests.get(f"{BASE_URL}/invoices/{invoice_id}")
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 404

    log("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_invoices()
