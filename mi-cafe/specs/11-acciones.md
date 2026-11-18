# 11 - Acciones

**Estado:** hecha (parcialmente reemplazada por las specs 13, 14 y 15; revisada el 18/11/2026)

## Depende de
03-indicadores, 08-pagina-completa

> **PARCIALMENTE REEMPLAZADA (18/11/2026).** La fuente de las acciones ya está aprobada y esta spec quedó obsoleta en ese punto. Son obsoletos los puntos 2, 3 y 6 de "Qué tiene que hacer" (BYMADATA y el "sin dato" permanente), el criterio "sin fuente confiable" como estado fijo y las "Notas de implementación" sobre la fuente. Lo vigente está en `13-acciones-data912.md` (GGAL, YPFD, PAMP), `14-merval-rava.md` (MSCI Merval: Rava y respaldo data912) y `15-acciones-avisos-y-resumen.md`. Siguen vigentes los puntos 1, 4 y 5 (lista de cuatro, nombre "MSCI Merval", mostrarlas solo si el usuario las eligió). Revisión del 18/11/2026: se comprobó con el código actual que los puntos vigentes se cumplen (ver "Notas de implementación").

## Para qué
Sumar el índice MSCI Merval y acciones conocidas como indicadores opcionales, sabiendo que no hay API oficial gratuita estable.

## Qué tiene que hacer
1. Definir la lista de acciones conocidas que se pueden elegir en las preferencias. Punto de partida de la investigación: MSCI Merval (ticker MMSCI) y 3 o 4 líderes, por ejemplo GGAL, YPFD y PAMP (decidido: estas cuatro, sin fuente paga).
2. *(OBSOLETO, reemplazado por 13 y 14.)* Buscar una fuente para cada una; la investigación apunta a BYMADATA (`open.bymadata.com.ar`), pero su API oficial es comercial y las alternativas gratuitas son de terceros o piden clave: no usarlas sin preguntar. Cada valor va con **fecha** y **fuente**, igual que en la spec 03.
3. *(OBSOLETO, reemplazado por 15.)* Si no hay fuente confiable o falla, mostrar "sin dato"; no inventar ni estimar.
4. Usar el nombre vigente **MSCI Merval** (no "S&P Merval").
5. Mostrarlas en la sección de indicadores de la página solo si el usuario las eligió.
6. *(OBSOLETO, la fuente ya está aprobada: 13 y 14.)* Si la fuente exige una dependencia externa o no hay forma gratuita estable, no sumarla: frenar y preguntar.

## Fuera de alcance
Recomendaciones de inversión, gráficos históricos, alertas de precio.

## Archivos que toca
- `servidor.py`
- `index.html`
- `datos/preferencias.json` (se lee, no se versiona)

## Criterios de aceptación
- [x] Las acciones elegidas aparecen con valor, fecha y fuente. (Comprobado el 18/11/2026 con los valores reales de las specs 13 y 14.)
- [ ] ~~Sin fuente confiable, dice "sin dato".~~ REEMPLAZADO por 13, 14 y 15: "sin dato" solo cuando la fuente falla, con aviso en la página. No se verifica acá.
- [x] El índice se llama "MSCI Merval".
- [x] Si el usuario no las eligió, no aparecen.
- [x] No se agregó ninguna dependencia externa sin autorización.

## Cómo probarlo
1. Elegir una acción en las preferencias y comparar su valor con una web de consulta.
2. *(Reemplazado por 14 y 15: romper la fuente y leer el aviso.)* Romper la fuente a propósito y ver "sin dato".
3. Desmarcarla y confirmar que desaparece.

## Notas de implementación

**Revisión del 18/11/2026.** Lo que sigue (de "Qué se hizo" en adelante) es la v1 original; la parte de la fuente, el "sin dato" fijo y las preguntas abiertas quedaron OBSOLETAS (reemplazadas por 13, 14 y 15; sobre la pregunta 2 se decidió mantener el checkbox único "acciones").

