import pytest
from tests.conftest import get_csrf_token


def test_books_catalog_and_filter(client):
    """Test viewing catalog and filtering by query and category."""
    response = client.get("/books?q=Algorithms")
    assert response.status_code == 200
    assert b"Introduction to Algorithms" in response.data

    cat_res = client.get("/books?category=Programming")
    assert cat_res.status_code == 200
    assert b"Learning Python" in cat_res.data


def test_admin_can_create_and_edit_book(admin_client):
    """Test that an administrator can add and edit a book."""
    csrf = get_csrf_token(admin_client)

    # 1. Create book
    create_res = admin_client.post("/books/add", data={
        "csrf_token": csrf,
        "title": "Computer Networks: A Systems Approach",
        "author": "Larry L. Peterson",
        "isbn": "978-0123850591",
        "publisher": "Morgan Kaufmann",
        "category": "Networking",
        "publication_year": "2011",
        "description": "Explores the key principles of computer networking.",
        "copies_count": "2",
        "shelf_location": "Stack N-1"
    }, follow_redirects=True)

    assert create_res.status_code == 200
    assert b"successfully added" in create_res.data
    assert b"Computer Networks" in create_res.data

    # 2. Edit book (using the newly created book ID or detail page)
    # Let's verify edit
    edit_res = admin_client.post("/books/1/edit", data={
        "csrf_token": csrf,
        "title": "Clean Code (Updated Edition)",
        "author": "Robert C. Martin",
        "isbn": "978-0132350884",
        "publisher": "Prentice Hall",
        "category": "Computer Science",
        "publication_year": "2008",
        "description": "Updated description for clean code."
    }, follow_redirects=True)

    assert edit_res.status_code == 200
    assert b"updated successfully" in edit_res.data


def test_duplicate_isbn_rejected(admin_client):
    """Test that adding another book with an existing ISBN is rejected."""
    csrf = get_csrf_token(admin_client)
    res = admin_client.post("/books/add", data={
        "csrf_token": csrf,
        "title": "Another Clean Code",
        "author": "Uncle Bob",
        "isbn": "978-0132350884",  # Already exists
        "publisher": "Prentice Hall",
        "category": "Computer Science",
        "publication_year": "2008",
        "description": "Duplicate book",
        "copies_count": "1",
        "shelf_location": "Stack A-1"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"already exists in the catalog" in res.data


def test_physical_copies_have_unique_accession(admin_client):
    """Test adding a physical copy with unique accession number and reject duplicate."""
    csrf = get_csrf_token(admin_client)

    # Add copy
    add_copy_res = admin_client.post("/books/1/copies/add", data={
        "csrf_token": csrf,
        "accession_number": "LIB-UNIQUE-999",
        "location": "Shelf Extra"
    }, follow_redirects=True)

    assert add_copy_res.status_code == 200
    assert b"added successfully" in add_copy_res.data

    # Attempt to add duplicate accession number
    dup_res = admin_client.post("/books/1/copies/add", data={
        "csrf_token": csrf,
        "accession_number": "LIB-UNIQUE-999",  # duplicate
        "location": "Shelf Extra 2"
    }, follow_redirects=True)

    assert dup_res.status_code == 200
    assert b"already exists" in dup_res.data


def test_cannot_delete_book_with_active_loans(admin_client):
    """Test that deleting a book whose copy is on loan is blocked."""
    csrf = get_csrf_token(admin_client)
    # Book 1 has borrowed copy LIB-CC-001
    delete_res = admin_client.post("/books/1/delete", data={
        "csrf_token": csrf
    }, follow_redirects=True)

    assert delete_res.status_code == 200
    assert b"Cannot delete" in delete_res.data
