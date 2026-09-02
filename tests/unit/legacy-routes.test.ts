import { describe, expect, test } from "vitest";

import { legacyRoutes } from "../../src/data/legacy-routes";

const currentSlugs = [
  "Churn-Prediction",
  "Cine-Match",
  "Dados-Airbnb",
  "Panorama-COVID-19",
  "Gasolina-Preco",
  "Tensões-Comerciais-EUA-China-e-Impactos-no-Brasil",
  "whatsapp-sender",
  "banco-de-horas",
  "aniversariantes-whatsapp",
  "auditorias-vidibr",
  "baixas-financeiras-google-drive",
  "resultados-venda-direta-browserless",
  "relatorio-iaf-trimestral",
  "recebimentos-e-pagamentos",
  "folha-pagamento-via-whatsapp",
] as const;

describe("legacyRoutes", () => {
  test("maps every current Jekyll slug to a unique Portuguese destination", () => {
    expect(Object.keys(legacyRoutes).sort()).toEqual([...currentSlugs].sort());
    const destinations = Object.values(legacyRoutes);
    expect(
      destinations.every((destination) => destination.startsWith("/pt/")),
    ).toBe(true);
    expect(new Set(destinations).size).toBe(destinations.length);
  });
});
