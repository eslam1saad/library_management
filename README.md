📚 Library Management System
A web application using frappe for managing a library, tracking books, issuing and returning books, managing members, and enforcing fine policies.

🚀 Features
✔️ Manage Books – Add, search, update, delete books with stock tracking.
✔️ Manage Members – Register, search, and delete members.
✔️ Issue & Return Books – Track transactions and enforce fine policies.
✔️ Fine Calculation – Ensures a member's outstanding debt does not exceed Rs.500.
✔️ Search Functionality – Search books, members, and transactions.
✔️ Data Import – Fetch books from the Frappe Library API.

📂 Project Structure
/library_management
│── hooks.py
│── api.py      # Backend API (Frappe)
│── www/
│   ├── index.html                 # Homepage
│   ├── books.html                 # Books Management
│   ├── members.html               # Members Management
│   ├── transactions.html          # Transactions (Issue/Return)
│── screenshots/                   # Screenshots of UI
│── README.md                      # Project Documentation
🛠️ Installation & Setup

1️⃣ Install Frappe Framework
pip install frappe-bench

2️⃣ Clone the Repository
git clone https://github.com/eslam1saad/library_management.git
cd library_management

3️⃣ Start the Frappe Server
bench start

4️⃣ Access the App
Open http://localhost:8000 in a browser.

🏠 Home Page

📖 Manage Books
http://127.0.0.1:8000/books.html

👥 Manage Members
http://127.0.0.1:8000/members.html

🔄 Transactions (Issue & Return)
http://127.0.0.1:8000/transactions.html

📬 Contact

For any issues, feel free to reach out at eslam.attia2000@gmail.com OR 01206310840.