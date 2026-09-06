// Dynamic corridor data loader
// Imports all corridor JSONs at build time via Vite glob
/* eslint-disable @typescript-eslint/no-explicit-any */
const corridorModules: Record<string, any> = import.meta.glob("../data/corridors/*/tradeoff.json", { eager: true });
const explanationModules: Record<string, any> = import.meta.glob("../data/corridors/*/explanations.json", { eager: true });
const routesModules: Record<string, any> = import.meta.glob("../data/corridors/*/routes.json", { eager: true });
const statusModules: Record<string, any> = import.meta.glob("../data/corridors/*/status.json", { eager: true });
const noticesModules: Record<string, any> = import.meta.glob("../data/corridors/*/notices.json", { eager: true });
const bergsModules: Record<string, any> = import.meta.glob("../data/corridors/*/bergs.json", { eager: true });

function getData(modules: Record<string, any>, corridorId: string): any {
  for (const [path, mod] of Object.entries(modules)) {
    if (path.includes(`/${corridorId}/`)) {
      return (mod as { default: any }).default;
    }
  }
  throw new Error(`Missing data for corridor: ${corridorId}`);
}

export function getTradeoff(corridorId: string) {
  return getData(corridorModules, corridorId);
}

export function getExplanations(corridorId: string) {
  return getData(explanationModules, corridorId);
}

export function getRoutes(corridorId: string) {
  return getData(routesModules, corridorId);
}

export function getStatus(corridorId: string) {
  return getData(statusModules, corridorId);
}

export function getNotices(corridorId: string) {
  return getData(noticesModules, corridorId);
}

export function getBergs(corridorId: string) {
  return getData(bergsModules, corridorId);
}
