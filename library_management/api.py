import frappe
from datetime import datetime, timedelta
from frappe.utils import fmt_money
from frappe.utils import today
from frappe import cache
import pandas as pd
from frappe.utils import nowdate
from io import BytesIO
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, today


## ---------------------- Get CSRF Token ----------------------
@frappe.whitelist(allow_guest=True)
def get_csrf_token():
    return {"csrf_token": frappe.sessions.get_csrf_token()}
# ---------------------- Issue Book ----------------------
@frappe.whitelist(allow_guest=True)
def issue_book():
    try:
        # ✅ Log Incoming Request
        frappe.logger().info("📥 Received API Call to issue_book")

        # ✅ Parse JSON Data
        data = frappe.request.get_json()
        if not data:
            frappe.logger().error("❌ No JSON data received")
            return {"success": False, "message": "❌ No data received"}

        member_email = data.get("member_email")
        book_isbn = data.get("book_isbn")

        frappe.logger().info(f"📌 member_email={member_email}, book_isbn={book_isbn}")

        # ✅ Validate Inputs
        if not member_email or not book_isbn:
            frappe.logger().error("❌ Missing member_email or book_isbn")
            return {"success": False, "message": "❌ Missing member_email or book_isbn"}

        # ✅ Fetch Member UUID
        member_name = frappe.get_value("Member", {"email": member_email}, "name")
        if not member_name:
            frappe.logger().error(f"❌ Member {member_email} not found.")
            return {"success": False, "message": "❌ Member not found."}

        # ✅ Fetch Book UUID
        book_name = frappe.get_value("Book", {"isbn": book_isbn}, "name")
        if not book_name:
            frappe.logger().error(f"❌ Book {book_isbn} not found.")
            return {"success": False, "message": "❌ Book not found."}

        # ✅ Fetch Book Document
        book = frappe.get_doc("Book", book_name)
        if book.stock <= 0:
            frappe.logger().warning(f"⚠️ Book {book_isbn} is out of stock!")
            return {"success": False, "message": "❌ Book is out of stock."}

        # ✅ Create Transaction
        transaction = frappe.get_doc({
            "doctype": "Transaction",
            "member": member_name,  # ✅ Store Member UUID
            "book": book_name,      # ✅ Store Book UUID
            "date_issued": frappe.utils.today(),
            "owner": "Administrator",
        })
        transaction.insert(ignore_permissions=True)

        # ✅ Ensure Transaction is Inserted
        created_transaction = frappe.get_value("Transaction", {
            "member": member_name, "book": book_name
        }, "name")

        if not created_transaction:
            frappe.logger().error(f"❌ Transaction for {member_email} & {book_isbn} not inserted!")
            return {"success": False, "message": "❌ Transaction not recorded!"}

        # ✅ Reduce Book Stock
        book.stock -= 1
        book.save(ignore_permissions=True)

        # ✅ Commit Changes
        frappe.db.commit()

        frappe.logger().info(f"✅ Book {book_isbn} issued to {member_email}. Transaction ID: {created_transaction}")
        return {"success": True, "message": "✅ Book Issued Successfully"}

    except Exception as e:
        frappe.db.rollback()  # Rollback any failed transaction
        frappe.logger().error(f"❌ Issue Book Failed: {str(e)}")
        return {"success": False, "message": "❌ Issue Book Failed", "error": str(e)}


