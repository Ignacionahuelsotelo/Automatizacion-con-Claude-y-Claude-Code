import { suscribir } from "@/lib/vivo";
import { hostPermitido } from "@/lib/seguridad";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Canal en vivo (SSE): avisa cuando cambian los archivos o avanza un comando.
export async function GET(req: Request) {
  if (!hostPermitido(req)) return new Response("Prohibido", { status: 403 });
  const enc = new TextEncoder();
  let cerrar = () => {};
  const stream = new ReadableStream({
    start(c) {
      const enviar = (txt: string) => {
        try {
          c.enqueue(enc.encode(txt));
        } catch {
          cerrar();
        }
      };
      enviar("retry: 2000\n\n");
      const baja = suscribir((e) => enviar(`data: ${JSON.stringify(e)}\n\n`));
      const latido = setInterval(() => enviar(": latido\n\n"), 20_000);
      cerrar = () => {
        clearInterval(latido);
        baja();
        try {
          c.close();
        } catch {}
      };
      req.signal.addEventListener("abort", cerrar);
    },
    cancel() {
      cerrar();
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-store, no-transform", Connection: "keep-alive" },
  });
}
