import path from "node:path";

// El tablero vive en <proyecto>/tablero-app; los datos están en <proyecto>.
export const RAIZ = path.resolve(/* turbopackIgnore: true */ process.cwd(), "..");
export const TAREAS = path.join(RAIZ, "tareas", "tareas.json");
export const REUNIONES = path.join(RAIZ, "reuniones");
export const LOGS = path.join(RAIZ, "logs");
export const ZONA = "America/Argentina/Buenos_Aires";

export const RE_FECHA = /^\d{4}-\d{2}-\d{2}$/;
export const RE_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function hoy(): string {
  // en-CA formatea como AAAA-MM-DD
  return new Intl.DateTimeFormat("en-CA", { timeZone: ZONA }).format(new Date());
}

export function fechaValida(f: string): boolean {
  if (!RE_FECHA.test(f)) return false;
  const d = new Date(`${f}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().startsWith(f);
}
