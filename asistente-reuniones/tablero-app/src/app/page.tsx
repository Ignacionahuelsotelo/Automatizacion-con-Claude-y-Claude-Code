import { Tablero } from "@/components/Tablero";
import { jobActual } from "@/lib/comandos";
import { leerEstado } from "@/lib/datos";

export const dynamic = "force-dynamic";

export default async function Pagina() {
  return <Tablero inicial={await leerEstado()} jobInicial={jobActual()} />;
}
