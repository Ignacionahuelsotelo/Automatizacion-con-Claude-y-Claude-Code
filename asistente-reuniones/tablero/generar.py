#!/usr/bin/env python3
"""Genera tablero/index.html a partir de tareas/tareas.json.

Uso: python3 tablero/generar.py
El resultado es un único archivo HTML autocontenido (sin librerías ni pedidos
externos): se abre con doble clic. Todos los datos salen del JSON.
"""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "tareas" / "tareas.json"
SALIDA = RAIZ / "tablero" / "index.html"
ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Tablero de pendientes</title>
<style>
:root {
  --bg: #eef1f5; --surface: #ffffff; --ink: #14202c; --muted: #566677;
  --line: #d5dce5; --accent: #1d4ed8; --accent-bg: #e4ebfd;
  --late: #b42318; --late-bg: #fdecea;
  --soon: #7a5200; --soon-bg: #fff1cc;
  --none: #5b3fae; --none-bg: #eee9ff;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0e141b; --surface: #151d27; --ink: #e8eef5; --muted: #9aabbc;
    --line: #263341; --accent: #86a8ff; --accent-bg: #1b2a4d;
    --late: #ff8a78; --late-bg: #3a1c19;
    --soon: #f3c060; --soon-bg: #3a2d12;
    --none: #bba9ff; --none-bg: #2a2144;
  }
}
:root[data-theme="dark"] {
  --bg: #0e141b; --surface: #151d27; --ink: #e8eef5; --muted: #9aabbc;
  --line: #263341; --accent: #86a8ff; --accent-bg: #1b2a4d;
  --late: #ff8a78; --late-bg: #3a1c19;
  --soon: #f3c060; --soon-bg: #3a2d12;
  --none: #bba9ff; --none-bg: #2a2144;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.5 var(--sans); font-variant-numeric: tabular-nums;
}
button, input, select { font: inherit; color: inherit; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.wrap { max-width: 1280px; margin: 0 auto; padding: 24px 16px 64px; }

/* Encabezado */
.top { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
h1 { font: 600 clamp(1.9rem, 5vw, 2.8rem)/1.05 var(--serif); letter-spacing: -0.01em; margin: 0; }
.top p { margin: 6px 0 0; color: var(--muted); font-size: .9rem; }
.theme {
  border: 1px solid var(--line); background: var(--surface); border-radius: 999px;
  padding: 8px 14px; cursor: pointer; font-size: .875rem;
}
.theme:hover { border-color: var(--muted); }

/* Tarjetas de resumen */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 28px 0 20px; }
.stat {
  --tone: var(--accent); --tone-bg: var(--accent-bg);
  position: relative; text-align: left; cursor: pointer;
  background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
  padding: 16px 16px 14px 20px; overflow: hidden;
}
.stat::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 6px; background: var(--tone); }
.stat[aria-pressed="true"] { background: var(--tone-bg); border-color: var(--tone); }
.stat:hover { border-color: var(--tone); }
.stat .n { display: block; font: 600 clamp(2.2rem, 6vw, 3.2rem)/1 var(--serif); }
.stat .l { display: block; margin-top: 6px; color: var(--muted); font-size: .9rem; }
.stat[aria-pressed="true"] .l { color: var(--ink); }
.stat.late { --tone: var(--late); --tone-bg: var(--late-bg); }
.stat.late.hot .n { color: var(--late); }
.stat.soon { --tone: #c98a00; --tone-bg: var(--soon-bg); }
.stat.none { --tone: var(--none); --tone-bg: var(--none-bg); }

/* Filtros */
.tools { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 8px; }
.tools input, .tools select {
  min-height: 44px; background: var(--surface); border: 1px solid var(--line);
  border-radius: 8px; padding: 8px 12px;
}
.tools input { flex: 1 1 240px; }
.tools select { flex: 0 1 320px; max-width: 100%; }
.tools input::placeholder { color: var(--muted); }
.count { color: var(--muted); font-size: .875rem; margin: 0 0 24px; min-height: 1.4em; }
.link {
  background: none; border: 0; color: var(--accent); text-decoration: underline;
  padding: 0; cursor: pointer;
}

/* Secciones */
h2 { font: 600 1.35rem/1.2 var(--serif); margin: 0 0 14px; }
.board { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; align-items: start; }
.col { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.col-h { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-bottom: 1px solid var(--line); }
.avatar {
  flex: none; width: 40px; height: 40px; border-radius: 50%;
  display: grid; place-items: center; background: var(--accent-bg); color: var(--accent);
  font: 600 1rem var(--serif);
}
.col-h h3 { margin: 0; font: 600 1.1rem/1.2 var(--serif); }
.col-h small { display: block; color: var(--muted); font-size: .8rem; }
.col-h .badge { margin-left: auto; }
.badge {
  display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: .78rem; font-weight: 600;
  background: var(--late-bg); color: var(--late); white-space: nowrap;
}
.badge.none { background: var(--none-bg); color: var(--none); }
ul.tasks { list-style: none; margin: 0; padding: 0; }
.task { display: grid; grid-template-columns: 56px 1fr; gap: 12px; padding: 14px 16px; border-top: 1px solid var(--line); }
.task:first-child { border-top: 0; }
.date {
  width: 56px; height: 60px; border: 1px solid var(--line); border-radius: 8px;
  display: grid; align-content: center; justify-items: center; line-height: 1.1; background: var(--bg);
}
.date b { font: 600 1.45rem var(--serif); }
.date span { font-size: .75rem; color: var(--muted); }
.date.late { background: var(--late-bg); border-color: var(--late); color: var(--late); }
.date.late span { color: var(--late); }
.date.today { border-color: var(--accent); background: var(--accent-bg); color: var(--accent); }
.date.today span { color: var(--accent); }
.date.nodate b { color: var(--muted); }
.task p { margin: 0; overflow-wrap: anywhere; }
.when { font-size: .85rem; color: var(--muted); margin-top: 4px; }
.when.late { color: var(--late); font-weight: 600; }
.when.today { color: var(--accent); font-weight: 600; }
.meta { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 6px; font-size: .8rem; color: var(--muted); }
.task.done p { text-decoration: line-through; color: var(--muted); }
.task.done .date { opacity: .6; }

.pending { margin-top: 36px; border: 2px dashed var(--line); border-radius: 12px; padding: 18px 16px 6px; background: color-mix(in srgb, var(--surface) 60%, transparent); }
.pending > p { margin: -6px 0 12px; color: var(--muted); font-size: .9rem; }
.pending ul.tasks { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin-bottom: 12px; }
.pending .task { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
.pending .task:first-child { border-top: 1px solid var(--line); }
.empty { padding: 28px 16px; text-align: center; color: var(--muted); }

@media (max-width: 720px) {
  .stats { grid-template-columns: repeat(2, 1fr); }
  .board { grid-template-columns: 1fr; }
  .pending ul.tasks { grid-template-columns: 1fr; }
  .task { grid-template-columns: 48px 1fr; padding: 12px; }
  .date { width: 48px; height: 54px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div>
      <h1>Tablero de pendientes</h1>
      <p id="generado"></p>
    </div>
    <button class="theme" id="tema" type="button"></button>
  </header>

  <section class="stats" id="stats" aria-label="Resumen"></section>

  <div class="tools">
    <input id="q" type="search" placeholder="Buscar por tarea, responsable o reunión" aria-label="Buscar tareas" autocomplete="off">
    <select id="reunion" aria-label="Filtrar por reunión"></select>
  </div>
  <p class="count" id="count" aria-live="polite"></p>

  <section aria-labelledby="h-resp">
    <h2 id="h-resp">Por responsable</h2>
    <div class="board" id="board"></div>
  </section>

  <section class="pending" id="pending" aria-labelledby="h-sd" hidden>
    <h2 id="h-sd">Sin definir</h2>
    <p>Tareas a las que les falta responsable o fecha. Conviene completarlas en la próxima reunión.</p>
    <ul class="tasks" id="pendingList"></ul>
  </section>
</div>

<script>
const TAREAS = __DATOS__;
const GENERADO = __GENERADO__;

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};
const norm = (s) => String(s == null ? "" : s).trim();
const sinDefinir = (s) => norm(s) === "" || norm(s).toLowerCase() === "sin definir";
const slugBonito = (s) => { const t = norm(s).replace(/-/g, " "); return t.charAt(0).toUpperCase() + t.slice(1); };
const pad = (n) => String(n).padStart(2, "0");
const DIA = 86400000;

/* Fechas: se calculan al abrir el archivo, contra el día de hoy */
const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
const dow = (hoy.getDay() + 6) % 7; /* lunes = 0 */
const finSemana = new Date(hoy.getTime() + (6 - dow) * DIA);
const mes = new Intl.DateTimeFormat("es-AR", { month: "short" });

function parseFecha(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(norm(s));
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
}
function diasHasta(f) { return Math.round((f - hoy) / DIA); }
function plural(n, uno, varios) { return n + " " + (n === 1 ? uno : varios); }

const tareas = TAREAS.map((t) => {
  const fecha = parseFecha(t.fecha);
  const abierta = ["abierta", "vencida"].includes(norm(t.estado).toLowerCase());
  const dias = fecha ? diasHasta(fecha) : null;
  return {
    id: norm(t.id), descripcion: norm(t.descripcion), responsable: norm(t.responsable),
    reunion: norm(t.reunion), estado: norm(t.estado), fecha, abierta, dias,
    sinResp: sinDefinir(t.responsable), sinFecha: !fecha,
    vencida: abierta && fecha !== null && dias < 0,
    semana: abierta && fecha !== null && fecha >= hoy && fecha <= finSemana,
  };
});

function ordenar(a, b) {
  if (a.abierta !== b.abierta) return a.abierta ? -1 : 1;
  if (a.fecha && b.fecha && a.fecha - b.fecha) return a.fecha - b.fecha;
  if (!a.fecha !== !b.fecha) return a.fecha ? -1 : 1;
  return a.id.localeCompare(b.id, "es", { numeric: true });
}

/* Estado de la vista */
const estado = { q: "", reunion: "", rapido: "" };

const RAPIDOS = [
  { k: "abiertas", clase: "", etiqueta: "Tareas abiertas", n: (t) => t.abierta },
  { k: "vencidas", clase: "late", etiqueta: "Vencidas", n: (t) => t.vencida },
  { k: "semana", clase: "soon", etiqueta: "Vencen esta semana", n: (t) => t.semana },
  { k: "sinresp", clase: "none", etiqueta: "Sin responsable", n: (t) => t.abierta && t.sinResp },
];

function coincide(t) {
  if (estado.reunion && t.reunion !== estado.reunion) return false;
  const r = RAPIDOS.find((x) => x.k === estado.rapido);
  if (r && !r.n(t)) return false;
  const q = estado.q.toLowerCase();
  if (q) {
    const pajar = [t.id, t.descripcion, t.responsable, t.reunion, slugBonito(t.reunion)].join(" ").toLowerCase();
    if (!q.split(/\s+/).every((p) => pajar.includes(p))) return false;
  }
  return true;
}

function bloqueFecha(t) {
  const d = el("div", "date");
  if (!t.fecha) {
    d.classList.add("nodate");
    d.append(el("b", null, "–"), el("span", null, "sin fecha"));
    return d;
  }
  if (t.vencida) d.classList.add("late");
  else if (t.abierta && t.dias === 0) d.classList.add("today");
  d.append(el("b", null, pad(t.fecha.getDate())), el("span", null, mes.format(t.fecha).replace(".", "")));
  return d;
}

function textoCuando(t) {
  if (!t.fecha) return null;
  const n = t.dias;
  if (!t.abierta) return { texto: "Fecha límite " + pad(t.fecha.getDate()) + "/" + pad(t.fecha.getMonth() + 1), clase: "" };
  if (n < 0) return { texto: "Vencida hace " + plural(-n, "día", "días"), clase: "late" };
  if (n === 0) return { texto: "Vence hoy", clase: "today" };
  if (n === 1) return { texto: "Vence mañana", clase: "" };
  return { texto: "Vence en " + plural(n, "día", "días"), clase: "" };
}

function itemTarea(t, conResponsable) {
  const li = el("li", "task" + (t.abierta ? "" : " done"));
  li.append(bloqueFecha(t));
  const cuerpo = el("div");
  cuerpo.append(el("p", null, t.descripcion));
  const c = textoCuando(t);
  if (c) cuerpo.append(el("div", "when " + c.clase, c.texto));
  const meta = el("div", "meta");
  meta.append(el("span", null, t.id));
  if (t.reunion) meta.append(el("span", null, slugBonito(t.reunion)));
  if (!t.abierta && t.estado) meta.append(el("span", null, "Estado: " + t.estado));
  if (conResponsable) {
    meta.append(el("span", null, t.sinResp ? "Responsable sin definir" : "Responsable: " + t.responsable));
  }
  cuerpo.append(meta);
  li.append(cuerpo);
  return li;
}

function iniciales(nombre) {
  const p = nombre.split(/\s+/).filter(Boolean);
  return ((p[0] || "?")[0] + (p.length > 1 ? p[p.length - 1][0] : "")).toUpperCase();
}

function dibujar() {
  const visibles = tareas.filter(coincide);

  /* Tarjetas: siempre sobre el total */
  const stats = $("stats");
  stats.textContent = "";
  RAPIDOS.forEach((r) => {
    const n = tareas.filter(r.n).length;
    const b = el("button", "stat " + r.clase + (r.k === "vencidas" && n > 0 ? " hot" : ""));
    b.type = "button";
    b.setAttribute("aria-pressed", String(estado.rapido === r.k));
    b.append(el("span", "n", String(n)), el("span", "l", r.etiqueta));
    b.addEventListener("click", () => { estado.rapido = estado.rapido === r.k ? "" : r.k; dibujar(); });
    stats.append(b);
  });

  /* Columnas por responsable (con responsable y fecha definidos) */
  const completas = visibles.filter((t) => !t.sinResp && !t.sinFecha);
  const porPersona = new Map();
  completas.forEach((t) => {
    if (!porPersona.has(t.responsable)) porPersona.set(t.responsable, []);
    porPersona.get(t.responsable).push(t);
  });
  const personas = [...porPersona.entries()].sort((a, b) => {
    const ab = (x) => x[1].filter((t) => t.abierta).length;
    return ab(b) - ab(a) || a[0].localeCompare(b[0], "es");
  });

  const board = $("board");
  board.textContent = "";
  personas.forEach(([nombre, lista]) => {
    lista.sort(ordenar);
    const abiertas = lista.filter((t) => t.abierta).length;
    const vencidas = lista.filter((t) => t.vencida).length;
    const col = el("article", "col");
    const h = el("div", "col-h");
    h.append(el("div", "avatar", iniciales(nombre)));
    const nom = el("div");
    nom.append(el("h3", null, nombre), el("small", null, plural(abiertas, "tarea abierta", "tareas abiertas")));
    h.append(nom);
    if (vencidas) h.append(el("span", "badge", plural(vencidas, "vencida", "vencidas")));
    col.append(h);
    const ul = el("ul", "tasks");
    lista.forEach((t) => ul.append(itemTarea(t, false)));
    col.append(ul);
    board.append(col);
  });
  if (!personas.length) {
    const vacio = el("div", "empty");
    vacio.textContent = tareas.length
      ? "No hay tareas con responsable y fecha que coincidan con los filtros."
      : "Todavía no hay tareas. Cerrá una reunión para cargar las primeras.";
    board.append(vacio);
  }

  /* Sin definir: falta responsable o fecha */
  const incompletas = visibles.filter((t) => t.sinResp || t.sinFecha).sort(ordenar);
  const sec = $("pending");
  sec.hidden = incompletas.length === 0;
  const ul = $("pendingList");
  ul.textContent = "";
  incompletas.forEach((t) => {
    const li = itemTarea(t, true);
    const falta = [];
    if (t.sinResp) falta.push("Sin responsable");
    if (t.sinFecha) falta.push("Sin fecha");
    const fila = el("div", "meta");
    falta.forEach((f) => fila.append(el("span", "badge none", f)));
    li.lastChild.append(fila);
    ul.append(li);
  });

  /* Contador */
  const filtrando = estado.q || estado.reunion || estado.rapido;
  const c = $("count");
  c.textContent = "";
  c.append(document.createTextNode(
    filtrando ? "Mostrando " + visibles.length + " de " + tareas.length + " tareas. " : tareas.length + " tareas en total. "
  ));
  if (filtrando) {
    const b = el("button", "link", "Borrar filtros");
    b.type = "button";
    b.addEventListener("click", () => {
      estado.q = ""; estado.reunion = ""; estado.rapido = "";
      $("q").value = ""; $("reunion").value = "";
      dibujar();
    });
    c.append(b);
  }
}

/* Filtro por reunión: las opciones salen de los datos */
(function () {
  const sel = $("reunion");
  const cuenta = new Map();
  tareas.forEach((t) => { if (t.reunion) cuenta.set(t.reunion, (cuenta.get(t.reunion) || 0) + 1); });
  sel.append(new Option("Todas las reuniones", ""));
  [...cuenta.keys()].sort((a, b) => a.localeCompare(b, "es")).forEach((r) => {
    sel.append(new Option(slugBonito(r) + " (" + cuenta.get(r) + ")", r));
  });
  sel.addEventListener("change", () => { estado.reunion = sel.value; dibujar(); });
  $("q").addEventListener("input", (e) => { estado.q = norm(e.target.value); dibujar(); });
})();

/* Tema claro u oscuro */
(function () {
  const raiz = document.documentElement;
  const btn = $("tema");
  const oscuroSistema = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
  const esOscuro = () => raiz.dataset.theme ? raiz.dataset.theme === "dark" : oscuroSistema();
  try { const g = localStorage.getItem("tablero-tema"); if (g) raiz.dataset.theme = g; } catch (e) {}
  const pintar = () => { btn.textContent = esOscuro() ? "Modo claro" : "Modo oscuro"; };
  btn.addEventListener("click", () => {
    const nuevo = esOscuro() ? "light" : "dark";
    raiz.dataset.theme = nuevo;
    try { localStorage.setItem("tablero-tema", nuevo); } catch (e) {}
    pintar();
  });
  pintar();
})();

$("generado").textContent = "Generado el " + GENERADO + " (hora de Buenos Aires)";
dibujar();
</script>
</body>
</html>
"""


def main():
    with open(ENTRADA, encoding="utf-8") as f:
        tareas = json.load(f)
    if not isinstance(tareas, list):
        raise SystemExit("tareas.json debe ser una lista de tareas.")

    def incrustar(valor):
        # JSON dentro de <script>: evita cerrar la etiqueta por accidente.
        texto = json.dumps(valor, ensure_ascii=False, indent=1)
        return texto.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    generado = datetime.now(ZONA).strftime("%d/%m/%Y %H:%M")
    html = PLANTILLA.replace("__DATOS__", incrustar(tareas)).replace("__GENERADO__", incrustar(generado))
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Tablero generado: {SALIDA} ({len(tareas)} tareas, {generado})")


if __name__ == "__main__":
    main()