@frappe.whitelist(allow_guest=True)
def return_book(member_email, book_isbn):
    try:
        frappe.session.user = "Administrator"  # ✅ Ensure Admin permissions
        frappe.logger().info(f"🟢 Attempting to return book {book_isbn} from {member_email}")

        # ✅ Retrieve Member UUID
        member_name = frappe.get_value("Member", {"email": member_email}, "name")
        if not member_name:
            frappe.logger().error(f"❌ Member {member_email} not found.")
            return {"success": False, "message": "❌ Member not found."}

        # ✅ Retrieve Book UUID
        book_name = frappe.get_value("Book", {"isbn": book_isbn}, "name")
        if not book_name:
            frappe.logger().error(f"❌ Book {book_isbn} not found.")
            return {"success": False, "message": "❌ Book not found."}

        # ✅ Find Latest Unreturned Transaction
        transaction_name = frappe.db.sql("""
            SELECT name FROM `tabTransaction`
            WHERE member = %s AND book = %s AND date_returned IS NULL
            ORDER BY creation DESC LIMIT 1
        """, (member_name, book_name), as_dict=True)

        if not transaction_name:
            frappe.logger().warning(f"⚠️ No active transaction found for {member_email} and book {book_isbn}.")
            return {"success": False, "message": "❌ No active transaction found for this book and member."}

        transaction_name = transaction_name[0]["name"]

        # ✅ Fetch Transaction & Update `date_returned`
        transaction = frappe.get_doc("Transaction", transaction_name)
        transaction.date_returned = frappe.utils.today()
        transaction.modified_by = "Administrator"
        transaction.save(ignore_permissions=True)

        # ✅ Update Book Stock
        book = frappe.get_doc("Book", book_name)
        book.stock += 1
        book.modified_by = "Administrator"
        book.save(ignore_permissions=True)

        # ✅ Commit Changes
        frappe.db.commit()

        # ✅ Confirm Transaction is Updated
        returned_transaction = frappe.get_value("Transaction", {"name": transaction_name}, "date_returned")
        if not returned_transaction:
            frappe.logger().error(f"❌ Return failed: Transaction {transaction_name} not updated.")
            return {"success": False, "message": "❌ Return failed! Transaction record not updated."}

        frappe.logger().info(f"✅ Book {book_isbn} successfully returned by {member_email}. Transaction: {transaction_name}")
        return {"success": True, "message": "✅ Book Returned Successfully"}

    except Exception as e:
        frappe.db.rollback()  # 🚨 Rollback if failure
        frappe.logger().error(f"❌ Error Returning Book: {str(e)}")
        return {"success": False, "message": "❌ Return Book Failed", "error": str(e)}

# ---------------------- import Book ----------------------
@frappe.whitelist()
def import_books(title=None, count=10, page=1):
    """
    Fetches books from Frappe Library API and adds them to the system.
    
    Parameters:
        - title (str): Filter books by title
        - count (int): Number of books to import (default: 10)
        - page (int): Page number for API pagination
    """
    try:
        # Ensure count is an integer
        count = int(count)
    except ValueError:
        return {"success": False, "message": "Invalid count parameter, must be an integer"}

    # API URL
    base_url = "https://frappe.io/api/method/frappe-library"
    params = {
        "title": title or "",  # Empty title for broader search if no title provided
        "page": page
    }

    try:
        # Make the request to the Frappe Library API
        response = requests.get(base_url, params=params)
        data = response.json()

        if "message" not in data:
            return {"success": False, "message": "Invalid API response"}

        imported_books = []

        # Loop through the books returned by the API
        for book in data["message"][:count]:
            title = book.get("title", "Unknown Title")
            author = book.get("authors", "Unknown Author")
            isbn = book.get("isbn13", book.get("isbn", None))  # Prefer ISBN13
            publisher = book.get("publisher", "Unknown Publisher")
            num_pages = book.get("num_pages", 0)

            # Skip books with missing ISBN
            if not isbn:
                continue

            # Insert the book into the Frappe system
            new_book = frappe.get_doc({
                "doctype": "Book",
                "title": title,
                "author": author,
                "isbn": isbn,
                "publisher": publisher,
                "stock": 5,  # Default stock
                "num_pages": num_pages
            })
            new_book.insert(ignore_permissions=True)
            imported_books.append(title)

        # Commit changes to the database
        frappe.db.commit()

        # Return success response
        return {"success": True, "message": f"Imported {len(imported_books)} books.", "books": imported_books}

    except Exception as e:
        return {"success": False, "message": f"Error importing books: {str(e)}"}
    
