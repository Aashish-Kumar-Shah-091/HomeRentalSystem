document.addEventListener("DOMContentLoaded", () => {
    const storageKey = "gharsetu-theme";
    const root = document.documentElement;
    const toggleButton = document.getElementById("theme-toggle");
    const toggleIcon = document.getElementById("theme-toggle-icon");
    const toggleLabel = document.getElementById("theme-toggle-label");

    if (!toggleButton || !toggleIcon || !toggleLabel) {
        return;
    }

    function currentTheme() {
        const theme = root.getAttribute("data-bs-theme");
        return theme === "dark" ? "dark" : "light";
    }

    function applyTheme(theme) {
        const nextTheme = theme === "dark" ? "dark" : "light";
        const isDark = nextTheme === "dark";

        root.setAttribute("data-bs-theme", nextTheme);
        toggleButton.setAttribute("aria-pressed", String(isDark));
        toggleButton.setAttribute(
            "aria-label",
            isDark ? "Switch to light mode" : "Switch to dark mode"
        );
        toggleIcon.className = isDark ? "fas fa-sun" : "fas fa-moon";
        toggleLabel.textContent = isDark ? "Light" : "Dark";
    }

    applyTheme(currentTheme());

    toggleButton.addEventListener("click", () => {
        const nextTheme = currentTheme() === "dark" ? "light" : "dark";
        applyTheme(nextTheme);

        try {
            localStorage.setItem(storageKey, nextTheme);
        } catch (error) {
            return;
        }
    });
});
