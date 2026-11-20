"use strict";

(() => {
  const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = null;
  try {
    const saved = localStorage.getItem("knowledge-ai-theme");
    if (["light", "dark"].includes(saved)) preference = saved;
  } catch {}

  function applyTheme() {
    const dark = preference ? preference === "dark" : systemTheme.matches;
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    document.querySelector('meta[name="theme-color"]').content = dark ? "#0d1117" : "#f6f8fa";
    const toggle = document.querySelector("#theme-toggle");
    if (toggle) {
      toggle.hidden = false;
      toggle.setAttribute("aria-label", dark ? "Ativar modo claro" : "Ativar modo escuro");
      toggle.title = toggle.getAttribute("aria-label");
      document.querySelector("#theme-label").textContent = dark ? "Claro" : "Escuro";
    }
  }

  applyTheme();
  systemTheme.addEventListener("change", applyTheme);
  document.addEventListener("DOMContentLoaded", () => {
    applyTheme();
    document.querySelector("#theme-toggle").addEventListener("click", () => {
      preference = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      try { localStorage.setItem("knowledge-ai-theme", preference); } catch {}
      applyTheme();
    });
  });
})();
