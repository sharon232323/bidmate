function confirmDelete() {
    return confirm("Are you sure you want to delete this item?");
}
const searchInput = document.getElementById("searchInput");

if (searchInput) {
    searchInput.addEventListener("keyup", function () {
        let filter = searchInput.value.toLowerCase();
        let cards = document.querySelectorAll(".card");

        cards.forEach(card => {
            let text = card.innerText.toLowerCase();
            card.style.display = text.includes(filter) ? "block" : "none";
        });
    });
}
function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
}