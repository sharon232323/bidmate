function toggleMode() {
    document.body.classList.toggle("dark");
    document.body.classList.toggle("light");
}

// Real-time search filter
function searchItems() {
    let input = document.getElementById("searchBar").value.toLowerCase();
    let cards = document.getElementsByClassName("item-card");

    for (let card of cards) {
        let title = card.getAttribute("data-title");
        card.style.display = title.includes(input) ? "block" : "none";
    }
}