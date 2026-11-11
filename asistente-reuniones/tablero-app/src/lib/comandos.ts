import { spawn, type ChildProcess } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { RAIZ, REUNIONES, fechaValida } from "./raiz";
import { emitir } from "./vivo";
import type { EstadoJob } from "./tipos";

// ---------------------------------------------------------------------------
// Qué puede hacer Claude cuando lo lanza el tablero.
// Lista cerrada: solo leer el calendario, Gmail y Drive, escribir archivos del
// proyecto y dejar BORRADORES. Enviar mails, crear/mover eventos o borrar nada
// queda prohibido aunque alguna skill lo pidiera.
// ---------------------------------------------------------------------------
const CAL = "mcp__claude_ai_Google_Calendar";
const GMAIL = "mcp__claude_ai_Gmail";
const DRIVE = "mcp__claude_ai_Google_Drive";
const DOCS = "mcp__claude_ai_Google_Docs";

const PERMITIDAS = [
  "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Skill",
  `${CAL}__list_events`, `${CAL}__get_event`, `${CAL}__search_events`, `${CAL}__list_calendars`,
  `${GMAIL}__search_threads`, `${GMAIL}__get_thread`, `${GMAIL}__get_message`,
  `${GMAIL}__create_draft`, `${GMAIL}__list_drafts`, `${GMAIL}__get_draft`,
  `${DRIVE}__search_files`, `${DRIVE}__read_file_content`, `${DRIVE}__get_file_metadata`, `${DRIVE}__list_recent_files`,
  `${DOCS}__read_doc`,
];

const PROHIBIDAS = [
  "Bash", "WebFetch", "WebSearch",
  `${GMAIL}__send_message`, `${GMAIL}__reply`, `${GMAIL}__forward`,
  `${GMAIL}__trash_message`, `${GMAIL}__trash_thread`, `${GMAIL}__delete_draft`,
  `${CAL}__create_event`, `${CAL}__update_event`, `${CAL}__delete_event`, `${CAL}__respond_to_event`,
  `${DRIVE}__share_file`, `${DRIVE}__trash_file`, `${DRIVE}__update_file`, `${DRIVE}__create_file`,
];

const MAX_NOTAS = 20_000;
const MAX_MINUTOS = 20;
const MAX_LINEAS = 400;

export type Pedido =
  | { comando: "preparar-dia"; alcance: "hoy" | "semana" | "fecha"; fecha?: string }
  | { comando: "cerrar-reunion"; reunion: string; notas: string };

type Resultado = { ok: true; job: EstadoJob } | { ok: false; error: string; codigo: number };

const g = globalThis as unknown as { __tableroJob?: { job: EstadoJob | null; proc: ChildProcess | null } };
const estado = (g.__tableroJob ??= { job: null, proc: null });

export function jobActual(): EstadoJob | null {
  return estado.job;
}

function validar(p: unknown): { ok: true; pedido: Pedido } | { ok: false; error: string } {
  if (typeof p !== "object" || p === null) return { ok: false, error: "Pedido inválido." };
  const x = p as Record<string, unknown>;
  if (x.comando === "preparar-dia") {
    if (x.alcance === "hoy" || x.alcance === "semana") return { ok: true, pedido: { comando: "preparar-dia", alcance: x.alcance } };
    if (x.alcance === "fecha" && typeof x.fecha === "string" && fechaValida(x.fecha))
      return { ok: true, pedido: { comando: "preparar-dia", alcance: "fecha", fecha: x.fecha } };
    return { ok: false, error: "Elegí hoy, la semana o una fecha válida." };
  }
  if (x.comando === "cerrar-reunion") {
    const notas = typeof x.notas === "string" ? x.notas.trim() : "";
    const reunion = typeof x.reunion === "string" ? x.reunion.trim() : "";
    if (!notas) return { ok: false, error: "Pegá las notas de la reunión." };
    if (notas.length > MAX_NOTAS) return { ok: false, error: `Las notas superan los ${MAX_NOTAS} caracteres.` };
    if (!/^[\p{L}\p{N} .,:;()\-¿?¡!/&+]{3,120}$/u.test(reunion))
      return { ok: false, error: "Escribí el título de la reunión (3 a 120 caracteres, sin símbolos raros)." };
    return { ok: true, pedido: { comando: "cerrar-reunion", reunion, notas } };
  }
  return { ok: false, error: "Comando no permitido." };
}