### Revisión de los puntos vigentes (1, 4 y 5)
- Punto 1: la lista de cuatro (MSCI Merval, GGAL, YPFD, PAMP) está en `acciones.py`. Las preferencias tienen un único checkbox "acciones" (`INDICADORES` en `preferencias.py`), como decidió el README (decisión sobre preguntas abiertas 6).
- Punto 4: el índice sale como "MSCI Merval" en `/api/indicadores` y no aparece "S&P Merval" en el código.
- Punto 5: `indicadores_con_acciones()` en `servidor.py` las suma solo si "acciones" está en las preferencias; `index.html` las dibuja con la misma función que los demás indicadores (valor, fecha, fuente, marca de desactualizado) y los avisos van a `#avisos-indicadores`. No hizo falta cambiar código.
- Prueba: copia del proyecto en el scratchpad, puerto 8011 (no se tocó el 8000 ni `datos/`). Con "acciones" tildada, `/api/indicadores` trae las cuatro con valor real, fecha y fuente (MSCI Merval 81.794 puntos, Rava, 17/11/2026; GGAL, YPFD y PAMP de data912). Destildada, no aparece ninguna. No se probó en navegador ni el botón "Preparar el de hoy" (queda en la spec 15).

### Qué se hizo
- Lista fija de las cuatro acciones de la decisión 11 de `specs/README.md`: MMSCI (MSCI Merval), GGAL, YPFD y PAMP. Está en `ACCIONES` de `servidor.py`.
- Cada acción sale como indicador con valor `None` (la página lo muestra como "sin dato"), fecha vacía y fuente explícita: "sin fuente gratuita y estable confirmada (BYMADATA no respondió)".
- Las acciones se suman al final de la lista de indicadores solo si "acciones" está en las preferencias (`indicadores_con_acciones`). Se aplica en `/api/indicadores` y en `/api/resumen` POST, para que el bloque que se guarda y el conteo de palabras incluyan las acciones y el botón "Preparar el de hoy" no las borre de la página.
- `index.html` no se tocó: `dibujarIndicador` ya muestra "sin dato" y la fuente cuando el valor es nulo.
- No se agregó ninguna dependencia ni se consultó ninguna fuente de terceros.

### Por qué no hay valor
- `open.bymadata.com.ar` resuelve DNS (101.44.10.20) pero no responde a las conexiones: dos intentos con timeout de 15 y 25 segundos, sin HTTP.
- La investigación (`docs/investigacion.md`) dice que la API oficial de BYMADATA es comercial y que las alternativas gratuitas son de terceros o piden clave. Según la spec, no se usan sin preguntar.
- Por eso todas las acciones dicen "sin dato". No se estimó ni se inventó ningún valor.

### Para decidir (preguntas abiertas)
1. ¿Hay una fuente gratuita y estable que aprobés para MMSCI, GGAL, YPFD y PAMP? Si la hay, habría que sumar su consulta y su copia local en `datos/`.
2. ¿Las acciones se eligen una por una en las preferencias, como dice "Qué tiene que hacer" punto 1, o alcanza con el checkbox "acciones" que ya existe? Lo que hice es el segundo caso, porque `preferencias.py` y `datos/preferencias.json` no están en "Archivos que toca". Elegir una por una implicaría cambiar `preferencias.py` y el formato del archivo.

### Pruebas
- Copia del proyecto en el scratchpad (`/private/tmp/claude-501/-Users-ignaciosotelo-Desktop-Automatizacion-con-Claude-y-Claude-Code-mi-cafe/dc4de262-903c-4346-8b82-e8ae7fc33578/scratchpad/copia-11`), puerto 8001. No se tocó el 8000 ni `datos/` del proyecto.
- `/api/indicadores` con "acciones" elegida: aparecen las cuatro con valor nulo, fecha nula y fuente; el resto de los indicadores no cambia.
- Con "acciones" desmarcada: no aparece ninguna.
- Sintaxis de `servidor.py` verificada.
- No se probó el botón "Preparar el de hoy" de punta a punta (llama a `claude -p`); el cambio ahí es solo sumar la misma lista a lo que se cuenta y se guarda.
- No se pudo comparar con una web de consulta (no hay valor) ni romper una fuente a propósito (ya devuelve "sin dato" siempre).
- Quedó corriendo el servidor de prueba de la copia en el puerto 8001 (PID 2646, cwd en el scratchpad). No lo cerré, como pediste; conviene cerrarlo a mano. El servidor del puerto 8000 (PID 24641) no se tocó; sigue con el código anterior hasta que se reinicie.
