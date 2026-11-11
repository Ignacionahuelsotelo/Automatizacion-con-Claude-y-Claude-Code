"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ddmm, diaCorto, rangoSemana, semanaHabil } from "@/lib/fechas";
import type { Estado, EstadoJob } from "@/lib/tipos";
import { Consola, type Pedido } from "./Consola";
import { Documento, type Abierto } from "./Documento";
import { Pendientes } from "./Pendientes";
import { Semana } from "./Semana";

const CABECERAS = { "Content-Type": "application/json", "X-Tablero": "1" };

export function Tablero({ inicial, jobInicial }: { inicial: Estado; jobInicial: EstadoJob | null }) {
  const [estado, setEstado] = useState<Estado>(inicial);
  const [job, setJob] = useState<EstadoJob | null>(jobInicial);
  const [enVivo, setEnVivo] = useState(false);
  const [offset, setOffset] = useState(0);
  const [seleccion, setSeleccion] = useState<string | null>(null);
  const [abierto, setAbierto] = useState<Abierto | null>(null);
  const [consola, setConsola] = useState<{ tab: "preparar-dia" | "cerrar-reunion"; fecha: string | null } | null>(null);

  const refrescar = useCallback(async () => {
    try {
      const r = await fetch("/api/estado", { cache: "no-store" });
      if (!r.ok) return;
      const j = (await r.json()) as { estado: Estado; job: EstadoJob | null };
      setEstado(j.estado);
      setJob((actual) => j.job ?? actual);
    } catch {
      /* sin red: se reintenta con el próximo aviso */
    }
  }, []);

  // Canal en vivo: cada cambio en los archivos o en un comando llega acá.
  useEffect(() => {
    const es = new EventSource("/api/eventos");
    es.onopen = () => {
      setEnVivo(true);
      void refrescar();
    };
    es.onerror = () => setEnVivo(false);
    es.onmessage = (m) => {
      try {
        const e = JSON.parse(m.data) as { tipo: "cambio" } | { tipo: "job"; job: EstadoJob | null };
        if (e.tipo === "cambio") void refrescar();
        else setJob(e.job ? { ...e.job } : null);
      } catch {
        /* mensaje ajeno: se ignora */
      }
    };
    return () => es.close();
  }, [refrescar]);

  const fechas = useMemo(() => semanaHabil(estado.hoy, offset), [estado.hoy, offset]);
  const dias = useMemo(() => new Map(estado.dias.map((d) => [d.fecha, d])), [estado.dias]);
  const elegida = seleccion && fechas.includes(seleccion) ? seleccion : fechas.includes(estado.hoy) ? estado.hoy : fechas[0];
  const dia = dias.get(elegida);
  const corriendo = job?.estado === "corriendo";

  async function enviar(p: Pedido): Promise<string | null> {
    try {
      const r = await fetch("/api/comandos", { method: "POST", headers: CABECERAS, body: JSON.stringify(p) });
      const j = await r.json();
      if (!r.ok) return j.error ?? "No se pudo iniciar.";
      setJob(j.job);
      return null;
    } catch {
      return "El tablero está apagado o perdió la conexión. Abrí de nuevo «Abrir tablero.command» y recargá esta página.";
    }
  }

  const cancelar = () => void fetch("/api/comandos", { method: "DELETE", headers: CABECERAS });

  return (
    <div className="pagina">
      <header className="cabecera">
        <div>
          <p className="etiqueta nav-semana">
            Mesa de operaciones
            <button className="flecha" aria-label="Semana anterior" onClick={() => setOffset(offset - 1)}>‹ anterior</button>
            <button className="flecha" aria-label="Semana siguiente" onClick={() => setOffset(offset + 1)}>siguiente ›</button>
          </p>
          <h1>Semana del {rangoSemana(fechas)}</h1>
          {offset !== 0 && <button className="enlace" onClick={() => setOffset(0)}>Volver a esta semana</button>}
        </div>
        <div className="cab-derecha">
          <span className={`vivo ${enVivo ? "on" : ""}`} role="status">
            <i aria-hidden /> {enVivo ? "en vivo" : "sin conexión"}
          </span>
          <button className="btn" disabled={corriendo} onClick={() => setConsola({ tab: "preparar-dia", fecha: null })}>Preparar día</button>
          <button className="btn btn-claro" disabled={corriendo} onClick={() => setConsola({ tab: "cerrar-reunion", fecha: null })}>Cerrar reunión</button>
        </div>
      </header>

      {!enVivo && (
        <p className="banda banda-alerta" role="alert">
          Sin conexión con el tablero. Si lo apagaste, abrí de nuevo «Abrir tablero.command» y recargá la página.
        </p>
      )}

      {corriendo && (
        <button className="banda" onClick={() => setConsola({ tab: job!.comando, fecha: null })}>
          <b>/{job!.comando}</b> en curso · {job!.detalle} — ver avance
        </button>
      )}

      <main className="cuerpo">
        <div className="izquierda">
          <Semana
            fechas={fechas}
            dias={dias}
            hoy={estado.hoy}
            seleccion={elegida}
            corriendo={corriendo}
            onElegir={setSeleccion}
            onAbrir={setAbierto}
            onPreparar={(f) => setConsola({ tab: "preparar-dia", fecha: f })}
          />

          <section className="detalle" aria-labelledby="t-det">
            <h2 id="t-det">
              Para no olvidar <span className="cuenta">{diaCorto(elegida)} {ddmm(elegida)}</span>
            </h2>
            {dia && dia.recordar.length > 0 ? (
              <ol className="recordar">
                {dia.recordar.map((t) => <li key={t}>{t}</li>)}
              </ol>
            ) : (
              <p className="vacio">{dia ? "Nada marcado para este día." : "Este día todavía no se preparó."}</p>
            )}
            {dia?.avisos.map((a) => <p key={a} className="aviso">{a}</p>)}
            {dia && dia.errores.length > 0 && dia.errores.map((e) => <p key={e} className="error">{e}</p>)}
            {dia && dia.log.length > 0 && (
              <details className="log">
                <summary>Registro de corridas ({dia.log.length})</summary>
                <pre>{dia.log.join("\n")}</pre>
              </details>
            )}
          </section>
        </div>

        <aside className="derecha">
          <Pendientes tareas={estado.tareas} hoy={estado.hoy} />
        </aside>
      </main>

      <Documento abierto={abierto} onCerrar={() => setAbierto(null)} />
      <Consola
        abierta={consola !== null}
        inicial={consola?.tab ?? "preparar-dia"}
        fechaSugerida={consola?.fecha ?? null}
        hoy={estado.hoy}
        job={job}
        onCerrar={() => setConsola(null)}
        onEnviar={enviar}
        onCancelar={cancelar}
      />
    </div>
  );
}
