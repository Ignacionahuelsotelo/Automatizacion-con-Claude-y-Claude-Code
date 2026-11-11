import { cancelar, lanzar } from "@/lib/comandos";
import { pedidoDeEscrituraValido } from "@/lib/seguridad";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: Request) {
  if (!pedidoDeEscrituraValido(req)) return Response.json({ error: "Pedido rechazado." }, { status: 403 });
  let cuerpo: unknown;
  try {
    cuerpo = await req.json();
  } catch {
    return Response.json({ error: "JSON inválido." }, { status: 400 });
  }
  const r = await lanzar(cuerpo);
  return r.ok ? Response.json({ job: r.job }, { status: 202 }) : Response.json({ error: r.error }, { status: r.codigo });
}

export async function DELETE(req: Request) {
  if (!pedidoDeEscrituraValido(req)) return Response.json({ error: "Pedido rechazado." }, { status: 403 });
  return Response.json({ cancelado: cancelar() });
}
