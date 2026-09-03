export type ToolStatus = "confirmed" | "in-depth";
export type ToolGroupSlug =
  | "data"
  | "automation"
  | "integration"
  | "infrastructure"
  | "cloud";

export interface EngineeringTool {
  slug: string;
  name: string;
  role: string;
  logo: string;
  status: ToolStatus;
}

export interface EngineeringToolGroup {
  slug: ToolGroupSlug;
  title: string;
  tools: EngineeringTool[];
}

const sharedGroups = {
  data: [
    {
      slug: "python",
      name: "Python",
      logo: "/images/tools/python.svg",
      status: "confirmed",
    },
    {
      slug: "sql",
      name: "SQL",
      logo: "/images/tools/sql.svg",
      status: "confirmed",
    },
  ],
  automation: [
    {
      slug: "kestra",
      name: "Kestra",
      logo: "/images/tools/kestra.svg",
      status: "confirmed",
    },
    {
      slug: "playwright",
      name: "Playwright",
      logo: "/images/tools/playwright.svg",
      status: "confirmed",
    },
    {
      slug: "browserless",
      name: "Browserless",
      logo: "/images/tools/browserless.svg",
      status: "confirmed",
    },
  ],
  integration: [
    {
      slug: "evolution-api",
      name: "Evolution API",
      logo: "/images/tools/evolution-api.svg",
      status: "confirmed",
    },
    {
      slug: "rest-webhooks",
      name: "REST e webhooks",
      logo: "/images/tools/rest-webhooks.svg",
      status: "confirmed",
    },
  ],
  infrastructure: [
    {
      slug: "docker",
      name: "Docker",
      logo: "/images/tools/docker.svg",
      status: "confirmed",
    },
    {
      slug: "linux",
      name: "Linux",
      logo: "/images/tools/linux.svg",
      status: "confirmed",
    },
    {
      slug: "coolify",
      name: "Coolify",
      logo: "/images/tools/coolify.svg",
      status: "confirmed",
    },
    {
      slug: "git",
      name: "Git",
      logo: "/images/tools/git.svg",
      status: "confirmed",
    },
  ],
  cloud: [
    {
      slug: "azure",
      name: "Azure",
      logo: "/images/tools/azure.svg",
      status: "in-depth",
    },
  ],
} as const;

type SharedTool = (typeof sharedGroups)[keyof typeof sharedGroups][number];

function withRole(
  tool: SharedTool,
  role: string,
): EngineeringTool {
  return { ...tool, role };
}

export const engineeringToolGroups: Record<"pt" | "en", EngineeringToolGroup[]> = {
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
        withRole(sharedGroups.integration[1], "Service integration"),
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
