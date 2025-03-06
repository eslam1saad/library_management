import frappe

def get_context(context):
    context.books = frappe.get_all("Book", fields=["title", "author", "isbn", "stock"])
