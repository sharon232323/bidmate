/* =========================
   BIDMATE UI INTERACTIONS
========================= */

// Dark Mode Toggle
document.addEventListener("DOMContentLoaded", function() {

    const toggle = document.getElementById("darkToggle");

    if (localStorage.getItem("darkMode") === "enabled") {
        document.body.classList.add("dark-mode");
    }

    if (toggle) {
        toggle.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");

            if (document.body.classList.contains("dark-mode")) {
                localStorage.setItem("darkMode", "enabled");
            } else {
                localStorage.setItem("darkMode", "disabled");
            }
        });
    }

    // Real-time Search Filter
    const searchInput = document.getElementById("searchInput");

    if (searchInput) {
        searchInput.addEventListener("keyup", function() {
            let filter = searchInput.value.toLowerCase();
            let cards = document.querySelectorAll(".item-card");

            cards.forEach(card => {
                let text = card.innerText.toLowerCase();
                card.style.display = text.includes(filter) ? "" : "none";
            });
        });
    }

});

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}
showToast("Item Added Successfully!");