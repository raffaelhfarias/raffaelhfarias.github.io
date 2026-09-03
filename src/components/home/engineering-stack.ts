export type ToolStatus = "confirmed" | "in-depth";
export type ToolGroupSlug =
  "data" | "automation" | "integration" | "infrastructure" | "cloud";

export interface EngineeringTool {
  slug: string;
  name: string;
  role: string;
  logo?: string;
  mark?: string;
  status: ToolStatus;
}

export interface EngineeringToolGroup {
  slug: ToolGroupSlug;
  title: string;
  tools: EngineeringTool[];
}

type SharedTool = Omit<EngineeringTool, "role">;

const sharedGroups: Record<ToolGroupSlug, SharedTool[]> = {
  data: [
    {
      slug: "python",
      name: "Python",
      logo: "/assets/img/stacks/python.svg",
      status: "confirmed",
    },
    {
      slug: "sql",
      name: "SQL",
      logo: "/assets/img/stacks/azure-sql-server.svg",
      status: "confirmed",
    },
  ],
  automation: [
    {
      slug: "kestra",
      name: "Kestra",
      logo: "/assets/img/stacks/kestra.svg",
      status: "confirmed",
    },
    {
      slug: "playwright",
      name: "Playwright",
      logo: "/assets/img/stacks/playwright.svg",
      status: "confirmed",
    },
    {
      slug: "browserless",
      name: "Browserless",
      logo: "/assets/img/stacks/browserless-light.svg",
      status: "confirmed",
    },
  ],
  integration: [
    {
      slug: "evolution-api",
      name: "Evolution API",
      mark: "EA",
      status: "confirmed",
    },
    {
      slug: "rest-webhooks",
      name: "REST e webhooks",
      logo: "/assets/img/stacks/webhookd.svg",
      status: "confirmed",
    },
  ],
  infrastructure: [
    {
      slug: "docker",
      name: "Docker",
      logo: "/assets/img/stacks/docker.svg",
      status: "confirmed",
    },
    {
      slug: "linux",
      name: "Linux",
      logo: "/assets/img/stacks/linux.svg",
      status: "confirmed",
    },
    {
      slug: "coolify",
      name: "Coolify",
      logo: "/assets/img/stacks/coolify.svg",
      status: "confirmed",
    },
    {
      slug: "git",
      name: "Git",
      logo: "/assets/img/stacks/git.svg",
      status: "confirmed",
    },
  ],
  cloud: [
    {
      slug: "azure",
      name: "Azure",
      logo: "/assets/img/stacks/azure-color.svg",
      status: "in-depth",
    },
  ],
};

function withRole(tool: SharedTool, role: string): EngineeringTool {
  return { ...tool, role };
}

export const engineeringToolGroups: Record<
  "pt" | "en",
  EngineeringToolGroup[]
> = {
  pt: [
    {
      slug: "data",
      title: "Dados e transformação",
      tools: [
        withRole(sharedGroups.data[0], "Parsing e regras"),
        withRole(sharedGroups.data[1], "Consulta e modelagem"),
      ],
    },
    {
      slug: "automation",
      title: "Orquestração e automação",
      tools: [
        withRole(sharedGroups.automation[0], "Orquestração"),
        withRole(sharedGroups.automation[1], "Automação web"),
        withRole(sharedGroups.automation[2], "Navegação remota"),
      ],
    },
    {
      slug: "integration",
      title: "Integrações e mensageria",
      tools: [
        withRole(sharedGroups.integration[0], "Entrega de relatórios"),
        withRole(sharedGroups.integration[1], "Integração de serviços"),
      ],
    },
    {
      slug: "infrastructure",
      title: "Infraestrutura",
      tools: [
        withRole(sharedGroups.infrastructure[0], "Containers"),
        withRole(sharedGroups.infrastructure[1], "Operação de VM"),
        withRole(sharedGroups.infrastructure[2], "Deploy em VM"),
        withRole(sharedGroups.infrastructure[3], "Versionamento"),
      ],
    },
    {
      slug: "cloud",
      title: "Cloud",
      tools: [withRole(sharedGroups.cloud[0], "Em aprofundamento")],
    },
  ],
  en: [
    {
      slug: "data",
      title: "Data and transformation",
      tools: [
        withRole(sharedGroups.data[0], "Parsing and rules"),
        withRole(sharedGroups.data[1], "Queries and modeling"),
      ],
    },
    {
      slug: "automation",
      title: "Orchestration and automation",
      tools: [
        withRole(sharedGroups.automation[0], "Orchestration"),
        withRole(sharedGroups.automation[1], "Web automation"),
        withRole(sharedGroups.automation[2], "Remote browsing"),
      ],
    },
    {
      slug: "integration",
      title: "Integrations and messaging",
      tools: [
        withRole(sharedGroups.integration[0], "Report delivery"),
        withRole(
          { ...sharedGroups.integration[1], name: "REST and webhooks" },
          "Service integration",
        ),
      ],
    },
    {
      slug: "infrastructure",
      title: "Infrastructure",
      tools: [
        withRole(sharedGroups.infrastructure[0], "Containers"),
        withRole(sharedGroups.infrastructure[1], "VM operations"),
        withRole(sharedGroups.infrastructure[2], "VM deployment"),
        withRole(sharedGroups.infrastructure[3], "Version control"),
      ],
    },
    {
      slug: "cloud",
      title: "Cloud",
      tools: [withRole(sharedGroups.cloud[0], "In progress")],
    },
  ],
};
