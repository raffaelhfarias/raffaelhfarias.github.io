const iconMarkup = {
  language: '<path d="m8 9-3 3 3 3M16 9l3 3-3 3M14 5l-4 14" />',
  data: '<ellipse cx="12" cy="6" rx="7" ry="3" /><path d="M5 6v6c0 1.66 3.13 3 7 3s7-1.34 7-3V6M5 12v6c0 1.66 3.13 3 7 3s7-1.34 7-3v-6" />',
  automation: '<rect x="3" y="4" width="6" height="6" rx="1" /><rect x="15" y="14" width="6" height="6" rx="1" /><path d="M9 7h3a3 3 0 0 1 3 3v4M15 17h-3a3 3 0 0 1-3-3v-4" />',
  ai: '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.64 5.64l2.12 2.12M16.24 16.24l2.12 2.12M18.36 5.64l-2.12 2.12M7.76 16.24l-2.12 2.12" /><circle cx="12" cy="12" r="4" />',
  tools: '<path d="M14 6a4 4 0 0 0-5 5L4 16a2 2 0 1 0 3 3l5-5a4 4 0 0 0 5-5l-3 3-3-3 3-3Z" /><path d="m15 15 5 5" />',
};

const iconByTechnology = {
  Python: "assets/tech-stack/python.svg",
  SQL: "assets/tech-stack/sql.svg",
  DAX: "assets/tech-stack/microsoft.svg",
  VBA: "assets/tech-stack/vba.svg",
  APIs: "assets/tech-stack/api.svg",
  Kestra: "assets/tech-stack/kestra.svg",
  Docker: "assets/tech-stack/docker.svg",
  "Automação de processos": "assets/tech-stack/n8n.svg",
  EvolutionAPI: "assets/tech-stack/evolution-api.png",
  "Power BI": "assets/tech-stack/microsoft-power-bi.svg",
  LLMs: "assets/tech-stack/LLM.svg",
  "Agentes de IA": "assets/tech-stack/agente-ia.svg",
  RAG: "assets/tech-stack/RAG.svg",
  Git: "assets/tech-stack/git.svg",
  GitHub: "assets/tech-stack/github-badge.svg",
  Playwright: "assets/tech-stack/playwright.svg",
  Excel: "assets/tech-stack/microsoft-excel.svg",
  MCP: "assets/tech-stack/mcp-model-context-protocol.svg",
};

function initTechStack() {
  const filterButtons = document.querySelectorAll(".tech-filter-button");
  const techPills = document.querySelectorAll(".tech-pill");

  techPills.forEach((pill) => {
    const technology = pill.textContent.trim();
    const iconPath = iconByTechnology[technology];

    if (iconPath) {
      const icon = document.createElement("img");
      icon.classList.add("tech-icon");
      if (technology === "RAG") {
        icon.classList.add("tech-icon-rag");
      }
      icon.src = iconPath;
      icon.alt = "";
      icon.setAttribute("aria-hidden", "true");
      pill.prepend(icon);
      return;
    }

    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.classList.add("tech-icon");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML = iconMarkup[pill.dataset.category] || "";
    pill.prepend(icon);
  });

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter;

      filterButtons.forEach((item) => {
        const isActive = item === button;
        item.classList.toggle("is-active", isActive);
        item.setAttribute("aria-pressed", String(isActive));
      });

      techPills.forEach((pill) => {
        pill.hidden = filter !== "all" && pill.dataset.category !== filter;
      });
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTechStack);
} else {
  initTechStack();
}
