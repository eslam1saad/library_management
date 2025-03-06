document.addEventListener("DOMContentLoaded", function () {
    fetchBooks();
    fetchMembers();
    fetchTransactions();
});

let booksData = [];
let membersData = [];

// Fetch Books
function fetchBooks() {
    fetch('/api/method/library_management.api.get_books')
        .then(response => response.json())
        .then(data => {
            booksData = data.message;
            displayBooks();
        })
        .catch(error => console.error("Error loading books:", error));
}

// Display Books
function displayBooks() {
    let tableBody = document.querySelector("#bookTable tbody");
    tableBody.innerHTML = "";

    booksData.forEach(book => {
        let row = `<tr>
            <td>${book.title}</td>
            <td>${book.author}</td>
            <td>${book.isbn}</td>
            <td>${book.stock}</td>
            <td><button class="delete-btn" onclick="deleteBook('${book.isbn}')">🗑️ Remove</button></td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}

// Fetch Members
function fetchMembers() {
    fetch('/api/method/library_management.api.get_members')
        .then(response => response.json())
        .then(data => {
            membersData = data.message;
            displayMembers();
        })
        .catch(error => console.error("Error loading members:", error));
}

// Display Members
function displayMembers() {
    let tableBody = document.querySelector("#memberTable tbody");
    tableBody.innerHTML = "";

    membersData.forEach(member => {
        let row = `<tr>
            <td>${member.full_name}</td>
            <td>${member.email}</td>
            <td>${member.phone}</td>
            <td><button class="delete-btn" onclick="deleteMember('${member.email}')">🗑️ Remove</button></td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}

// Fetch Transactions
function fetchTransactions() {
    fetch('/api/method/library_management.api.get_transactions')
        .then(response => response.json())
        .then(data => {
            let tableBody = document.querySelector("#transactionTable tbody");
            tableBody.innerHTML = "";

            data.message.forEach(transaction => {
                let row = `<tr>
                    <td>${transaction.member_email}</td>
                    <td>${transaction.book_isbn}</td>
                    <td>${transaction.status}</td>
                    <td>${transaction.date}</td>
                </tr>`;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => console.error("Error loading transactions:", error));
}
