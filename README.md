# EnglishTec · Pre-Registro y Consulta de Calificaciones (CLE) — PROTOTIPO CON DATOS SIMULADOS

Flask + SQLite. Todos Los Nombres, Números de Control y Calificaciones Son Inventados.

## Sistema En Línea
Prueba El Sistema Aquí: https://englishtec-cle.onrender.com/

Si Nadie Lo Ha Usado En Unos Minutos, La Primera Carga Puede Tardar Cerca de Un Minuto.

## Cuentas de Demostración
- Coordinación: `coordinacion` / `Coord-2026`
- Docentes: `docente1` a `docente5` / `Docente-2026` (cada docente atiende los grupos A y B de su nivel)
- Datos Iniciales: 10 Grupos Con 10 Alumnos Cada Uno. Publicados: Inglés 1-A, 3-A y 5-A. Capturados Sin Publicar: Inglés 2-B, 3-B y 4-A. Sin Calificaciones: Inglés 1-B, 2-A, 4-B y 5-B
- Alumnos de prueba para la consulta (grupos publicados):
  - Inglés 1-A: Control `20000001`, Código `GQ49-6RAF`
  - Inglés 3-A: Control `20000041`, Código `XW93-WMN7`
  - Inglés 5-A: Control `20000081`, Código `8L8H-EJAV`

## Correr Local
    pip install -r requirements.txt
    python app.py        # http://localhost:5000

## Publicar En Render (gratis)
Sube Esta Carpeta a Un Repositorio de GitHub → Render → New Web Service → Build: `pip install -r requirements.txt` → Start: `gunicorn app:app --workers 1 --threads 8`.
Variables: `FORCE_HTTPS=1`, `SECRET_KEY=<texto largo al azar>`. Nota: en el plan gratuito el disco no es permanente; la base se recrea con los datos simulados (suficiente para la práctica).

## Pruebas Automáticas
    python app.py &   (con DATA_DIR=/tmp/cle_t PORT=5055)
    python -m pytest tests/test_api.py -q
    node tests/ui.js