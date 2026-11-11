# Caso 03: una reunión ya tiene brief

**Qué prueba:** no reinvestigar una reunión con brief previo (y no pisarlo), pero incluirla en el resumen leyendo ese brief.

## Entrada

Comando: `/preparar-dia 2026-11-05`. Hoy es 04/11/2026. La fecha es futura, por lo que la regla de las 12:00 no aplica.

Calendario del 05/11:

| Hora | Título | Invitados |
|------|--------|-----------|
| 10:00 | Kickoff de migración a Meet | Martín Ruiz, Camila Torres |
| 15:00 | Capacitación de soporte | Laura Gómez |

Ya existe `reuniones/2026-11-05/kickoff-de-migracion-a-meet/brief.md`, escrito a mano el 03/11. Su objetivo dice: "Definir el cronograma de migración de Zoom a Meet". Pendiente destacado: "Martín debe traer la lista de salas con licencia de Zoom".

Lo que devuelve el investigador de la capacitación: faltan las diapositivas de la sesión. Requiere atención.

## Salida esperada

`reuniones/2026-11-05/resumen-dia.md`:

```markdown
# Resumen del día: 05/11/2026

## Agenda
- 10:00 Kickoff de migración a Meet: definir el cronograma de migración de Zoom a Meet (brief existente).
- 15:00 Capacitación de soporte: faltan las diapositivas de la sesión.

## Las 3 cosas que no me puedo olvidar hoy
1. Martín debe traer la lista de salas con licencia de Zoom (Kickoff de migración a Meet).
2. Preparar las diapositivas de la capacitación (Capacitación de soporte).

## Errores
- ninguno
```

`logs/2026-11-05.md`:

```
- HH:MM preparar-dia: 2 reuniones (1 nuevas, 1 con brief existente, 0 ya pasadas) | errores: ninguno
```

(`HH:MM` es la hora real de la corrida.)

## Criterios

- [ ] Se lanza un solo investigador, el de la capacitación.
- [ ] El brief del kickoff no se toca: mismo contenido y fecha de modificación.
- [ ] El kickoff aparece en la agenda, marcado como `(brief existente)`.
- [ ] La carpeta y el nombre del archivo usan la fecha pedida (2026-11-05), no la de hoy.
- [ ] El log se escribe en `logs/2026-11-05.md`.
- [ ] La hora de corrida no activa la regla de las 12:00: es una fecha futura.
