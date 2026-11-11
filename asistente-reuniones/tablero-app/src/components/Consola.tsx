"use client";

import { useEffect, useRef, useState } from "react";
import type { EstadoJob } from "@/lib/tipos";

export type Pedido =
  | { comando: "preparar-dia"; alcance: "hoy" | "semana" | "fecha"; fecha?: string }
  | { comando: "cerrar-reunion"; reunion: string; notas: string };

type Props = {
  abierta: boolean;
  inicial: "preparar-dia" | "cerrar-reunion";
  fechaSugerida: string | null;
  hoy: string;
  job: EstadoJob | null;
  onCerrar: () => void;
  onEnviar: (p: Pedido) => Promise<string | null>;
  onCancelar: () => void;
};

export function Consola({ abierta, inicial, fechaSugerida, hoy, job, onCerrar, onEnviar, onCancelar }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const fin = useRef<HTMLPreElement>(null);
  const [tab, setTab] = useState(inicial);
  const [alcance, setAlcance] = useState<"hoy" | "semana" | "fecha">("hoy");
  const [fecha, setFecha] = useState(fechaSugerida ?? hoy);
  const [reunion, setReunion] = useState("");
  const [notas, setNotas] = useState("");
  const [error, setError] = useState<string | null>(null);
  const corriendo = job?.estado === "corriendo";

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (abierta && !d.open) d.showModal();
    if (!abierta && d.open) d.close();
  }, [abierta]);

  useEffect(() => {
    if (abierta) {
      setTab(inicial);
      setFecha(fechaSugerida ?? hoy);
      setAlcance(fechaSugerida ? "fecha" : "hoy");
    }
  }, [abierta, inicial, fechaSugerida, hoy]);

  useEffect(() => {
    fin.current?.scrollTo({ top: fin.current.scrollHeight });
  }, [job?.lineas.length]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const pedido: Pedido =
      tab === "preparar-dia"
        ? { comando: "preparar-dia", alcance, ...(alcance === "fecha" ? { fecha } : {}) }
        : { comando: "cerrar-reunion", reunion, notas };
    const falla = await onEnviar(pedido);
    if (falla) setError(falla);
  }

  return (
    <dialog ref={ref} className="hoja consola" onClose={onCerrar} aria-label="Comandos del asistente">
      <header className="hoja-cab">
        <div>
          <p className="etiqueta">Asistente</p>
          <h2>Correr un comando</h2>
        </div>
        <button className="btn-texto" onClick={() => ref.current?.close()}>Cerrar</button>
      </header>

      <div className="pestanas" role="tablist">
        {(["preparar-dia", "cerrar-reunion"] as const).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)} disabled={corriendo}>
            /{t}
          </button>
        ))}
      </div>

      <form onSubmit={enviar} className="form">
        {tab === "preparar-dia" ? (
          <fieldset disabled={corriendo}>
            <legend>Qué días preparar</legend>
            <label className="opcion"><input type="radio" name="alc" checked={alcance === "hoy"} onChange={() => setAlcance("hoy")} /> Hoy</label>
            <label className="opcion"><input type="radio" name="alc" checked={alcance === "semana"} onChange={() => setAlcance("semana")} /> Toda la semana</label>
            <label className="opcion">
              <input type="radio" name="alc" checked={alcance === "fecha"} onChange={() => setAlcance("fecha")} /> Un día
              <input type="date" value={fecha} onChange={(e) => { setFecha(e.target.value); setAlcance("fecha"); }} />
            </label>
            <p className="ayuda">Lee el calendario, Gmail y Drive. Solo escribe archivos de este proyecto.</p>
          </fieldset>
        ) : (
          <fieldset disabled={corriendo}>
            <legend>Notas de la reunión</legend>
            <label className="campo">
              Título de la reunión (la confirmás vos)
              <input type="text" value={reunion} maxLength={120} onChange={(e) => setReunion(e.target.value)} placeholder="Ej.: Retro de octubre y plan de noviembre" required />
            </label>
            <label className="campo">
              Notas
              <textarea value={notas} onChange={(e) => setNotas(e.target.value)} rows={8} maxLength={20000} placeholder="Pegá acá las notas o la transcripción." required />
            </label>
            <p className="ayuda">Guarda la minuta y las tareas. El mail queda como borrador: nunca se envía ni se crean eventos.</p>
          </fieldset>
        )}

        {error && <p className="error" role="alert">{error}</p>}
        <div className="acciones">
          <button type="submit" className="btn" disabled={corriendo}>{corriendo ? "Corriendo…" : "Ejecutar"}</button>
          {corriendo && <button type="button" className="btn-texto" onClick={onCancelar}>Cancelar</button>}
        </div>
      </form>

      {job && (
        <section aria-live="polite" className="registro">
          <p className="etiqueta">
            /{job.comando} · {job.detalle} ·{" "}
            <b className={`estado-${job.estado}`}>{job.estado === "corriendo" ? "en curso" : job.estado === "terminado" ? "terminado" : "falló"}</b>
          </p>
          <pre ref={fin}>{job.lineas.length ? job.lineas.join("\n") : "Esperando respuesta…"}</pre>
        </section>
      )}
    </dialog>
  );
}
