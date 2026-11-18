# 01 - Esqueleto

**Estado:** hecha

## Depende de
Nada. Es el primer paso.

## Para qué
Tener la estructura de carpetas y un servidor mínimo andando, para que todo lo demás se apoye en algo que ya funciona.

## Qué tiene que hacer
1. Crear la estructura: `servidor.py`, `index.html`, `datos/` y `.claude/skills/`.
2. Crear `.gitignore` con `datos/` (nada personal se sube a GitHub).
3. `servidor.py` levanta un servidor local con solo la librería estándar de Python (`http.server`), sin `pip install`.
4. Al abrir `http://localhost:8000` se ve una página que dice "Hola Café", servida desde `index.html`.
5. Si `datos/` no existe, el servidor la crea al arrancar.
6. Los textos y comentarios van en español rioplatense.

## Fuera de alcance
Preferencias, indicadores, noticias, Claude, diseño de la página y cualquier endpoint que no sea servir `index.html`.

## Archivos que toca
- `servidor.py` (nuevo)
- `index.html` (nuevo)
- `.gitignore` (nuevo)
- `datos/` (carpeta, ignorada por git)
- `.claude/skills/` (carpeta vacía)

## Criterios de aceptación
- [x] `python3 servidor.py` arranca sin instalar nada.
- [ ] En `http://localhost:8000` se ve "Hola Café". (Comprobado con `curl`: la respuesta trae el HTML con "Hola Café". Falta mirarlo en el navegador.)
- [x] `.gitignore` contiene `datos/` y `git status` no muestra nada de adentro de `datos/`.
- [x] No se importa ninguna librería externa.
- [x] Si se abre una ruta que no existe, el servidor responde 404 sin caerse.

## Cómo probarlo
1. Correr `python3 servidor.py`.
2. Abrir `localhost` en el navegador y ver "Hola Café".
3. Crear un archivo en `datos/` y confirmar con `git status` que no aparece.

## Notas de implementación
- **Archivos creados:** `servidor.py`, `index.html`, `.gitignore` (con la línea `datos/`) y la carpeta `.claude/skills/` (vacía; git no versiona carpetas vacías, así que no aparece en `git status`).
- **Servidor:** `http.server` de la librería estándar, escuchando en `127.0.0.1:8000`. Se usa `127.0.0.1` a propósito para no exponer nada fuera de la máquina; `http://localhost:8000` funciona igual.
- **Rutas:** solo `/` devuelve `index.html` (200). Cualquier otra ruta responde 404 con texto plano. No hay otros endpoints, según el alcance.
- **Rutas de archivo:** `index.html` y `datos/` se calculan a partir de la ubicación de `servidor.py`, así que el servidor anda aunque se lo arranque desde otra carpeta.
- **`datos/`:** el servidor la crea al arrancar con `os.makedirs(..., exist_ok=True)`.
- **Pruebas hechas:** arranque con `python3 servidor.py`; `GET /` devuelve 200 con "Hola Café"; `GET /no-existe` devuelve 404 y el proceso sigue vivo; un archivo de prueba dentro de `datos/` no aparece en `git status` (lo confirma `git check-ignore`). Después se detuvo el servidor.
- **Pendiente:** no se abrió el navegador, así que falta mirar la página visualmente. Ese criterio queda sin tildar hasta hacerlo.
- **Git:** `mi-cafe/` todavía no es un repo propio; está dentro del repo del directorio padre. El `.gitignore` de `mi-cafe/` funciona igual porque git lo aplica en el árbol.
- **Diseño:** la página es intencionalmente mínima (un `<h1>`). El diseño queda para la spec 08.
