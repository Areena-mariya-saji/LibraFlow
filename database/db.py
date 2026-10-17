import sqlite3
from pathlib import Path
from datetime import datetime, date
from flask import current_app, g, has_app_context

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"


def get_db(db_path=None):
    """
    Get a database connection.
    If called within a Flask application context, the connection is cached on `flask.g`.
    """
    if db_path is None:
        if has_app_context() and current_app.config.get("DATABASE_PATH"):
            db_path = current_app.config["DATABASE_PATH"]
        else:
            db_path = str(Path(__file__).resolve().parent / "libraflow.db")

    if has_app_context():
        if "_database" not in g:
            # Ensure parent directory exists if not in-memory
            if db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            g._database = conn
        return g._database
    else:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


def close_db(e=None):
    """Closes the current database connection if it exists."""
    if has_app_context():
        db = g.pop("_database", None)
        if db is not None:
            db.close()


def init_db(db_path=None):
    """Initializes the database using schema.sql."""
    conn = get_db(db_path)
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    if not has_app_context():
        conn.close()


def sync_overdue_and_fines(conn=None, fine_per_day=1.00):
    """
    Checks active loans past their due date, marks them overdue,
    and updates or inserts unpaid fines.
    """
    should_close = False
    if conn is None:
        conn = get_db()
    
    today = date.today().isoformat()

    # Find active loans that are past due
    overdue_loans = conn.execute("""
        SELECT id, member_id, due_date,
               CAST((julianday(?) - julianday(due_date)) AS INTEGER) as days_overdue
        FROM loans
        WHERE return_date IS NULL
          AND due_date < ?
    """, (today, today)).fetchall()

    for loan in overdue_loans:
        days = max(1, int(loan["days_overdue"]))
        fine_amount = round(days * fine_per_day, 2)

        # Update loan status to overdue
        conn.execute("""
            UPDATE loans
            SET loan_status = 'overdue'
            WHERE id = ? AND loan_status != 'overdue'
        """, (loan["id"],))

        # Check existing fine for this loan
        existing_fine = conn.execute("""
            SELECT id, payment_status FROM fines WHERE loan_id = ?
        """, (loan["id"],)).fetchone()

        if existing_fine is None:
            conn.execute("""
                INSERT INTO fines (loan_id, amount, reason, payment_status, recorded_date)
                VALUES (?, ?, ?, 'unpaid', ?)
            """, (loan["id"], fine_amount, f"Overdue fine for {days} day(s)", today))
        elif existing_fine["payment_status"] == "unpaid":
            conn.execute("""
                UPDATE fines
                SET amount = ?, reason = ?
                WHERE id = ?
            """, (fine_amount, f"Overdue fine for {days} day(s)", existing_fine["id"]))

    conn.commit()
