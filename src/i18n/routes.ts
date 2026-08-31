import type { Locale } from "./locales";
import { isLocale } from "./locales";

const routeKeys = ["projects", "about", "articles", "direct-sales"] as const;

type RouteKey = (typeof routeKeys)[number];

export const routeAliases = {
  projects: { pt: "projetos", en: "projects" },
  about: { pt: "sobre", en: "about" },
  articles: { pt: "artigos", en: "articles" },
  "direct-sales": { pt: "venda-direta", en: "direct-sales" },
} as const satisfies Record<RouteKey, Record<Locale, string>>;

function isRouteKey(value: string): value is RouteKey {
  return routeKeys.some((key) => key === value);
}

function segments(path: string): string[] {
  return path.split("/").filter(Boolean);
}

function logicalSegment(segment: string): string {
  return (
    routeKeys.find(
      (key) =>
        routeAliases[key].pt === segment || routeAliases[key].en === segment,
    ) ?? segment
  );
}

export function localizedPath(locale: Locale, logicalPath = ""): string {
  const translated = segments(logicalPath).map((segment) =>
    isRouteKey(segment) ? routeAliases[segment][locale] : segment,
  );

  return `/${locale}/${translated.join("/")}`.replace(/\/$/, "") + "/";
}

export function swapLocale(pathname: string, target: Locale): string {
  const pathSegments = segments(pathname);
  const logical = (
    isLocale(pathSegments[0]) ? pathSegments.slice(1) : pathSegments
  ).map(logicalSegment);

  return localizedPath(target, logical.join("/"));
}
