import fs from "node:fs/promises";
import path from "node:path";
import { LOGS, REUNIONES, RE_FECHA, RE_SLUG, TAREAS, hoy } from "./raiz";
import type { Dia, Estado, Reunion, Tarea } from "./tipos";

export function slugify(titulo: string): string {
  return titulo
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

async function leer(ruta: string): Promise<string | null> {
  try {
    return await fs.readFile(ruta, "utf8");
  } catch {
    return null;
  }
}

async function existe(ruta: string): Promise<boolean> {
  try {
    await fs.access(ruta);
    return true;
  } catch {
    return false;
  }
}

async function leerTareas(): Promise<Tarea[]> {
  const crudo = await leer(TAREAS);
  if (!crudo) return [];
  try {
    const datos: unknown = JSON.parse(crudo);
    if (!Array.isArray(datos)) return [];
    return datos
      .filter((t): t is Record<string, unknown> => typeof t === "object" && t !== null)
      .map((t) => ({
        id: String(t.id ?? ""),
        descripcion: String(t.descripcion ?? ""),
        responsable: String(t.responsable ?? "sin definir"),
        fecha: String(t.fecha ?? "sin definir"),
        estado: String(t.estado ?? "abierta"),
        reunion: String(t.reunion ?? ""),
      }))
      .filter((t) => t.id);
  } catch {
    return [];
  }
}

function secciones(md: string): Map<string, string[]> {
  const mapa = new Map<string, string[]>();
  let actual = "_intro";
  mapa.set(actual, []);
  for (const linea of md.split("\n")) {
    const h = /^##\s+(.+?)\s*$/.exec(linea);
    if (h) {
      actual = h[1].toLowerCase();
      mapa.set(actual, []);
    } else if (/^#\s/.test(linea)) {
      continue;
    } else {
      mapa.get(actual)!.push(linea);
    }
  }
  return mapa;
}

function parsearAgenda(lineas: string[]): { agenda: Omit<Reunion, "brief" | "minuta">[]; avisos: string[] } {
  const agenda: Omit<Reunion, "brief" | "minuta">[] = [];
  const avisos: string[] = [];
  for (const crudo of lineas) {
    const linea = crudo.trim();
    if (!linea || linea === "- (vacía)") continue;
    const m = /^-\s+(\d{1,2}:\d{2})\s+(.+)$/.exec(linea);
    if (!m) {
      avisos.push(linea.replace(/^[-(]\s*|\)$/g, "").trim());
      continue;
    }
    const resto = m[2];
    const corte = resto.indexOf(": ");
    const titulo = corte === -1 ? resto : resto.slice(0, corte);
    let texto = corte === -1 ? "" : resto.slice(corte + 2);
    let nota: string | null = null;
    const par = /\s*\(([^()]*)\)\s*$/.exec(texto);
    if (/^no se pudo preparar/i.test(texto)) {
      nota = texto;
      texto = "";
    } else if (par && /brief existente/i.test(par[1])) {
      nota = par[1];
      texto = texto.slice(0, par.index).trim();
    }
    agenda.push({ hora: m[1].padStart(5, "0"), titulo: titulo.trim(), resumen: texto, slug: slugify(titulo), nota });
  }
  return { agenda, avisos };
}

function listaNumerada(lineas: string[]): string[] {
  return lineas
    .map((l) => /^\s*\d+\.\s+(.+)$/.exec(l)?.[1].trim())
    .filter((x): x is string => Boolean(x));
}

async function leerDia(fecha: string): Promise<Dia | null> {
  const carpeta = path.join(REUNIONES, fecha);
  const resumen = await leer(path.join(carpeta, "resumen-dia.md"));
  const log = (await leer(path.join(LOGS, `${fecha}.md`))) ?? "";
  const logLineas = log.split("\n").map((l) => l.trim()).filter(Boolean);
  if (resumen === null && logLineas.length === 0) return null;

  const sec = secciones(resumen ?? "");
  const { agenda, avisos } = parsearAgenda(sec.get("agenda") ?? []);
  const intro = (sec.get("_intro") ?? []).map((l) => l.trim()).filter(Boolean);

  const reuniones: Reunion[] = [];
  for (const r of agenda) {
    const base = path.join(carpeta, r.slug);
    reuniones.push({
      ...r,
      brief: RE_SLUG.test(r.slug) && (await existe(path.join(base, "brief.md"))),
      minuta: RE_SLUG.test(r.slug) && (await existe(path.join(base, "minuta.md"))),
    });
  }

  const errores = (sec.get("errores") ?? [])
    .map((l) => l.replace(/^-\s*/, "").trim())
    .filter((l) => l && l !== "ninguno");

  return {
    fecha,
    avisos: [...intro, ...avisos],
    agenda: reuniones,
    recordar: listaNumerada(sec.get("las 3 cosas que no me puedo olvidar hoy") ?? []),
    errores,
    log: logLineas,
  };
}

export async function leerEstado(): Promise<Estado> {
  const [tareas, carpetas] = await Promise.all([
    leerTareas(),
    fs.readdir(REUNIONES).catch(() => [] as string[]),
  ]);
  const fechas = new Set(carpetas.filter((c) => RE_FECHA.test(c)));
  for (const f of await fs.readdir(LOGS).catch(() => [] as string[])) {
    const m = /^(\d{4}-\d{2}-\d{2})\.md$/.exec(f);
    if (m) fechas.add(m[1]);
  }
  const dias = (await Promise.all([...fechas].sort().map(leerDia))).filter((d): d is Dia => d !== null);
  return { hoy: hoy(), generado: new Date().toISOString(), tareas, dias };
}

export async function leerDocumento(fecha: string, slug: string, tipo: "brief" | "minuta") {
  if (!RE_FECHA.test(fecha) || !RE_SLUG.test(slug)) return null;
  return leer(path.join(REUNIONES, fecha, slug, `${tipo}.md`));
}
