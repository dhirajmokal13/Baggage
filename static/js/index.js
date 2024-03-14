const modalImage = document.getElementById("modalImage");
document.querySelectorAll(".img-gallary").forEach(img => {
    img.addEventListener("click", event => {
        modalImage.src = img.getAttribute("src");
    });
});

document.getElementById("logo").addEventListener("click", () => {
    location.href = "/"
});