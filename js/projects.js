const projects = [
  {
    name: "EBAC_Profissao_Cientista_de_Dados",
    description: "Repositório de projetos e atividades da EBAC.",
    language: "Jupyter Notebook",
    stars: 0,
    forks: 0,
    updatedAt: "2022-10-09T14:19:07Z",
    url: "https://github.com/raffaelhfarias/EBAC_Profissao_Cientista_de_Dados",
  },
  {
    name: "term-deposit",
    description: "Mod28.",
    language: "Python",
    stars: 0,
    forks: 0,
    updatedAt: "2022-10-13T14:29:26Z",
    url: "https://github.com/raffaelhfarias/term-deposit",
  },
  {
    name: "RFV",
    description: "Sem descrição informada no GitHub.",
    language: "Jupyter Notebook",
    stars: 0,
    forks: 0,
    updatedAt: "2022-10-14T14:24:43Z",
    url: "https://github.com/raffaelhfarias/RFV",
  },
  {
    name: "Dados_Airbnb",
    description: "Analisando dados do Airbnb.",
    language: "Jupyter Notebook",
    stars: 0,
    forks: 0,
    updatedAt: "2024-11-12T18:12:45Z",
    url: "https://github.com/raffaelhfarias/Dados_Airbnb",
  },
  {
    name: "Panorama_COVID-19",
    description: "Panorama do COVID-19 no Brasil.",
    language: "CSS",
    stars: 0,
    forks: 0,
    updatedAt: "2025-04-16T18:47:40Z",
    url: "https://github.com/raffaelhfarias/Panorama_COVID-19",
  },
  {
    name: "visaoComputacional",
    description: "Sem descrição informada no GitHub.",
    language: "Python",
    stars: 0,
    forks: 0,
    updatedAt: "2023-05-23T23:14:20Z",
    url: "https://github.com/raffaelhfarias/visaoComputacional",
  },
  {
    name: "churnPrediction",
    description: "Sem descrição informada no GitHub.",
    language: "Jupyter Notebook",
    stars: 0,
    forks: 0,
    updatedAt: "2024-11-12T18:14:18Z",
    url: "https://github.com/raffaelhfarias/churnPrediction",
  },
  {
    name: "recomenda-o",
    description: "Sem descrição informada no GitHub.",
    language: "Python",
    stars: 0,
    forks: 0,
    updatedAt: "2025-04-16T21:34:43Z",
    url: "https://github.com/raffaelhfarias/recomenda-o",
  },
  {
    name: "gasolina-preco",
    description: "Sem descrição informada no GitHub.",
    language: "Python",
    stars: 1,
    forks: 0,
    updatedAt: "2025-04-16T02:47:30Z",
    url: "https://github.com/raffaelhfarias/gasolina-preco",
  },
  {
    name: "PowerBI_Projetos",
    description: "Sem descrição informada no GitHub.",
    language: "Não informado",
    stars: 0,
    forks: 0,
    updatedAt: "2025-04-22T21:57:31Z",
    url: "https://github.com/raffaelhfarias/PowerBI_Projetos",
  },
];

const projectList = document.querySelector("#project-list");
const projectStatus = document.querySelector("#project-status");
const searchInput = document.querySelector("#project-search");
const languageSelect = document.querySelector("#project-language");
const sortSelect = document.querySelector("#project-sort");

const formatDate = (date) =>
  new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(date));

const createProjectCard = (project) => {
  const article = document.createElement("article");
  article.className = "featured-project-card";
  article.innerHTML = `
    <div class="featured-project-title">
      <h3><a href="${project.url}" target="_blank" rel="noreferrer">${project.name}</a></h3>
      <a class="project-external" href="${project.url}" target="_blank" rel="noreferrer" aria-label="Abrir ${project.name} no GitHub">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M14 4h6v6M20 4l-9 9" />
          <path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5" />
        </svg>
      </a>
    </div>
    <p>${project.description}</p>
    <div class="project-meta">
      <span>${project.language}</span>
      <time datetime="${project.updatedAt}">Atualizado em ${formatDate(project.updatedAt)}</time>
    </div>
  `;
  return article;
};

const populateLanguages = () => {
  [...new Set(projects.map((project) => project.language))]
    .sort((a, b) => a.localeCompare(b, "pt-BR"))
    .forEach((language) => {
      const option = document.createElement("option");
      option.value = language;
      option.textContent = language;
      languageSelect.append(option);
    });
};

const renderProjects = () => {
  const query = searchInput.value.trim().toLowerCase();
  const language = languageSelect.value;
  const sort = sortSelect.value;
  const filtered = projects
    .filter((project) => {
      const matchesQuery = `${project.name} ${project.description} ${project.language}`
        .toLowerCase()
        .includes(query);
      const matchesLanguage = language === "all" || project.language === language;
      return matchesQuery && matchesLanguage;
    })
    .sort((a, b) => {
      if (sort === "name") return a.name.localeCompare(b.name, "pt-BR");
      if (sort === "stars") return b.stars - a.stars || a.name.localeCompare(b.name, "pt-BR");
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });

  projectList.replaceChildren(...filtered.map(createProjectCard));
  projectStatus.textContent = filtered.length
    ? `${filtered.length} projeto${filtered.length === 1 ? "" : "s"}`
    : "Nenhum projeto encontrado. Tente outro termo ou selecione todas as linguagens.";
};

populateLanguages();
renderProjects();
searchInput.addEventListener("input", renderProjects);
languageSelect.addEventListener("change", renderProjects);
sortSelect.addEventListener("change", renderProjects);
