export type Tarea = {
  id: string;
  descripcion: string;
  responsable: string;
  fecha: string; // AAAA-MM-DD o "sin definir"
  estado: string;
  reunion: string;
};

export type Reunion = {
  hora: string;
  titulo: string;
  resumen: string;
  slug: string;
  nota: string | null; // "brief existente", "no se pudo preparar (...)"
  brief: boolean;
  minuta: boolean;
};

export type Dia = {
  fecha: string;
  avisos: string[];
  agenda: Reunion[];
  recordar: string[];
  errores: string[];
  log: string[];
};

export type Estado = {
  hoy: string;
  generado: string;
  tareas: Tarea[];
  dias: Dia[];
};

export type EstadoJob = {
  id: string;
  comando: "preparar-dia" | "cerrar-reunion";
  detalle: string;
  estado: "corriendo" | "terminado" | "fallo";
  inicio: string;
  lineas: string[];
};
