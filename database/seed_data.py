import sys
from pathlib import Path
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_db, init_db, sync_overdue_and_fines
from config import Config


def seed(db_path=None):
    if db_path is None:
        db_path = Config.DATABASE_PATH

    print(f"[*] Seeding data into {db_path}...")
    init_db(db_path)
    conn = get_db(db_path)

    # 1. Clear existing data in reverse order of foreign keys
    conn.execute("DELETE FROM fines;")
    conn.execute("DELETE FROM reservations;")
    conn.execute("DELETE FROM loans;")
    conn.execute("DELETE FROM book_copies;")
    conn.execute("DELETE FROM books;")
    conn.execute("DELETE FROM users;")
    try:
        conn.execute("DELETE FROM sqlite_sequence;")
    except Exception:
        pass

    # 2. Seed Users
    # Admin: Admin@123, Students: Student@123
    users_data = [
        ("System Administrator", "admin", "admin@libraflow.edu", generate_password_hash("Admin@123"), "admin", "active"),
        ("Alex Kumar", "student1", "alex.kumar@student.libraflow.edu", generate_password_hash("Student@123"), "member", "active"),
        ("Priya Sharma", "student2", "priya.sharma@student.libraflow.edu", generate_password_hash("Student@123"), "member", "active"),
        ("Rahul Verma", "student3", "rahul.verma@student.libraflow.edu", generate_password_hash("Student@123"), "member", "active"),
        ("Ananya Sen", "student4", "ananya.sen@student.libraflow.edu", generate_password_hash("Student@123"), "member", "suspended"),
    ]

    conn.executemany("""
        INSERT INTO users (full_name, username, email, password_hash, role, account_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, users_data)

    user_map = {row["username"]: row["id"] for row in conn.execute("SELECT id, username FROM users").fetchall()}

    # 3. Seed Books
    books_data = [
        ("978-0132350884", "Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "Prentice Hall", "Computer Science", 2008, "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees. A must-read handbook for professional software engineers."),
        ("978-0262033848", "Introduction to Algorithms (CLRS)", "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein", "MIT Press", "Computer Science", 2009, "A comprehensive update of the leading algorithms textbook, covering graphs, dynamic programming, greedy algorithms, and data structures."),
        ("978-1491950357", "Designing Data-Intensive Applications", "Martin Kleppmann", "O'Reilly Media", "Database Systems", 2017, "The definitive guide to the architecture of modern data systems, storage engines, distributed consensus, and stream processing."),
        ("978-1492043454", "Kubernetes: Up and Running", "Brendan Burns, Joe Beda, Kelsey Hightower", "O'Reilly Media", "Cloud & DevOps", 2019, "Legendary guide on container orchestration, service discovery, rolling updates, and scalable cloud-native architectures."),
        ("978-0134685991", "Effective Java", "Joshua Bloch", "Addison-Wesley Professional", "Programming", 2018, "The definitive best practices guide for the Java platform, covering generics, enums, lambdas, streams, and concurrency."),
        ("978-1449355739", "Learning Python (5th Edition)", "Mark Lutz", "O'Reilly Media", "Programming", 2013, "Comprehensive in-depth introduction to Python core concepts, object-oriented design, modules, and metaprogramming.")
    ]

    conn.executemany("""
        INSERT INTO books (isbn, title, author, publisher, category, publication_year, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, books_data)

    book_map = {row["isbn"]: row["id"] for row in conn.execute("SELECT id, isbn FROM books").fetchall()}

    # 4. Seed Book Copies
    copies_data = [
        (book_map["978-0132350884"], "LIB-CC-001", "borrowed", "Stack A-1"),
        (book_map["978-0132350884"], "LIB-CC-002", "available", "Stack A-1"),
        (book_map["978-0132350884"], "LIB-CC-003", "available", "Stack A-1"),
        
        (book_map["978-0262033848"], "LIB-ALGO-001", "borrowed", "Stack A-2"),
        (book_map["978-0262033848"], "LIB-ALGO-002", "reserved", "Stack A-2"),
        
        (book_map["978-1491950357"], "LIB-DDIA-001", "available", "Stack B-1"),
        (book_map["978-1491950357"], "LIB-DDIA-002", "available", "Stack B-1"),
        
        (book_map["978-1492043454"], "LIB-K8S-001", "borrowed", "Stack C-1"),
        (book_map["978-1492043454"], "LIB-K8S-002", "available", "Stack C-1"),
        
        (book_map["978-0134685991"], "LIB-EJ-001", "available", "Stack A-3"),
        
        (book_map["978-1449355739"], "LIB-LP-001", "available", "Stack A-4"),
        (book_map["978-1449355739"], "LIB-LP-002", "maintenance", "Repair Workshop"),
    ]

    conn.executemany("""
        INSERT INTO book_copies (book_id, accession_number, status, location)
        VALUES (?, ?, ?, ?)
    """, copies_data)

    copy_map = {row["accession_number"]: row["id"] for row in conn.execute("SELECT id, accession_number FROM book_copies").fetchall()}

    # 5. Seed Loans
    today = date.today()
    loans_data = [
        # Loan 1: Active, issued 7 days ago to Alex Kumar (due in 7 days)
        (copy_map["LIB-CC-001"], user_map["student1"], (today - timedelta(days=7)).isoformat(), (today + timedelta(days=7)).isoformat(), None, "active"),
        # Loan 2: Overdue, issued 25 days ago to Priya Sharma (due 11 days ago)
        (copy_map["LIB-ALGO-001"], user_map["student2"], (today - timedelta(days=25)).isoformat(), (today - timedelta(days=11)).isoformat(), None, "overdue"),
        # Loan 3: Active, issued 2 days ago to Rahul Verma (due in 12 days)
        (copy_map["LIB-K8S-001"], user_map["student3"], (today - timedelta(days=2)).isoformat(), (today + timedelta(days=12)).isoformat(), None, "active"),
        # Loan 4: Returned on time, issued 30 days ago, returned 16 days ago
        (copy_map["LIB-CC-002"], user_map["student1"], (today - timedelta(days=30)).isoformat(), (today - timedelta(days=16)).isoformat(), (today - timedelta(days=16)).isoformat(), "returned"),
    ]

    conn.executemany("""
        INSERT INTO loans (book_copy_id, member_id, issue_date, due_date, return_date, loan_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, loans_data)

    # 6. Seed Fines for overdue loan
    overdue_loan = conn.execute("""
        SELECT id FROM loans WHERE loan_status = 'overdue' LIMIT 1
    """).fetchone()

    if overdue_loan:
        conn.execute("""
            INSERT INTO fines (loan_id, amount, reason, payment_status, recorded_date)
            VALUES (?, 11.00, 'Overdue fine for 11 day(s)', 'unpaid', ?)
        """, (overdue_loan["id"], (today - timedelta(days=11)).isoformat()))

    # 7. Seed Reservations
    conn.execute("""
        INSERT INTO reservations (book_id, member_id, reservation_date, reservation_status)
        VALUES (?, ?, ?, 'pending')
    """, (book_map["978-0262033848"], user_map["student1"], (today - timedelta(days=3)).isoformat()))

    conn.commit()
    sync_overdue_and_fines(conn)
    conn.close()
    print("[+] Database successfully seeded with accounts and library records.")
    print("    - Admin: username='admin', password='Admin@123'")
    print("    - Student 1: username='student1', password='Student@123'")
    print("    - Student 2: username='student2', password='Student@123'")
    print("    - Student 3: username='student3', password='Student@123'")


if __name__ == "__main__":
    seed()
