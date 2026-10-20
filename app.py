import os
import secrets
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import config_by_name
from database.db import get_db, close_db, sync_overdue_and_fines


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Register database teardown
    app.teardown_appcontext(close_db)

    # -------------------------------------------------------------
    # CSRF & Security Utilities
    # -------------------------------------------------------------
    def generate_csrf_token():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_hex(24)
        return session["_csrf_token"]

    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
        else:
            conn = get_db()
            g.user = conn.execute(
                "SELECT id, full_name, username, email, role, account_status FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

    @app.before_request
    def csrf_protect():
        if request.method == "POST":
            # Exclude health check and API endpoints from CSRF
            if request.path.startswith("/health") or request.path.startswith("/api/"):
                return
            token = session.get("_csrf_token", None)
            form_token = request.form.get("csrf_token")
            if not token or token != form_token:
                flash("Security session expired or invalid CSRF token. Please try again.", "danger")
                abort(400, description="Invalid CSRF Token")

    # -------------------------------------------------------------
    # Authentication & Authorization Decorators
    # -------------------------------------------------------------
    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login", next=request.path))
            if g.user["account_status"] != "active":
                flash("Your account has been suspended or deactivated. Contact the administrator.", "danger")
                session.clear()
                return redirect(url_for("login"))
            return view(**kwargs)
        return wrapped_view

    def roles_required(*allowed_roles):
        def decorator(view):
            @wraps(view)
            def wrapped_view(**kwargs):
                if g.user is None:
                    flash("Please log in to access this page.", "warning")
                    return redirect(url_for("login"))
                if g.user["role"] not in allowed_roles:
                    flash("Access denied: You do not have permission to view that resource.", "danger")
                    abort(403)
                return view(**kwargs)
            return wrapped_view
        return decorator

    # -------------------------------------------------------------
    # Context Processor for Global Template Variables
    # -------------------------------------------------------------
    @app.context_processor
    def inject_global_data():
        return {
            "current_year": datetime.now().year,
            "current_user": getattr(g, "user", None),
            "app_name": "LibraFlow",
            "today_date": date.today().isoformat()
        }

    # -------------------------------------------------------------
    # Health Check Endpoint (Docker / K8s probes / AWS)
    # -------------------------------------------------------------
    @app.route("/health", methods=["GET"])
    def health():
        try:
            conn = get_db()
            conn.execute("SELECT 1").fetchone()
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            return jsonify({
                "status": "degraded",
                "service": "LibraFlow Library Management System",
                "database": db_status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 500

        return jsonify({
            "status": "healthy",
            "service": "LibraFlow Library Management System",
            "database": db_status,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    # -------------------------------------------------------------
    # Public & Auth Routes
    # -------------------------------------------------------------
    @app.route("/")
    def index():
        conn = get_db()
        # Fetch summary stats for homepage showcase
        total_books = conn.execute("SELECT COUNT(*) as count FROM books").fetchone()["count"]
        total_copies = conn.execute("SELECT COUNT(*) as count FROM book_copies").fetchone()["count"]
        available_copies = conn.execute("SELECT COUNT(*) as count FROM book_copies WHERE status = 'available'").fetchone()["count"]
        
        # Featured recent books
        recent_books = conn.execute("""
            SELECT b.*, 
                   (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id) as copy_count,
                   (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') as avail_count
            FROM books b
            ORDER BY b.id DESC LIMIT 4
        """).fetchall()

        return render_template(
            "index.html",
            total_books=total_books,
            total_copies=total_copies,
            available_copies=available_copies,
            recent_books=recent_books
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user is not None:
            if g.user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("member_dashboard"))

        if request.method == "POST":
            identifier = request.form.get("identifier", "").strip()
            password = request.form.get("password", "")

            if not identifier or not password:
                flash("Please enter both username/email and password.", "danger")
                return render_template("login.html")

            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (identifier, identifier)
            ).fetchone()

            if user is None or not check_password_hash(user["password_hash"], password):
                flash("Invalid credentials. Please verify your username/email and password.", "danger")
                return render_template("login.html")

            if user["account_status"] != "active":
                flash("Your account is currently inactive or suspended. Please contact the administrator.", "danger")
                return render_template("login.html")

            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]

            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("member_dashboard"))

        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if g.user is not None:
            return redirect(url_for("index"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            # Validation
            if not full_name or not username or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if len(username) < 3:
                flash("Username must be at least 3 characters long.", "danger")
                return render_template("register.html")

            if "@" not in email or "." not in email:
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("register.html")

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("register.html")

            conn = get_db()
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            ).fetchone()

            if existing:
                flash("A user with this username or email already exists.", "danger")
                return render_template("register.html")

            # Newly registered users default to member role
            conn.execute("""
                INSERT INTO users (full_name, username, email, password_hash, role, account_status)
                VALUES (?, ?, ?, ?, 'member', 'active')
            """, (full_name, username, email, generate_password_hash(password)))
            conn.commit()

            flash("Registration successful! You can now log in with your credentials.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been safely logged out.", "info")
        return redirect(url_for("login"))

    # -------------------------------------------------------------
    # Dashboards
    # -------------------------------------------------------------
    @app.route("/admin/dashboard")
    @login_required
    @roles_required("admin")
    def admin_dashboard():
        conn = get_db()
        sync_overdue_and_fines(conn, app.config["FINE_PER_DAY"])

        total_books = conn.execute("SELECT COUNT(*) as c FROM books").fetchone()["c"]
        total_copies = conn.execute("SELECT COUNT(*) as c FROM book_copies").fetchone()["c"]
        available_copies = conn.execute("SELECT COUNT(*) as c FROM book_copies WHERE status = 'available'").fetchone()["c"]
        borrowed_copies = conn.execute("SELECT COUNT(*) as c FROM book_copies WHERE status = 'borrowed'").fetchone()["c"]
        registered_members = conn.execute("SELECT COUNT(*) as c FROM users WHERE role = 'member'").fetchone()["c"]
        active_loans = conn.execute("SELECT COUNT(*) as c FROM loans WHERE return_date IS NULL").fetchone()["c"]
        overdue_loans = conn.execute("SELECT COUNT(*) as c FROM loans WHERE loan_status = 'overdue'").fetchone()["c"]
        pending_reservations = conn.execute("SELECT COUNT(*) as c FROM reservations WHERE reservation_status = 'pending'").fetchone()["c"]
        total_unpaid_fines = conn.execute("SELECT COALESCE(SUM(amount), 0) as s FROM fines WHERE payment_status = 'unpaid'").fetchone()["s"]

        recent_loans = conn.execute("""
            SELECT l.id, l.issue_date, l.due_date, l.loan_status,
                   u.full_name as member_name, u.username,
                   b.title as book_title, bc.accession_number
            FROM loans l
            JOIN users u ON l.member_id = u.id
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN books b ON bc.book_id = b.id
            ORDER BY l.id DESC LIMIT 5
        """).fetchall()

        recent_members = conn.execute("""
            SELECT id, full_name, username, email, role, account_status, created_at
            FROM users
            ORDER BY id DESC LIMIT 5
        """).fetchall()

        return render_template(
            "admin_dashboard.html",
            total_books=total_books,
            total_copies=total_copies,
            available_copies=available_copies,
            borrowed_copies=borrowed_copies,
            registered_members=registered_members,
            active_loans=active_loans,
            overdue_loans=overdue_loans,
            pending_reservations=pending_reservations,
            total_unpaid_fines=total_unpaid_fines,
            recent_loans=recent_loans,
            recent_members=recent_members
        )

    @app.route("/librarian/dashboard")
    @login_required
    def librarian_dashboard():
        return redirect(url_for("admin_dashboard"))

    @app.route("/member/dashboard")
    @login_required
    def member_dashboard():
        conn = get_db()
        sync_overdue_and_fines(conn, app.config["FINE_PER_DAY"])
        user_id = g.user["id"]

        active_loans = conn.execute("""
            SELECT l.id, l.issue_date, l.due_date, l.loan_status,
                   b.title, b.author, bc.accession_number, bc.location
            FROM loans l
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN books b ON bc.book_id = b.id
            WHERE l.member_id = ? AND l.return_date IS NULL
            ORDER BY l.due_date ASC
        """, (user_id,)).fetchall()

        reservations = conn.execute("""
            SELECT r.id, r.reservation_date, r.reservation_status,
                   b.id as book_id, b.title, b.author,
                   (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') as available_copies
            FROM reservations r
            JOIN books b ON r.book_id = b.id
            WHERE r.member_id = ?
            ORDER BY r.id DESC
        """, (user_id,)).fetchall()

        fines = conn.execute("""
            SELECT f.id, f.amount, f.reason, f.payment_status, f.recorded_date,
                   b.title as book_title
            FROM fines f
            JOIN loans l ON f.loan_id = l.id
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN books b ON bc.book_id = b.id
            WHERE l.member_id = ?
            ORDER BY f.id DESC
        """, (user_id,)).fetchall()

        total_unpaid = sum(f["amount"] for f in fines if f["payment_status"] == "unpaid")

        return render_template(
            "member_dashboard.html",
            active_loans=active_loans,
            reservations=reservations,
            fines=fines,
            total_unpaid=total_unpaid
        )

    # -------------------------------------------------------------
    # Books Catalog & Details
    # -------------------------------------------------------------
    @app.route("/books")
    def books():
        conn = get_db()
        query = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        availability = request.args.get("availability", "").strip()

        # Build dynamic query
        sql = """
            SELECT b.*,
                   (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id) as total_copies,
                   (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') as available_copies
            FROM books b
            WHERE 1=1
        """
        params = []

        if query:
            sql += " AND (b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)"
            term = f"%{query}%"
            params.extend([term, term, term])

        if category:
            sql += " AND b.category = ?"
            params.append(category)

        if availability == "available":
            sql += " AND (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') > 0"
        elif availability == "unavailable":
            sql += " AND (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') = 0"

        sql += " ORDER BY b.title ASC"
        books_list = conn.execute(sql, params).fetchall()

        # Get unique categories for dropdown filter
        categories = [row["category"] for row in conn.execute("SELECT DISTINCT category FROM books ORDER BY category").fetchall()]

        return render_template(
            "books.html",
            books=books_list,
            categories=categories,
            search_query=query,
            selected_category=category,
            selected_availability=availability
        )

    @app.route("/books/<int:book_id>")
    def book_detail(book_id):
        conn = get_db()
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            flash("Book not found.", "warning")
            return redirect(url_for("books"))

        copies = conn.execute("""
            SELECT * FROM book_copies
            WHERE book_id = ?
            ORDER BY accession_number ASC
        """, (book_id,)).fetchall()

        available_count = sum(1 for c in copies if c["status"] == "available")

        # Check if current user has already reserved or loaned this book
        user_has_loan = False
        user_has_reservation = False
        if g.user:
            user_has_loan = bool(conn.execute("""
                SELECT 1 FROM loans l
                JOIN book_copies bc ON l.book_copy_id = bc.id
                WHERE bc.book_id = ? AND l.member_id = ? AND l.return_date IS NULL
            """, (book_id, g.user["id"])).fetchone())

            user_has_reservation = bool(conn.execute("""
                SELECT 1 FROM reservations
                WHERE book_id = ? AND member_id = ? AND reservation_status = 'pending'
            """, (book_id, g.user["id"])).fetchone())

        return render_template(
            "book_detail.html",
            book=book,
            copies=copies,
            available_count=available_count,
            user_has_loan=user_has_loan,
            user_has_reservation=user_has_reservation
        )

    @app.route("/books/add", methods=["GET", "POST"])
    @login_required
    @roles_required("admin")
    def add_book():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            isbn = request.form.get("isbn", "").strip()
            publisher = request.form.get("publisher", "").strip()
            category = request.form.get("category", "").strip()
            pub_year_raw = request.form.get("publication_year", "").strip()
            description = request.form.get("description", "").strip()
            num_copies_raw = request.form.get("copies_count", "1").strip()
            shelf_location = request.form.get("shelf_location", "Main Stack").strip()

            if not (title and author and isbn and publisher and category and pub_year_raw):
                flash("Please complete all required book metadata fields.", "danger")
                return render_template("book_form.html", action="Add", book={})

            try:
                publication_year = int(pub_year_raw)
                num_copies = max(1, int(num_copies_raw))
            except ValueError:
                flash("Publication year and copies count must be valid integers.", "danger")
                return render_template("book_form.html", action="Add", book={})

            conn = get_db()
            existing = conn.execute("SELECT id FROM books WHERE isbn = ?", (isbn,)).fetchone()
            if existing:
                flash("A book with this ISBN already exists in the catalog.", "danger")
                return render_template("book_form.html", action="Add", book=request.form)

            cursor = conn.execute("""
                INSERT INTO books (isbn, title, author, publisher, category, publication_year, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (isbn, title, author, publisher, category, publication_year, description))
            new_book_id = cursor.lastrowid

            # Create the initial physical copies with unique accession numbers
            prefix = "".join(filter(str.isalnum, isbn))[-4:]
            for i in range(1, num_copies + 1):
                accession_num = f"LF-{prefix}-{i:03d}"
                # Handle possible collision in accession numbers
                check_acc = conn.execute("SELECT id FROM book_copies WHERE accession_number = ?", (accession_num,)).fetchone()
                if check_acc:
                    accession_num = f"LF-{prefix}-{secrets.token_hex(2).upper()}"
                
                conn.execute("""
                    INSERT INTO book_copies (book_id, accession_number, status, location)
                    VALUES (?, ?, 'available', ?)
                """, (new_book_id, accession_num, shelf_location))

            conn.commit()
            flash(f"Book '{title}' successfully added with {num_copies} copy/copies.", "success")
            return redirect(url_for("book_detail", book_id=new_book_id))

        return render_template("book_form.html", action="Add", book={})

    @app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
    @login_required
    @roles_required("admin")
    def edit_book(book_id):
        conn = get_db()
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            flash("Book not found.", "warning")
            return redirect(url_for("books"))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            isbn = request.form.get("isbn", "").strip()
            publisher = request.form.get("publisher", "").strip()
            category = request.form.get("category", "").strip()
            pub_year_raw = request.form.get("publication_year", "").strip()
            description = request.form.get("description", "").strip()

            if not (title and author and isbn and publisher and category and pub_year_raw):
                flash("All required book fields must be provided.", "danger")
                return render_template("book_form.html", action="Edit", book=book)

            try:
                publication_year = int(pub_year_raw)
            except ValueError:
                flash("Publication year must be an integer.", "danger")
                return render_template("book_form.html", action="Edit", book=book)

            # Check if updated ISBN collides with another book
            duplicate_isbn = conn.execute(
                "SELECT id FROM books WHERE isbn = ? AND id != ?",
                (isbn, book_id)
            ).fetchone()
            if duplicate_isbn:
                flash("Another book already exists with this ISBN.", "danger")
                return render_template("book_form.html", action="Edit", book=book)

            conn.execute("""
                UPDATE books
                SET title = ?, author = ?, isbn = ?, publisher = ?, category = ?, publication_year = ?, description = ?
                WHERE id = ?
            """, (title, author, isbn, publisher, category, publication_year, description, book_id))
            conn.commit()

            flash(f"Book '{title}' details updated successfully.", "success")
            return redirect(url_for("book_detail", book_id=book_id))

        return render_template("book_form.html", action="Edit", book=book)

    @app.route("/books/<int:book_id>/delete", methods=["POST"])
    @login_required
    @roles_required("admin")
    def delete_book(book_id):
        conn = get_db()
        book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            flash("Book not found.", "warning")
            return redirect(url_for("books"))

        # Safety Guard: Check if any copy is currently on active loan
        active_loan = conn.execute("""
            SELECT l.id FROM loans l
            JOIN book_copies bc ON l.book_copy_id = bc.id
            WHERE bc.book_id = ? AND l.return_date IS NULL
        """, (book_id,)).fetchone()

        if active_loan:
            flash(f"Cannot delete '{book['title']}': One or more physical copies are currently borrowed.", "danger")
            return redirect(url_for("book_detail", book_id=book_id))

        # Delete associated copies and book (cascades where configured)
        conn.execute("DELETE FROM reservations WHERE book_id = ?", (book_id,))
        conn.execute("DELETE FROM book_copies WHERE book_id = ?", (book_id,))
        conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()

        flash(f"Book '{book['title']}' and its copies have been removed.", "success")
        return redirect(url_for("books"))

    @app.route("/books/<int:book_id>/copies/add", methods=["POST"])
    @login_required
    @roles_required("admin")
    def add_book_copy(book_id):
        accession_number = request.form.get("accession_number", "").strip()
        location = request.form.get("location", "").strip()

        if not accession_number or not location:
            flash("Accession number and location are required.", "danger")
            return redirect(url_for("book_detail", book_id=book_id))

        conn = get_db()
        existing = conn.execute("SELECT id FROM book_copies WHERE accession_number = ?", (accession_number,)).fetchone()
        if existing:
            flash("A book copy with this accession number already exists. Accession numbers must be unique.", "danger")
            return redirect(url_for("book_detail", book_id=book_id))

        conn.execute("""
            INSERT INTO book_copies (book_id, accession_number, status, location)
            VALUES (?, ?, 'available', ?)
        """, (book_id, accession_number, location))
        conn.commit()

        flash(f"Copy '{accession_number}' added successfully.", "success")
        return redirect(url_for("book_detail", book_id=book_id))

    # -------------------------------------------------------------
    # Loans & Returns Management
    # -------------------------------------------------------------
    @app.route("/loans")
    @login_required
    @roles_required("admin")
    def loans():
        conn = get_db()
        sync_overdue_and_fines(conn, app.config["FINE_PER_DAY"])

        status_filter = request.args.get("status", "").strip()
        sql = """
            SELECT l.id, l.issue_date, l.due_date, l.return_date, l.loan_status,
                   u.full_name as member_name, u.username, u.email,
                   b.title as book_title, bc.accession_number, bc.location,
                   (SELECT amount FROM fines f WHERE f.loan_id = l.id) as fine_amount,
                   (SELECT payment_status FROM fines f WHERE f.loan_id = l.id) as fine_payment_status
            FROM loans l
            JOIN users u ON l.member_id = u.id
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN books b ON bc.book_id = b.id
            WHERE 1=1
        """
        params = []
        if status_filter:
            sql += " AND l.loan_status = ?"
            params.append(status_filter)

        sql += " ORDER BY l.id DESC"
        loans_list = conn.execute(sql, params).fetchall()

        # Available copies for quick issue modal/form
        available_copies = conn.execute("""
            SELECT bc.id, bc.accession_number, bc.location, b.title as book_title
            FROM book_copies bc
            JOIN books b ON bc.book_id = b.id
            WHERE bc.status = 'available'
            ORDER BY b.title ASC
        """).fetchall()

        active_members = conn.execute("""
            SELECT id, full_name, username FROM users
            WHERE role = 'member' AND account_status = 'active'
            ORDER BY full_name ASC
        """).fetchall()

        return render_template(
            "loans.html",
            loans=loans_list,
            status_filter=status_filter,
            available_copies=available_copies,
            active_members=active_members
        )

    @app.route("/loans/issue", methods=["POST"])
    @login_required
    @roles_required("admin")
    def issue_book():
        copy_id = request.form.get("copy_id")
        member_id = request.form.get("member_id")

        if not copy_id or not member_id:
            flash("Please select both a valid physical copy and a member.", "danger")
            return redirect(url_for("loans"))

        conn = get_db()

        # Verify member is valid and active
        member = conn.execute("SELECT id, full_name, account_status FROM users WHERE id = ?", (member_id,)).fetchone()
        if not member:
            flash("Selected member does not exist.", "danger")
            return redirect(url_for("loans"))
        if member["account_status"] != "active":
            flash("Cannot issue book: Member account is not active.", "danger")
            return redirect(url_for("loans"))

        # Verify copy exists and is currently available
        copy = conn.execute("SELECT id, status, accession_number, book_id FROM book_copies WHERE id = ?", (copy_id,)).fetchone()
        if not copy:
            flash("Physical book copy not found.", "danger")
            return redirect(url_for("loans"))

        if copy["status"] != "available":
            flash(f"Copy {copy['accession_number']} is currently '{copy['status']}' and cannot be issued.", "danger")
            return redirect(url_for("loans"))

        # Guard: Check for duplicate active loan on the same physical copy
        existing_loan = conn.execute("""
            SELECT id FROM loans WHERE book_copy_id = ? AND return_date IS NULL
        """, (copy_id,)).fetchone()
        if existing_loan:
            flash(f"Copy {copy['accession_number']} already has an active loan recorded.", "danger")
            return redirect(url_for("loans"))

        today = date.today()
        loan_period = app.config["LOAN_PERIOD_DAYS"]
        due_date = today + timedelta(days=loan_period)

        # Atomic transaction: Update copy status & insert loan
        conn.execute("UPDATE book_copies SET status = 'borrowed' WHERE id = ?", (copy_id,))
        conn.execute("""
            INSERT INTO loans (book_copy_id, member_id, issue_date, due_date, loan_status)
            VALUES (?, ?, ?, ?, 'active')
        """, (copy_id, member_id, today.isoformat(), due_date.isoformat()))

        # Check if member had a pending reservation for this book; if so, mark it fulfilled
        pending_res = conn.execute("""
            SELECT id FROM reservations
            WHERE book_id = ? AND member_id = ? AND reservation_status = 'pending'
            LIMIT 1
        """, (copy["book_id"], member_id)).fetchone()
        if pending_res:
            conn.execute("UPDATE reservations SET reservation_status = 'fulfilled' WHERE id = ?", (pending_res["id"],))

        conn.commit()
        flash(f"Book copy {copy['accession_number']} successfully issued to {member['full_name']}. Due on {due_date.strftime('%Y-%m-%d')}.", "success")
        return redirect(url_for("loans"))

    @app.route("/loans/<int:loan_id>/return", methods=["POST"])
    @login_required
    @roles_required("admin")
    def return_book(loan_id):
        conn = get_db()
        loan = conn.execute("""
            SELECT l.*, bc.id as copy_id, bc.accession_number, bc.book_id,
                   u.full_name as member_name
            FROM loans l
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN users u ON l.member_id = u.id
            WHERE l.id = ?
        """, (loan_id,)).fetchone()

        if not loan:
            flash("Loan record not found.", "warning")
            return redirect(url_for("loans"))

        # Guard: Prevent invalid duplicate returns
        if loan["return_date"] is not None or loan["loan_status"] == "returned":
            flash("Invalid action: This loan has already been marked as returned.", "warning")
            return redirect(url_for("loans"))

        today = date.today()
        due_date_obj = datetime.strptime(loan["due_date"], "%Y-%m-%d").date()
        is_overdue = today > due_date_obj

        # Update loan record
        conn.execute("""
            UPDATE loans
            SET return_date = ?, loan_status = 'returned'
            WHERE id = ?
        """, (today.isoformat(), loan_id))

        # Check if there is an overdue fine to record or finalize
        if is_overdue:
            days_late = (today - due_date_obj).days
            fine_amount = round(days_late * app.config["FINE_PER_DAY"], 2)
            existing_fine = conn.execute("SELECT id FROM fines WHERE loan_id = ?", (loan_id,)).fetchone()
            if not existing_fine:
                conn.execute("""
                    INSERT INTO fines (loan_id, amount, reason, payment_status, recorded_date)
                    VALUES (?, ?, ?, 'unpaid', ?)
                """, (loan_id, fine_amount, f"Overdue return by {days_late} day(s)", today.isoformat()))
            else:
                conn.execute("""
                    UPDATE fines SET amount = ?, reason = ? WHERE id = ?
                """, (fine_amount, f"Overdue return by {days_late} day(s)", existing_fine["id"]))

        # Check if another member has a pending reservation for this book
        pending_reservation = conn.execute("""
            SELECT id, member_id FROM reservations
            WHERE book_id = ? AND reservation_status = 'pending'
            ORDER BY reservation_date ASC LIMIT 1
        """, (loan["book_id"],)).fetchone()

        if pending_reservation:
            # Mark copy as reserved for the waiting member
            conn.execute("UPDATE book_copies SET status = 'reserved' WHERE id = ?", (loan["copy_id"],))
            flash_note = " Copy reserved for next waiting member."
        else:
            # Mark copy as available
            conn.execute("UPDATE book_copies SET status = 'available' WHERE id = ?", (loan["copy_id"],))
            flash_note = " Copy is now available in inventory."

        conn.commit()
        flash(f"Book {loan['accession_number']} successfully returned by {loan['member_name']}.{flash_note}", "success")
        return redirect(url_for("loans"))

    # -------------------------------------------------------------
    # Reservations Management
    # -------------------------------------------------------------
    @app.route("/reservations")
    @login_required
    def reservations():
        conn = get_db()
        if g.user["role"] == "admin":
            reservations_list = conn.execute("""
                SELECT r.id, r.reservation_date, r.reservation_status,
                       u.full_name as member_name, u.username, u.email,
                       b.id as book_id, b.title as book_title, b.category,
                       (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') as available_copies
                FROM reservations r
                JOIN users u ON r.member_id = u.id
                JOIN books b ON r.book_id = b.id
                ORDER BY r.id DESC
            """).fetchall()
        else:
            # Member only sees their own reservations
            reservations_list = conn.execute("""
                SELECT r.id, r.reservation_date, r.reservation_status,
                       u.full_name as member_name, u.username, u.email,
                       b.id as book_id, b.title as book_title, b.category,
                       (SELECT COUNT(*) FROM book_copies bc WHERE bc.book_id = b.id AND bc.status = 'available') as available_copies
                FROM reservations r
                JOIN users u ON r.member_id = u.id
                JOIN books b ON r.book_id = b.id
                WHERE r.member_id = ?
                ORDER BY r.id DESC
            """, (g.user["id"],)).fetchall()

        return render_template("reservations.html", reservations=reservations_list)

    @app.route("/reservations/create/<int:book_id>", methods=["POST"])
    @login_required
    def create_reservation(book_id):
        conn = get_db()
        book = conn.execute("SELECT id, title FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            flash("Book not found.", "danger")
            return redirect(url_for("books"))

        # Guard: Member cannot reserve if already holding active loan for this book
        active_loan = conn.execute("""
            SELECT l.id FROM loans l
            JOIN book_copies bc ON l.book_copy_id = bc.id
            WHERE bc.book_id = ? AND l.member_id = ? AND l.return_date IS NULL
        """, (book_id, g.user["id"])).fetchone()
        if active_loan:
            flash(f"You already have a borrowed copy of '{book['title']}'. Cannot reserve simultaneously.", "warning")
            return redirect(url_for("book_detail", book_id=book_id))

        # Guard: Prevent duplicate pending reservations by the same member for the same book
        existing_res = conn.execute("""
            SELECT id FROM reservations
            WHERE book_id = ? AND member_id = ? AND reservation_status = 'pending'
        """, (book_id, g.user["id"])).fetchone()
        if existing_res:
            flash(f"You already have a pending reservation for '{book['title']}'.", "info")
            return redirect(url_for("book_detail", book_id=book_id))

        today = date.today().isoformat()
        conn.execute("""
            INSERT INTO reservations (book_id, member_id, reservation_date, reservation_status)
            VALUES (?, ?, ?, 'pending')
        """, (book_id, g.user["id"], today))
        conn.commit()

        flash(f"Reservation for '{book['title']}' recorded. You will be notified when a copy is ready.", "success")
        return redirect(url_for("reservations"))

    @app.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
    @login_required
    def cancel_reservation(reservation_id):
        conn = get_db()
        res = conn.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
        if not res:
            flash("Reservation record not found.", "warning")
            return redirect(url_for("reservations"))

        # Guard: Member can only cancel their own reservation unless admin
        if g.user["role"] != "admin" and res["member_id"] != g.user["id"]:
            flash("Access denied: You cannot modify another member's reservation.", "danger")
            abort(403)

        conn.execute("UPDATE reservations SET reservation_status = 'cancelled' WHERE id = ?", (reservation_id,))
        conn.commit()

        flash("Reservation cancelled successfully.", "info")
        return redirect(url_for("reservations"))

    @app.route("/reservations/<int:reservation_id>/fulfill", methods=["POST"])
    @login_required
    @roles_required("admin")
    def fulfill_reservation(reservation_id):
        conn = get_db()
        res = conn.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
        if not res:
            flash("Reservation record not found.", "warning")
            return redirect(url_for("reservations"))

        conn.execute("UPDATE reservations SET reservation_status = 'fulfilled' WHERE id = ?", (reservation_id,))
        conn.commit()
        flash("Reservation marked as fulfilled.", "success")
        return redirect(url_for("reservations"))

    # -------------------------------------------------------------
    # Fines Management
    # -------------------------------------------------------------
    @app.route("/fines")
    @login_required
    def fines():
        conn = get_db()
        sync_overdue_and_fines(conn, app.config["FINE_PER_DAY"])

        if g.user["role"] == "admin":
            fines_list = conn.execute("""
                SELECT f.id, f.amount, f.reason, f.payment_status, f.recorded_date,
                       u.full_name as member_name, u.username,
                       b.title as book_title, bc.accession_number
                FROM fines f
                JOIN loans l ON f.loan_id = l.id
                JOIN users u ON l.member_id = u.id
                JOIN book_copies bc ON l.book_copy_id = bc.id
                JOIN books b ON bc.book_id = b.id
                ORDER BY f.id DESC
            """).fetchall()
        else:
            fines_list = conn.execute("""
                SELECT f.id, f.amount, f.reason, f.payment_status, f.recorded_date,
                       u.full_name as member_name, u.username,
                       b.title as book_title, bc.accession_number
                FROM fines f
                JOIN loans l ON f.loan_id = l.id
                JOIN users u ON l.member_id = u.id
                JOIN book_copies bc ON l.book_copy_id = bc.id
                JOIN books b ON bc.book_id = b.id
                WHERE l.member_id = ?
                ORDER BY f.id DESC
            """, (g.user["id"],)).fetchall()

        total_unpaid = sum(f["amount"] for f in fines_list if f["payment_status"] == "unpaid")

        return render_template("fines.html", fines=fines_list, total_unpaid=total_unpaid)

    @app.route("/fines/<int:fine_id>/pay", methods=["POST"])
    @login_required
    @roles_required("admin")
    def pay_fine(fine_id):
        conn = get_db()
        fine = conn.execute("SELECT * FROM fines WHERE id = ?", (fine_id,)).fetchone()
        if not fine:
            flash("Fine record not found.", "warning")
            return redirect(url_for("fines"))

        action = request.form.get("action", "paid")
        new_status = "waived" if action == "waive" else "paid"

        conn.execute("UPDATE fines SET payment_status = ? WHERE id = ?", (new_status, fine_id))
        conn.commit()

        flash(f"Fine #{fine_id} (${fine['amount']:.2f}) marked as {new_status}.", "success")
        return redirect(url_for("fines"))

    # -------------------------------------------------------------
    # Member History & Records
    # -------------------------------------------------------------
    @app.route("/member/loans")
    @login_required
    def member_loans():
        conn = get_db()
        sync_overdue_and_fines(conn, app.config["FINE_PER_DAY"])
        
        loans_history = conn.execute("""
            SELECT l.id, l.issue_date, l.due_date, l.return_date, l.loan_status,
                   b.title, b.author, bc.accession_number, bc.location,
                   (SELECT amount FROM fines f WHERE f.loan_id = l.id) as fine_amount,
                   (SELECT payment_status FROM fines f WHERE f.loan_id = l.id) as fine_status
            FROM loans l
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN books b ON bc.book_id = b.id
            WHERE l.member_id = ?
            ORDER BY l.id DESC
        """, (g.user["id"],)).fetchall()

        return render_template("member_loans.html", loans=loans_history)

    # -------------------------------------------------------------
    # Member Management (Admin)
    # -------------------------------------------------------------
    @app.route("/members")
    @login_required
    @roles_required("admin")
    def members():
        conn = get_db()
        members_list = conn.execute("""
            SELECT u.id, u.full_name, u.username, u.email, u.role, u.account_status, u.created_at,
                   (SELECT COUNT(*) FROM loans l WHERE l.member_id = u.id AND l.return_date IS NULL) as active_loans_count,
                   (SELECT COALESCE(SUM(amount), 0) FROM fines f JOIN loans l ON f.loan_id = l.id WHERE l.member_id = u.id AND f.payment_status = 'unpaid') as unpaid_fines
            FROM users u
            ORDER BY u.id DESC
        """).fetchall()

        return render_template("members.html", members=members_list)

    @app.route("/members/add", methods=["POST"])
    @login_required
    @roles_required("admin")
    def add_member():
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "member")

        if g.user["role"] != "admin" and role == "admin":
            flash("Only administrators can assign administrative roles.", "danger")
            return redirect(url_for("members"))

        if not (full_name and username and email and password):
            flash("All member registration fields are required.", "danger")
            return redirect(url_for("members"))

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            flash("A user with this username or email already exists.", "danger")
            return redirect(url_for("members"))

        conn.execute("""
            INSERT INTO users (full_name, username, email, password_hash, role, account_status)
            VALUES (?, ?, ?, ?, ?, 'active')
        """, (full_name, username, email, generate_password_hash(password), role))
        conn.commit()

        flash(f"User account '{username}' successfully registered as {role}.", "success")
        return redirect(url_for("members"))

    @app.route("/members/<int:user_id>/status", methods=["POST"])
    @login_required
    @roles_required("admin")
    def toggle_member_status(user_id):
        conn = get_db()
        target_user = conn.execute("SELECT id, username, account_status FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target_user:
            flash("User not found.", "warning")
            return redirect(url_for("members"))

        if target_user["id"] == g.user["id"]:
            flash("You cannot deactivate your own administrative account.", "danger")
            return redirect(url_for("members"))

        new_status = "suspended" if target_user["account_status"] == "active" else "active"
        conn.execute("UPDATE users SET account_status = ? WHERE id = ?", (new_status, user_id))
        conn.commit()

        flash(f"Account for '{target_user['username']}' updated to '{new_status}'.", "info")
        return redirect(url_for("members"))

    # -------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------
    @app.route("/reports")
    @login_required
    @roles_required("admin")
    def reports():
        conn = get_db()
        sync_overdue_and_fines(conn, app.config["FINE_PER_DAY"])

        # Category breakdown
        category_stats = conn.execute("""
            SELECT b.category, COUNT(DISTINCT b.id) as title_count, COUNT(bc.id) as copy_count
            FROM books b
            LEFT JOIN book_copies bc ON b.id = bc.book_id
            GROUP BY b.category
            ORDER BY copy_count DESC
        """).fetchall()

        # Overdue loans report
        overdue_report = conn.execute("""
            SELECT l.id, l.issue_date, l.due_date,
                   u.full_name as member_name, u.email,
                   b.title as book_title, bc.accession_number,
                   f.amount as fine_amount, f.payment_status
            FROM loans l
            JOIN users u ON l.member_id = u.id
            JOIN book_copies bc ON l.book_copy_id = bc.id
            JOIN books b ON bc.book_id = b.id
            LEFT JOIN fines f ON f.loan_id = l.id
            WHERE l.loan_status = 'overdue'
            ORDER BY l.due_date ASC
        """).fetchall()

        # Summary KPIs
        total_books = conn.execute("SELECT COUNT(*) as c FROM books").fetchone()["c"]
        total_copies = conn.execute("SELECT COUNT(*) as c FROM book_copies").fetchone()["c"]
        total_loans_all_time = conn.execute("SELECT COUNT(*) as c FROM loans").fetchone()["c"]
        total_fines_collected = conn.execute("SELECT COALESCE(SUM(amount), 0) as s FROM fines WHERE payment_status = 'paid'").fetchone()["s"]

        return render_template(
            "reports.html",
            category_stats=category_stats,
            overdue_report=overdue_report,
            total_books=total_books,
            total_copies=total_copies,
            total_loans_all_time=total_loans_all_time,
            total_fines_collected=total_fines_collected
        )

    # -------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", error_code=400, title="Bad Request", message=str(e.description if hasattr(e, 'description') else "Bad request.")), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", error_code=403, title="Forbidden", message="You do not have permission to view or modify this resource."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", error_code=404, title="Page Not Found", message="The requested page or resource could not be found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", error_code=500, title="Internal Server Error", message="An unexpected server error occurred. Please try again later."), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
