# Caso 02: tarea que ya existe con otra redacción

**Qué prueba:** no duplicar tareas. Una tarea de las notas ya está en `tareas.json` con otra redacción, y hay que reconocerla igual. Además, una tarea nueva con "mañana" y otra sin fecha.

## Entrada

Reunión (calendario): "Comité de compras: renovación de licencias 2027", 04/11/2026 16:00 a 17:00, Sala Andes.
Invitados: Pablo Ibáñez, Martín Ruiz, Laura Gómez.
Asistieron: Pablo, Martín, Laura.
`tareas/tareas.json` antes:

```json
[
  {
    "id": "T-004",
    "descripcion": "Enviar cotización de Microsoft 365 a Compras",
    "responsable": "Pablo Ibáñez",
    "fecha": "2026-11-06",
    "estado": "abierta",
    "reunion": "seguimiento-licencias-octubre"
  }
]
```

Notas:

```text
- Pablo: la cotización de Microsoft 365 la mando a Compras esta semana.
- Pablo: al proveedor C lo llamo mañana, todavía no nos contestó.
- Martín: lo de cambiar Zoom por Meet, ahorro de tres mil dólares al año. ¿cambiamos?
- Laura: eso no lo cerramos hoy, lo vemos en el comité de diciembre.
- Laura: la orden de compra tiene que salir sí o sí el 1 de diciembre.
- Martín: el plazo con Finanzas lo confirmo yo, todavía no sé cuál es.
- Microsoft 365: proveedor A o B, lo decidimos cuando llegue la cotización de C.
```

## Salida esperada

```markdown
# Minuta: Comité de compras: renovación de licencias 2027

## Datos
- Fecha y hora: 04/11/2026 16:00 a 17:00
- Participantes: Pablo Ibáñez, Martín Ruiz, Laura Gómez

## Resumen
- Se revisó la renovación de licencias que vencen en diciembre y enero.
- Falta la cotización del proveedor C para elegir entre A y B en Microsoft 365.
- El cambio de Zoom a Meet queda para el comité de diciembre.

## Decisiones
- Ninguna decisión cerrada en la reunión.

## Tareas
| id | descripción | responsable | fecha límite | estado |
|----|-------------|-------------|--------------|--------|
| T-005 | Llamar al proveedor C para que responda la cotización | Pablo Ibáñez | 05/11 (mañana) | abierta |
| T-006 | Confirmar con Finanzas el plazo de la orden de compra | Martín Ruiz | sin definir | abierta |

Omitida (ya existe): "Enviar cotización de Microsoft 365 a Compras" = T-004.

## Temas abiertos
- Zoom por Meet (ahorro estimado de USD 3.000 por año): se ve en el comité de diciembre.
- Microsoft 365, proveedor A o B: depende de la cotización del proveedor C.
- Orden de compra: plazo 01/12 (dato, no tarea).

## Próxima reunión
- Comité de diciembre, sin fecha.
```

Tareas nuevas para `tareas/tareas.json` (2): T-005 y T-006. T-004 no se toca.

## Criterios

- [ ] "La cotización de Microsoft 365 la mando a Compras esta semana" no se agrega: es la misma tarea que T-004, con otra redacción.
- [ ] La omisión aparece en el resumen de la respuesta, para que la persona la pueda revisar.
- [ ] "Mañana" con reunión el 04/11 da 05/11, escrito como `05/11 (mañana)`.
- [ ] "Confirmo yo" de Martín es una tarea, y el responsable es Martín porque es quien habla y estuvo presente.
- [ ] El cambio de Zoom no es una tarea: la decisión se pospone al comité de diciembre.
- [ ] El comité de diciembre aparece como próxima reunión, sin fecha, en lugar de `sin datos`.
