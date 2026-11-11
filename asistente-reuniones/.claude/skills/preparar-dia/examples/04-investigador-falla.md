# Caso 04: un investigador falla

**Qué prueba:** si un investigador falla, el error se anota y los demás siguen. El resumen y el log reflejan el fallo sin ocultarlo y sin reintentar en silencio.

## Entrada

Comando: `/preparar-dia`. Hoy es 04/11/2026, son las 08:10. No hay briefs previos.

Calendario del 04/11:

| Hora | Título | Invitados |
|------|--------|-----------|
| 09:00 | Daily de soporte | Camila Torres |
| 11:30 | Revisión de contrato con proveedor B | Pablo Ibáñez, Laura Gómez |
| 16:00 | Planificación de diciembre | Martín Ruiz |

Resultado de los investigadores:

- Daily de soporte: hay 4 tickets sin responsable. Requiere atención.
- Revisión de contrato con proveedor B: **falló** (error de Gmail: tiempo de espera agotado).
- Planificación de diciembre: faltan las fechas de licencias del equipo. Sin alertas.

## Salida esperada

`reuniones/2026-11-04/resumen-dia.md`:

```markdown
# Resumen del día: 04/11/2026

## Agenda
- 09:00 Daily de soporte: hay 4 tickets sin responsable.
- 11:30 Revisión de contrato con proveedor B: no se pudo preparar (error de Gmail: tiempo de espera agotado).
- 16:00 Planificación de diciembre: faltan las fechas de licencias del equipo.

## Las 3 cosas que no me puedo olvidar hoy
1. Asignar responsable a los 4 tickets sin dueño (Daily de soporte).
2. Revisar el brief de "Revisión de contrato con proveedor B" a mano: no se pudo preparar.
3. Cargar las fechas de licencias del equipo (Planificación de diciembre).

## Errores
- Revisión de contrato con proveedor B: error de Gmail, tiempo de espera agotado.
```

`logs/2026-11-04.md`:

```
- 08:10 preparar-dia: 3 reuniones (2 nuevas, 0 con brief existente, 0 ya pasadas) | errores: 1 (Revisión de contrato con proveedor B: error de Gmail, tiempo de espera agotado)
```

Respuesta: el resumen en 15 líneas o menos, con el error visible, y la ruta del archivo.

## Criterios

- [ ] Los 3 investigadores se lanzaron en paralelo; el fallo de uno no frenó a los otros dos.
- [ ] La reunión fallida aparece en la agenda, en su hora, marcada como `no se pudo preparar`, con el motivo.
- [ ] El error está en la sección Errores del resumen y en el log, con el nombre de la reunión.
- [ ] No se inventó contenido del brief que falló.
- [ ] No hubo reintento silencioso: el reintento, si la persona lo quiere, se ofrece al final.
- [ ] La cuenta del log (`2 nuevas`) cuenta solo los briefs que sí se escribieron.
