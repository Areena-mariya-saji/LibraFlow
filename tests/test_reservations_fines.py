import pytest
from tests.conftest import get_csrf_token


def test_member_can_reserve_eligible_book(member2_client):
    """Test member reserving a book they do not currently hold."""
    csrf = get_csrf_token(member2_client)

    # Book 3 (Designing Data-Intensive Applications)
    res = member2_client.post("/reservations/create/3", data={
        "csrf_token": csrf
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Reservation for" in res.data or b"recorded" in res.data


def test_member_cannot_access_other_member_private_loans(member1_client):
    """Test that a member's loans dashboard only displays their own loans."""
    res = member1_client.get("/member/loans")
    assert res.status_code == 200
    # member1 (Alex Kumar) borrowed Clean Code
    assert b"Clean Code" in res.data
    # member1 should NOT see other members' loans (Algorithms was loaned to Priya Sharma)
    assert b"Priya Sharma" not in res.data
    assert b"Introduction to Algorithms" not in res.data


def test_member_can_cancel_own_reservation(member1_client):
    """Test member cancelling their own pending reservation."""
    csrf = get_csrf_token(member1_client)

    # In seed data, reservation 1 is for member 1 (student1)
    res = member1_client.post("/reservations/1/cancel", data={
        "csrf_token": csrf
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"cancelled successfully" in res.data


def test_pay_or_waive_fine(admin_client):
    """Test administrator marking a fine as paid."""
    csrf = get_csrf_token(admin_client)

    # In seed data, fine 1 exists for overdue loan
    res = admin_client.post("/fines/1/pay", data={
        "csrf_token": csrf,
        "action": "paid"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"marked as paid" in res.data