async function armarPrompt(p: Pedido): Promise<{ prompt: string; detalle: string }> {
  if (p.comando === "preparar-dia") {
    if (p.alcance === "hoy") return { prompt: "/preparar-dia", detalle: "hoy" };
    if (p.alcance === "semana")
      return { prompt: "/preparar-dia de todos los dias de esta semana", detalle: "toda la semana" };
    return { prompt: `/preparar-dia ${p.fecha}`, detalle: p.fecha! };
  }
  // Las notas van a un archivo: el prompt solo lleva la ruta, nunca el texto.
  const carpeta = path.join(REUNIONES, "_entrada");
  await fs.mkdir(carpeta, { recursive: true, mode: 0o700 });
  const archivo = path.join(carpeta, `notas-${Date.now()}.txt`);
  await fs.writeFile(archivo, p.notas, { mode: 0o600 });
  const relativo = path.relative(RAIZ, archivo);
  return {
    prompt:
      `/cerrar-reunion ${relativo}\n\n` +
      `La persona confirmó desde el tablero que la reunión es «${p.reunion}»: no pidas confirmación. ` +
      `Ejecutás sin supervisión: guardá la minuta y las tareas, dejá el mail solo como borrador, ` +
      `NO crees eventos ni envíes mails; si las notas acordaron una próxima reunión, anotala como propuesta en el resumen.`,
    detalle: p.reunion,
  };
}

function agregar(job: EstadoJob, texto: string) {
  for (const l of texto.split("\n")) {
    const linea = l.trimEnd();
    if (!linea) continue;
    job.lineas.push(linea.slice(0, 400));
  }
  if (job.lineas.length > MAX_LINEAS) job.lineas.splice(0, job.lineas.length - MAX_LINEAS);
  emitir({ tipo: "job", job });
}

function interpretar(job: EstadoJob, linea: string) {
  let m: Record<string, any>;
  try {
    m = JSON.parse(linea);
  } catch {
    return;
  }
  if (m.type === "assistant") {
    for (const b of m.message?.content ?? []) {
      if (b.type === "text" && typeof b.text === "string") agregar(job, b.text);
      if (b.type === "tool_use") {
        const nombre = String(b.name ?? "").split("__").pop();
        const extra = b.input?.description ?? b.input?.file_path ?? "";
        agregar(job, `→ ${nombre}${extra ? `: ${String(extra).slice(0, 120)}` : ""}`);
      }
    }
  } else if (m.type === "result") {
    job.estado = m.is_error ? "fallo" : "terminado";
    if (typeof m.result === "string" && m.result) agregar(job, m.result);
  }
}

export async function lanzar(crudo: unknown): Promise<Resultado> {
  if (estado.job?.estado === "corriendo")
    return { ok: false, error: "Ya hay un comando corriendo. Esperá a que termine.", codigo: 409 };
  const v = validar(crudo);
  if (!v.ok) return { ok: false, error: v.error, codigo: 400 };

  const { prompt, detalle } = await armarPrompt(v.pedido);
  const job: EstadoJob = {
    id: randomUUID(),
    comando: v.pedido.comando,
    detalle,
    estado: "corriendo",
    inicio: new Date().toISOString(),
    lineas: [],
  };
  estado.job = job;

  const bin = process.env.CLAUDE_BIN || "claude";
  const args = [
    "-p", prompt,
    "--output-format", "stream-json", "--verbose",
    "--no-session-persistence",
    "--max-budget-usd", "5",
    `--allowedTools=${PERMITIDAS.join(",")}`,
    `--disallowedTools=${PROHIBIDAS.join(",")}`,
  ];
  // Sin shell: los argumentos viajan como lista, nada se interpreta como comando.
  const proc = spawn(bin, args, { cwd: RAIZ, stdio: ["ignore", "pipe", "pipe"], shell: false });
  estado.proc = proc;

  const tope = setTimeout(() => {
    agregar(job, `Se cortó: pasaron ${MAX_MINUTOS} minutos.`);
    proc.kill("SIGTERM");
  }, MAX_MINUTOS * 60_000);

  let resto = "";
  proc.stdout.on("data", (d: Buffer) => {
    resto += d.toString("utf8");
    const partes = resto.split("\n");
    resto = partes.pop() ?? "";
    for (const p of partes) interpretar(job, p);
  });
  proc.stderr.on("data", (d: Buffer) => agregar(job, d.toString("utf8")));
  proc.on("error", (e) => {
    clearTimeout(tope);
    job.estado = "fallo";
    agregar(job, `No se pudo iniciar Claude: ${e.message}`);
  });
  proc.on("close", (codigo) => {
    clearTimeout(tope);
    if (resto) interpretar(job, resto);
    if (job.estado === "corriendo") job.estado = codigo === 0 ? "terminado" : "fallo";
    estado.proc = null;
    emitir({ tipo: "job", job });
    emitir({ tipo: "cambio" });
  });

  emitir({ tipo: "job", job });
  return { ok: true, job };
}

export function cancelar(): boolean {
  if (estado.proc && estado.job?.estado === "corriendo") {
    estado.proc.kill("SIGTERM");
    agregar(estado.job, "Cancelado desde el tablero.");
    return true;
  }
  return false;
}
