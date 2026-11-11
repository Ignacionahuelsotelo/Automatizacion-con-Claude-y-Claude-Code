"use client";

import { ddmm, diaCorto, diaNumero } from "@/lib/fechas";
import type { Dia } from "@/lib/tipos";
import type { Abierto } from "./Documento";

type Props = {
  fechas: string[];
  dias: Map<string, Dia>;
  hoy: string;
  seleccion: string;
  corriendo: boolean;
  onElegir: (f: string) => void;
  onAbrir: (a: Abierto) => void;
  onPreparar: (f: string) => void;
};

export function Semana({ fechas, dias, hoy, seleccion, corriendo, onElegir, onAbrir, onPreparar }: Props) {
  return (
    <ol className="semana" aria-label="Días de la semana">
      {fechas.map((f) => {
        const dia = dias.get(f);
        const esHoy = f === hoy;
        const activo = f === seleccion;
        return (
          <li key={f} className={`dia${activo ? " activo" : ""}${esHoy ? " es-hoy" : ""}`}>
            <button className="dia-cab" onClick={() => onElegir(f)} aria-pressed={activo}>
              <span className="dia-nombre">{diaCorto(f)}{esHoy && <i className="marca-hoy">hoy</i>}</span>
              <span className="dia-num">{diaNumero(f)}</span>
            </button>

            {!dia ? (
              <div className="dia-vacio">
                <p>Sin preparar</p>
                <button className="enlace" disabled={corriendo} onClick={() => onPreparar(f)}>
                  Preparar {ddmm(f)}
                </button>
              </div>
            ) : dia.agenda.length === 0 ? (
              <p className="dia-vacio">{dia.avisos[0] ?? "Sin reuniones con invitados."}</p>
            ) : (
              <ul className="reuniones">
                {dia.agenda.map((r) => (
                  <li key={r.hora + r.slug}>
                    <span className="hora">{r.hora}</span>
                    <h3>{r.titulo}</h3>
                    {r.resumen && <p>{r.resumen}</p>}
                    {r.nota && <p className="alerta-texto">{r.nota}</p>}
                    <span className="docs">
                      {r.brief && <button className="enlace" onClick={() => onAbrir({ fecha: f, slug: r.slug, titulo: r.titulo, tipo: "brief" })}>brief</button>}
                      {r.minuta && <button className="enlace" onClick={() => onAbrir({ fecha: f, slug: r.slug, titulo: r.titulo, tipo: "minuta" })}>minuta</button>}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        );
      })}
    </ol>
  );
}
