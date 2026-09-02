export const locales = ["pt", "en"] as const;

export type Locale = (typeof locales)[number];

export const ui = {
  pt: {
    projects: "Projetos",
    about: "Sobre",
    articles: "Artigos",
    resume: "Currículo",
  },
  en: {
    projects: "Projects",
    about: "About",
    articles: "Articles",
    resume: "Résumé",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export function isLocale(value: string): value is Locale {
  return locales.includes(value as Locale);
}
