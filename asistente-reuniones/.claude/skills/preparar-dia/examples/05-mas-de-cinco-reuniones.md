# Caso 05: más de 5 reuniones, en tandas

**Qué prueba:** el límite de 5 investigadores en paralelo. Con 7 reuniones, se hacen dos tandas (5 y 2), y el resumen conserva el orden cronológico y limita las 3 cosas a 3.

## Entrada

Comando: `/preparar-dia 2026-11-06`. Hoy es 04/11/2026. Fecha futura, la regla de las 12:00 no aplica. No hay briefs previos.

Calendario del 06/11:

| Hora | Título | Invitados |
|------|--------|-----------|
| 08:30 | Daily de soporte | Camila Torres |
| 09:30 | Revisión de tickets | Camila Torres, Martín Ruiz |
| 10:30 | Seguimiento de licencias | Pablo Ibáñez |
| 11:30 | Reunión con Finanzas | Laura Gómez |
| 13:00 | Almuerzo de equipo | Todo el equipo (6 invitados) |
| 15:00 | Comité de compras | Pablo Ibáñez, Martín Ruiz |
| 16:30 | Cierre de semana | Camila Torres |

Los 7 eventos tienen invitados. Ninguno devuelve error. Entre todos, los investigadores marcan 5 puntos que requieren atención:

1. Orden de compra con plazo el 01/12 (Comité de compras).
2. Tarea T-004 vence hoy (Seguimiento de licencias).
3. Finanzas pide el presupuesto firmado (Reunión con Finanzas).
4. Hay 4 tickets sin responsable (Revisión de tickets).
5. Falta confirmar el menú del almuerzo (Almuerzo de equipo).

## Salida esperada

Ejecución:

1. Tanda 1: Daily de soporte, Revisión de tickets, Seguimiento de licencias, Reunión con Finanzas, Almuerzo de equipo (5 en paralelo).
2. Se espera a que termine la tanda 1.
3. Tanda 2: Comité de compras, Cierre de semana (2 en paralelo).

`reuniones/2026-11-06/resumen-dia.md`:

```markdown
# Resumen del día: 06/11/2026

## Agenda
- 08:30 Daily de soporte: sin puntos que requieran atención.
- 09:30 Revisión de tickets: hay 4 tickets sin responsable.
- 10:30 Seguimiento de licencias: la tarea T-004 vence hoy.
- 11:30 Reunión con Finanzas: piden el presupuesto firmado.
- 13:00 Almuerzo de equipo: falta confirmar el menú.
- 15:00 Comité de compras: orden de compra con plazo el 01/12.
- 16:30 Cierre de semana: sin puntos que requieran atención.

## Las 3 cosas que no me puedo olvidar hoy
1. Tarea T-004 vence hoy (Seguimiento de licencias).
2. Presupuesto firmado para Finanzas (Reunión con Finanzas).
3. Asignar responsable a los 4 tickets sin dueño (Revisión de tickets).

## Errores
- ninguno
```

`logs/2026-11-06.md`:

```
- HH:MM preparar-dia: 7 reuniones (7 nuevas, 0 con brief existente, 0 ya pasadas) | errores: ninguno
```

(`HH:MM` es la hora real de la corrida.)

## Criterios

- [ ] Nunca hay más de 5 investigadores corriendo a la vez.
- [ ] La tanda 2 se lanza después de que termina la tanda 1, no antes.
- [ ] La agenda tiene las 7 reuniones, en orden cronológico (no en orden de tanda).
- [ ] Hay exactamente 3 cosas, no 5: se priorizan las que vencen hoy o bloquean a otros, y cada una nombra su fuente. Las otras dos (orden de compra, menú) quedan en la agenda.
- [ ] El archivo y el log se escriben con la fecha pedida (2026-11-06).
