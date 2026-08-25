import pytest
from fastapi.testclient import TestClient
from main import app
from config import DEFAULT_APPROVER_EMAIL, ADMINISTRATOR_EMAIL

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.3"

def test_expense_submission_and_translation():
    """
    TS-38: A requester enters the expense name and purpose in Russian.
    The agent shows an English translation and stores only the confirmed English version.
    """
    payload = {
        "SubmittedBy": "requester1@test.com",
        "Program": "Office",
        "ExpenseName": "Канцелярия",
        "AmountUSD": 150.0,
        "PurchasePurpose": "Бумага для принтера",
        "ExpenseCategory": "Office Supplies"
    }

    response = client.post("/api/expenses/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["was_translated"] is True
    
    record = data["record"]
    assert record["ExpenseName"] == "Office Supplies"
    assert record["PurchasePurpose"] == "Printer Paper"
    assert record["ExpenseID"].startswith("EXP-")

def test_login_endpoint():
    # Valid credentials
    response = client.post("/api/auth/login", json={"email": "approver@test.com", "password": "Password123!"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["name"] == "Dmytro Kachurovskyy"

    # Invalid password
    response_bad = client.post("/api/auth/login", json={"email": "approver@test.com", "password": "wrong"})
    assert response_bad.status_code == 401

def test_approver_delegation_endpoints():
    # Delegate to Admin
    resp_del = client.post(f"/api/approver/delegate?requested_by={DEFAULT_APPROVER_EMAIL}")
    assert resp_del.status_code == 200
    assert resp_del.json()["active_approver"] == ADMINISTRATOR_EMAIL

    # Unauthorized user attempts to return
    resp_fail = client.post("/api/approver/return?requested_by=requester1@test.com")
    assert resp_fail.status_code == 403

    # Approver returns role
    resp_ret = client.post(f"/api/approver/return?requested_by={DEFAULT_APPROVER_EMAIL}")
    assert resp_ret.status_code == 200
    assert resp_ret.json()["active_approver"] == DEFAULT_APPROVER_EMAIL
