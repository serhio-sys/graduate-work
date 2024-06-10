const message = document.querySelector(".message");

if (message !== null) {
    message.addEventListener("click", () => {
        message.classList.add("hidden");
    });
} 