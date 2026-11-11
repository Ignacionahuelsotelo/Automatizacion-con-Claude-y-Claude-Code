"use client";

import { useMemo, useState } from "react";
import { ddmm, diaCorto, relativo } from "@/lib/fechas";
import type { Tarea } from "@/lib/tipos";

const SIN = "sin definir";
// Todo lo que no está cerrado sigue pendiente ("abierta", "vencida", ...).
const CERRADAS = new Set(["cerrada", "completada", "hecha", "cancelada"]);

type Grupo = { clave: string; titulo: string; tono: "tarde" | "hoy" | "normal"; items: Tarea[] };

export function Pendientes({ tareas, hoy }: { tareas: Tarea[]; hoy: string }) {
  const [quien, setQuien] = useState("todos");

  const abiertas = useMemo(() => tareas.filter((t) => !CERRADAS.has(t.estado.toLowerCase())), [tareas]);
  const personas = useMemo(
    () => [...new Set(abiertas.map((t) => t.responsable))].sort((a, b) => (a === SIN ? 1 : b === SIN ? -1 : a.localeCompare(b))),
    [abiertas],
  );

  const grupos = useMemo<Grupo[]>(() => {
    const visibles = abiertas.filter((t) => quien === "todos" || t.responsable === quien);
    const conFecha = (t: Tarea) => /^\d{4}-\d{2}-\d{2}$/.test(t.fecha);
    const orden = (a: Tarea, b: Tarea) => a.fecha.localeCompare(b.fecha) || a.id.localeCompare(b.id);
    const tarde = (t: Tarea) => t.estado.toLowerCase() === "vencida" || (conFecha(t) && t.fecha < hoy);
    const g: Grupo[] = [
      { clave: "tarde", titulo: "Vencidas", tono: "tarde", items: visibles.filter(tarde).sort(orden) },
      { clave: "hoy", titulo: "Vencen hoy", tono: "hoy", items: visibles.filter((t) => !tarde(t) && t.fecha === hoy) },
      { clave: "pronto", titulo: "Próximas", tono: "normal", items: visibles.filter((t) => !tarde(t) && conFecha(t) && t.fecha > hoy).sort(orden) },
      { clave: "sin", titulo: "Sin fecha", tono: "normal", items: visibles.filter((t) => !tarde(t) && !conFecha(t)) },
    ];
    return g.filter((x) => x.items.length > 0);
  }, [abiertas, quien, hoy]);

  const total = grupos.reduce((n, g) => n + g.items.length, 0);

  return (
    <section aria-labelledby="t-pend" className="pendientes">
      <div className="cab-seccion">
        <h2 id="t-pend">Pendientes <span className="cuenta">{total}</span></h2>
        <label className="filtro">
          <span className="sr">Filtrar por responsable</span>
          <select value={quien} onChange={(e) => setQuien(e.target.value)}>
            <option value="todos">Todos</option>
            {personas.map((p) => <option key={p} value={p}>{p === SIN ? "Sin responsable" : p}</option>)}
          </select>
        </label>
      </div>

      {grupos.length === 0 && <p className="vacio">Nada pendiente para este filtro.</p>}

      {grupos.map((g) => (
        <div key={g.clave} className={`grupo tono-${g.tono}`}>
          <h3 className="etiqueta">{g.titulo}</h3>
          <ul>
            {g.items.map((t) => {
              const fechado = /^\d{4}-\d{2}-\d{2}$/.test(t.fecha);
              return (
                <li key={t.id} className="tarea">
                  <span className="tarea-id">{t.id}</span>
                  <p>{t.descripcion}</p>
                  <p className="tarea-meta">
                    <span className={t.responsable === SIN ? "alerta-texto" : ""}>
                      {t.responsable === SIN ? "sin responsable" : t.responsable}
                    </span>
                    {fechado && (
                      <span>
                        {diaCorto(t.fecha)} {ddmm(t.fecha)} · {relativo(t.fecha, hoy)}
                      </span>
                    )}
                  </p>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </section>
  );
}
