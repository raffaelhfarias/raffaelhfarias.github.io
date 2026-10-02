const root = document.documentElement;
const themeToggle = document.querySelector(".theme-toggle");

function applyTheme(theme) {
  const isDark = theme === "dark";
  root.dataset.theme = isDark ? "dark" : "light";
  themeToggle.setAttribute("aria-pressed", String(isDark));
  themeToggle.setAttribute(
    "aria-label",
    isDark ? "Ativar tema claro" : "Ativar tema escuro",
  );
  document.querySelector('meta[name="theme-color"]').content = isDark
    ? "#0d1117"
    : "#f6f8fa";
}

applyTheme(root.dataset.theme || "light");

themeToggle.addEventListener("click", () => {
  const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("portfolio-theme", nextTheme);
  applyTheme(nextTheme);
});