# ---------------------- Add Book ----------------------
@frappe.whitelist(allow_guest=True)
def add_book(title, author, isbn, stock):
    """Add a new book to the system with debugging"""
    try:
        frappe.logger().info(f"📥 Add Book Request: title={title}, author={author}, isbn={isbn}, stock={stock}")

        if not title or not author or not isbn or not stock:
            frappe.logger().error("❌ Missing fields in add_book request")
            return {"error": "Missing required fields!"}

        new_book = frappe.get_doc({
            "doctype": "Book",
            "title": title,
            "author": author,
            "isbn": isbn,
            "stock": int(stock)
        })
        new_book.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger().info(f"✅ Book added successfully: {title}")
        return {"message": "Book added successfully!"}
    
    except Exception as e:
        frappe.logger().error(f"❌ Error adding book: {str(e)}")
        return {"error": str(e)}

# ---------------------- Delete Book ----------------------
@frappe.whitelist()
def delete_book(isbn=None):
    """Delete a book entry by ISBN and ensure commit"""
    try:
        if not isbn:
            return {"error": "❌ ISBN is required for deletion!"}

        book = frappe.get_doc("Book", {"isbn": isbn})
        if book:
            book.delete()
            frappe.db.commit()  # ✅ Ensure DB changes are saved
            return {"message": f"✅ Book '{isbn}' deleted successfully!"}
        else:
            return {"error": "❌ Book not found!"}
    except Exception as e:
        frappe.log_error(f"❌ Error deleting book: {str(e)}")
        frappe.throw(_("Error deleting book"), exc=e)

# ---------------------- Get All Books ----------------------
@frappe.whitelist(allow_guest=True)
def get_books():
    """Fetch books with no caching."""
    
    # 🔥 Delete cache before fetching
    frappe.cache().delete_value("library_books")

    books = frappe.get_all("Book", fields=["title", "author", "isbn", "stock"])
    
    # 🔥 Do NOT cache this response
    return books


# ---------------------- Search Books ----------------------
@frappe.whitelist(allow_guest=True)
def search_books(title=None, author=None, in_stock=None):
    """Search books by title, author, and availability with fuzzy matching."""

    filters = {}

    if title:
        filters["title"] = ["like", f"%{title}%"]
    if author:
        filters["author"] = ["like", f"%{author}%"]
    if in_stock:
        filters["stock"] = [">", 0]  # Only show books that are in stock

    books = frappe.get_all("Book", filters=filters, fields=["title", "author", "isbn", "stock"])

    # Aggregate books with the same title and ISBN
    aggregated_books = {}
    for book in books:
        key = (book["title"], book["isbn"])  # Unique identifier
        if key in aggregated_books:
            aggregated_books[key]["stock"] += book["stock"]
        else:
            aggregated_books[key] = book

    return list(aggregated_books.values())

# ---------------------- Add Member ----------------------
@frappe.whitelist()
def add_member(full_name, email, phone=None):  # Ensure phone is optional
    if frappe.db.exists("Member", email):
        frappe.throw(f"❌ Member with email {email} already exists.", frappe.DuplicateEntryError)

    member = frappe.get_doc({
        "doctype": "Member",
        "full_name": full_name,
        "email": email,
        "phone": phone  # Ensure this field is saved
    })
    member.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"message": "✅ Member added successfully!"}

# ---------------------- Delete Member ----------------------
@frappe.whitelist()
def delete_member(email):
    """Delete a member by email"""
    try:
        member = frappe.get_doc("Member", {"email": email})
        if not member:
            return {"error": "❌ Member not found!"}

        member.delete()
        frappe.db.commit()
        return {"message": f"✅ Member '{email}' deleted successfully!"}

    except Exception as e:
        frappe.log_error(f"❌ Error deleting member: {str(e)}")
        frappe.throw("Error deleting member", exc=e)

# ---------------------- Get All Members ----------------------
@frappe.whitelist(allow_guest=True)
def get_members():
    return frappe.get_all("Member", fields=["name", "email", "full_name","phone"])

