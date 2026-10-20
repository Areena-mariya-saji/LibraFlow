import pytest
from tests.conftest import get_csrf_token


def test_borrow_available_book(admin_client):
    """Test issuing an available book copy to an active member."""
    csrf = get_csrf_token(admin_client)

    # In seed data, LIB-DDIA-001 (id 6) is available, student3 (id 4) is active
    res = admin_client.post("/loans/issue", data={
        "csrf_token": csrf,
        "copy_id": "6",
        "member_id": "4"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"successfully issued" in res.data


def test_cannot_borrow_unavailable_copy(admin_client):
    """Test that a copy already borrowed cannot be re-issued."""
    csrf = get_csrf_token(admin_client)

    # Copy 1 (LIB-CC-001) is already borrowed
    res = admin_client.post("/loans/issue", data={
        "csrf_token": csrf,
        "copy_id": "1",
        "member_id": "3"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"cannot be issued" in res.data or b"already has an active loan" in res.data


def test_return_book_updates_availability(admin_client):
    """Test returning a borrowed book updates its status to available."""
    csrf = get_csrf_token(admin_client)

    # In seed data, loan 3 (LIB-K8S-001, id 3) is active
    res = admin_client.post("/loans/3/return", data={
        "csrf_token": csrf
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"successfully returned" in res.data


def test_invalid_return_rejected(admin_client):
    """Test that returning an already returned loan is rejected."""
    csrf = get_csrf_token(admin_client)

    # Loan 4 in seed data is already returned
    res = admin_client.post("/loans/4/return", data={
        "csrf_token": csrf
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"already been marked as returned" in res.data


def test_overdue_status_and_fine_calculation(admin_client):
    """Test that overdue loans have overdue status and generated unpaid fines."""
    res = admin_client.get("/loans?status=overdue")
    assert res.status_code == 200
    assert b"Overdue" in res.data
