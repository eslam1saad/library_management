// Show loading spinner
function showLoader() {
    document.getElementById("loader").style.display = "block";
}

// Hide loading spinner
function hideLoader() {
    document.getElementById("loader").style.display = "none";
}

// Fetch and Display Members
function loadMembers() {
    showLoader();
    fetch('/api/method/library_management.api.get_members')
        .then(response => response.json())
        .then(data => {
            hideLoader();
            let members = data.message;
            let tableBody = document.querySelector("#memberTable tbody");
            tableBody.innerHTML = "";

            members.forEach(member => {
                let row = `<tr>
                    <td>${member.full_name}</td>
                    <td>${member.email}</td>
                </tr>`;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => {
            hideLoader();
            console.error("Error loading members:", error);
            alert("Failed to load members. Please try again.");
        });
}

// Add New Member
document.getElementById("addMemberForm")?.addEventListener("submit", function(event) {
    event.preventDefault();
    showLoader();

    let fullName = document.getElementById("full_name").value;
    let email = document.getElementById("email").value;

    fetch(`/api/method/library_management.api.add_member?full_name=${fullName}&email=${email}`, {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();
        alert(data.message);
        loadMembers(); // Refresh the member list
    })
    .catch(error => {
        hideLoader();
        console.error("Error adding member:", error);
        alert("Failed to add member.");
    });
});

// Load books
function loadBooks() {
    showLoader();
    fetch('/api/method/library_management.api.get_books')
        .then(response => response.json())
        .then(data => {
            hideLoader();
            let books = data.message;
            let tableBody = document.querySelector("#bookTable tbody");
            tableBody.innerHTML = "";

            books.forEach(book => {
                let row = `<tr>
                    <td>${book.title}</td>
                    <td>${book.author}</td>
                    <td>${book.isbn}</td>
                    <td>${book.stock}</td>
                </tr>`;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => {
            hideLoader();
            console.error("Error loading books:", error);
            alert("Failed to load books. Please try again.");
        });
});

// Load Books on page load
document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("bookTable")) {
        loadBooks();
    }
    if (document.getElementById("memberTable")) {
        loadMembers();
    }
});