# ---------------------- Generate Library Report ----------------------
@frappe.whitelist()
def generate_report():
    """Generate a summary report for the librarian"""

    total_books = frappe.db.count("Book")
    total_issued_books = frappe.db.count("Transaction", {"transaction_type": "Issue"})
    outstanding_members = frappe.get_all("Member", filters={"outstanding_fees": [">", 0]}, fields=["full_name", "outstanding_fees"])

    return {
        "total_books": total_books,
        "total_issued_books": total_issued_books,
        "outstanding_members": outstanding_members
    }
# -------------------------- Pay Fees --------------------------
@frappe.whitelist()
def pay_fees(member_name, amount_paid):
    """Processes a fee payment for a member, but does NOT allow payments if balance is zero."""

    # Fetch member details
    member_id = frappe.get_value("Member", {"full_name": member_name}, "name")
    if not member_id:
        return {"success": False, "message": "Member not found!", "error_code": "MEMBER_NOT_FOUND"}

    # Convert outstanding fees to float
    outstanding_fees = frappe.db.get_value("Member", member_id, "outstanding_fees") or 0
    outstanding_fees = float(outstanding_fees)  # Ensure it's float
    amount_paid = float(amount_paid)  # Ensure amount_paid is also float

    # 🚨 **Block Payment if Outstanding Balance is Zero**
    if outstanding_fees == 0:
        return {
            "success": False,
            "message": "Payment is not allowed when outstanding balance is zero.",
            "error_code": "NO_BALANCE_DUE"
        }

    # 🚨 **Block Overpayment**
    if amount_paid > outstanding_fees:
        return {
            "success": False,
            "message": f"Payment exceeds outstanding balance ({outstanding_fees:.2f} EGP).",
            "error_code": "PAYMENT_EXCEEDS_BALANCE"
        }

    # Calculate remaining balance
    remaining_balance = outstanding_fees - amount_paid

    # Update outstanding fees
    frappe.db.set_value("Member", member_id, "outstanding_fees", remaining_balance)

    # Log payment
    new_payment = frappe.get_doc({
        "doctype": "Payment",
        "member": member_id,
        "amount_paid": amount_paid,
        "date_paid": frappe.utils.today()
    })
    new_payment.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": f"Payment successful! Remaining balance: {remaining_balance:.2f} EGP"
    }

#  -------------------------- API Response --------------------------
def api_response(success=True, message="", data=None, error_code=None):
    """Standardized API response format"""
    return {
        "success": success,
        "message": message,
        "data": data if data else {},
        "error_code": error_code
    }

#  -------------------------- Get Transactions --------------------------
@frappe.whitelist(allow_guest=True)
def get_transactions():
    try:
        transactions = frappe.get_all(
            "Transaction",
            fields=["member", "book", "date_issued", "date_returned", "creation as date"]
        )

        today = datetime.today().date()

        # Fetch Member & Book Details + Fine Calculation
        for transaction in transactions:
            transaction["member_email"] = frappe.get_value("Member", transaction["member"], "email") or "Unknown"
            transaction["book_isbn"] = frappe.get_value("Book", transaction["book"], "isbn") or "Unknown"

            # Convert dates to datetime objects
            date_issued = transaction["date_issued"]
            date_returned = transaction["date_returned"]

            if date_issued:
                date_issued = datetime.strptime(str(date_issued), "%Y-%m-%d").date()
            
            if date_returned:
                date_returned = datetime.strptime(str(date_returned), "%Y-%m-%d").date()

            # ✅ **Fix Transaction Type**
            transaction["status"] = "Returned" if transaction["date_returned"] else "Issued"

            # ✅ **Calculate fine if book is overdue**
            fine = 0
            if transaction["status"] == "Issued" and date_issued:
                overdue_days = (today - date_issued).days
                if overdue_days > 0:
                    fine = min(overdue_days * 10, 500)  # Max fine Rs.500

            transaction["fine"] = fine  # Assign fine

        # 🚨 Remove transactions with missing data
        transactions = [t for t in transactions if t["member_email"] != "Unknown" and t["book_isbn"] != "Unknown"]

        # ✅ Return formatted transactions
        frappe.response["transactions"] = transactions
        return

    except Exception as e:
        frappe.logger().error(f"❌ Error fetching transactions: {str(e)}")
        frappe.response["error"] = str(e)
        return

