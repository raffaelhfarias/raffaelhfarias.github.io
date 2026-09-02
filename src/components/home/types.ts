export interface Metric {
  value: string;
  label: string;
  qualifier?: string;
}
export interface FeaturedProject {
  title: string;
  summary: string;
  href: string;
  stack: string[];
  metric: Metric;
}
export interface ProcessStep {
  index: string;
  title: string;
  description: string;
}
export interface SkillGroup {
  title: string;
  evidence: string;
  href: string;
}
export interface ContactLink {
  label: string;
  href: string;
  external?: boolean;
}
