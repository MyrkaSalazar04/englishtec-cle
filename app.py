"""EnglishTec · Sistema de Pre-Registro y Consulta de Calificaciones (CLE, TecNM Campus Matehuala).
Prototipo Funcional Con DATOS SIMULADOS."""
import os, io, re, csv, json, secrets, sqlite3, datetime as dt
from flask import Flask, g, request, session, jsonify, send_file, redirect, render_template, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE, "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.environ.get("DB_PATH", os.path.join(DATA_DIR, "cle.db"))
HASH = "pbkdf2:sha256:100000"
MAX_INTENTOS, BLOQUEO_MIN = 5, 10

def _secret():
    k = os.environ.get("SECRET_KEY")
    if k: return k
    p = os.path.join(DATA_DIR, "secret.key")
    if not os.path.exists(p):
        try: open(p, "w").write(secrets.token_hex(32))
        except OSError: return "dev-" + secrets.token_hex(16)
    return open(p).read().strip()

app = Flask(__name__)
app.secret_key = _secret()
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("FORCE_HTTPS") == "1",
                  MAX_CONTENT_LENGTH=5 * 1024 * 1024)

# ---------------------------------------------------------------- base de datos
SCHEMA = """
CREATE TABLE IF NOT EXISTS grupos(id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, docente TEXT NOT NULL, publicado INTEGER DEFAULT 0, capturado INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS alumnos(id INTEGER PRIMARY KEY, folio TEXT UNIQUE, nombre TEXT, control TEXT UNIQUE, carrera TEXT, semestre INTEGER,
  telefono TEXT, correo TEXT, tipo TEXT, nivel TEXT DEFAULT '', grupo_id INTEGER, pago INTEGER DEFAULT 0, pago_fecha TEXT, codigo_hash TEXT, creado TEXT);
CREATE TABLE IF NOT EXISTS calificaciones(alumno_id INTEGER PRIMARY KEY, u1 REAL, u2 REAL, u3 REAL, u4 REAL);
CREATE TABLE IF NOT EXISTS ajustes(clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS extras(control TEXT PRIMARY KEY, creado TEXT);
CREATE TABLE IF NOT EXISTS avisos(id INTEGER PRIMARY KEY, titulo TEXT, texto TEXT, fecha TEXT);
CREATE TABLE IF NOT EXISTS usuarios(usuario TEXT PRIMARY KEY, clave_hash TEXT, rol TEXT, nombre TEXT);
CREATE TABLE IF NOT EXISTS intentos(clave TEXT PRIMARY KEY, n INTEGER DEFAULT 0, hasta TEXT);
"""
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=30)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def _close(_):
    d = g.pop("db", None)
    if d: d.close()

def now(): return dt.datetime.now().replace(microsecond=0)
def iso(d): return d.isoformat(sep=" ")

def init_db():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    if c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        seed(c)
    cols = [r[1] for r in c.execute("PRAGMA table_info(alumnos)")]
    for col, tipo in [("baja", "INTEGER DEFAULT 0"), ("baja_motivo", "TEXT"), ("baja_fecha", "TEXT")]:
        if col not in cols: c.execute("ALTER TABLE alumnos ADD COLUMN %s %s" % (col, tipo))
    for u, n in [("docente1", "M. Ruiz"), ("docente2", "A. Campos"), ("docente3", "L. Herrera"), ("docente4", "J. Salinas"), ("docente5", "R. Medina")]:
        if not c.execute("SELECT 1 FROM usuarios WHERE usuario=?", (u,)).fetchone():
            c.execute("INSERT INTO usuarios VALUES(?,?,?,?)", (u, generate_password_hash("Docente-2026", HASH), "docente", n))
    for n in range(1, 6):          # un docente por nivel; cada uno atiende sus grupos A y B
        for letra in ("A", "B"):
            nombre, doc = "Inglés %d · Grupo %s" % (n, letra), "docente%d" % n
            if c.execute("SELECT 1 FROM grupos WHERE nombre=?", (nombre,)).fetchone():
                c.execute("UPDATE grupos SET docente=? WHERE nombre=?", (doc, nombre))
            else:
                c.execute("INSERT INTO grupos(nombre,docente,publicado,capturado) VALUES(?,?,0,0)", (nombre, doc))
    c.commit(); c.close()

def seed(c):
    """Datos SIMULADOS (Nombres y Números de Control Inventados)."""
    import random
    for u, p, r, n in [("coordinacion", "Coord-2026", "coordinacion", "Coordinación de Lenguas Extranjeras"),
                       ("docente1", "Docente-2026", "docente", "M. Ruiz"), ("docente2", "Docente-2026", "docente", "A. Campos"),
                       ("docente3", "Docente-2026", "docente", "L. Herrera"), ("docente4", "Docente-2026", "docente", "J. Salinas"),
                       ("docente5", "Docente-2026", "docente", "R. Medina")]:
        c.execute("INSERT INTO usuarios VALUES(?,?,?,?)", (u, generate_password_hash(p, HASH), r, n))
    # 10 grupos (5 niveles x A y B). Estado inicial: 3 publicados, 3 capturados sin publicar y 4 sin calificaciones (para probar desde cero).
    estados = {"Inglés 1 · Grupo A": (1, 1), "Inglés 3 · Grupo A": (1, 1), "Inglés 5 · Grupo A": (1, 1),
               "Inglés 2 · Grupo B": (0, 1), "Inglés 3 · Grupo B": (0, 1), "Inglés 4 · Grupo A": (0, 1)}
    grupos = []
    for niv in range(1, 6):
        for letra in ("A", "B"):
            nom = "Inglés %d · Grupo %s" % (niv, letra); pub, cap = estados.get(nom, (0, 0))
            grupos.append((len(grupos) + 1, nom, "docente%d" % niv, pub, cap, niv))
    c.executemany("INSERT INTO grupos(id,nombre,docente,publicado,capturado) VALUES(?,?,?,?,?)", [g[:5] for g in grupos])
    # 100 alumnos SIMULADOS (nombres inventados, todos con nombre y dos apellidos), 10 por grupo.
    nombres = ["Ana", "Luis", "Sofía", "Marco", "Valeria", "Diego", "Camila", "Emilio", "Renata", "Pablo", "Lucía", "Mateo", "Ximena", "Santiago",
               "Regina", "Leonardo", "Daniela", "Gael", "Paula", "Iker", "Mariana", "Bruno", "Jimena", "Dylan", "Natalia", "Rodrigo", "Alexa", "Hugo",
               "Fernanda", "Tadeo", "Andrea", "Axel", "Ivanna", "Julián", "Abril", "Mauricio", "Elena", "Samuel", "Carla", "Adrián"]
    apellidos = ["Torres", "Díaz", "Pérez", "Ríos", "Mora", "Cruz", "Vega", "Núñez", "Ibarra", "Ortiz", "Salas", "Rangel", "García", "Hernández", "López",
                 "Martínez", "González", "Rodríguez", "Sánchez", "Ramírez", "Flores", "Gómez", "Morales", "Vázquez", "Jiménez", "Reyes", "Ortega", "Castillo",
                 "Mendoza", "Guerrero", "Aguilar", "Medina", "Herrera", "Campos", "Salinas", "Ruiz", "Soto", "Navarro", "Cortés", "Delgado"]
    carreras = ["Sistemas Computacionales", "Industrial", "Gestión Empresarial", "Contador Público", "Civil"]
    def notas_demo(r, k):
        """Aprueba con 70 o más. En cada grupo: la mayoría aprueba todo, uno reprueba 1 unidad, otro 2 unidades y aun así aprueba, y otro reprueba 2 unidades y el general."""
        malas, (bj, bx), (aj, ax) = {3: (2, (25, 50), (70, 82)), 5: (1, (55, 69), (78, 95)), 8: (2, (62, 69), (82, 95))}.get(k, (0, (0, 0), (70, 100)))
        v = [r.randint(aj, ax) for _ in range(4)]
        for p in r.sample(range(4), malas): v[p] = r.randint(bj, bx)
        return v
    rng = random.Random(2026); notas = random.Random(7); alf = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; usados = set(); i = 0
    for gid, gnom, _doc, pub, cap, niv in grupos:
        for k in range(10):
            i += 1
            while True:
                n = "%s %s %s" % (nombres[rng.randrange(40)], apellidos[rng.randrange(40)], apellidos[rng.randrange(40)])
                a1, a2 = n.split()[1:]
                if a1 != a2 and n not in usados: usados.add(n); break
            cod = "".join(rng.choice(alf) for _ in range(8)); cod = cod[:4] + "-" + cod[4:]
            ctl = "2000%04d" % i; pago = 0 if (k == 7 or (k == 2 and gid % 2 == 0)) else 1
            c.execute("INSERT INTO alumnos(folio,nombre,control,carrera,semestre,telefono,correo,tipo,nivel,grupo_id,pago,pago_fecha,codigo_hash,creado) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("CLE-2026-%04d" % (140 + i), n, ctl, carreras[i % 5], 2 + i % 8, "4881%06d" % (i * 7919 % 1000000), ctl + "@ejemplo.mx",
                       "Inscripción" if niv == 1 else "Reinscripción", str(niv), gid, pago, "2026-11-10 10:00:00" if pago else None,
                       generate_password_hash(cod, HASH), "2026-11-09 09:%02d:00" % (i % 60)))
            if cap:
                aid = c.execute("SELECT id FROM alumnos WHERE control=?", (ctl,)).fetchone()[0]
                c.execute("INSERT INTO calificaciones VALUES(?,?,?,?,?)", (aid, *notas_demo(notas, k)))
    for k, v in [("periodo_abierto", "1"), ("examen_fecha", "Sábado 12 de Diciembre · 9:00 a.m."), ("examen_lugar", "Laboratorio de Cómputo (Se Confirma Por Teams)")]:
        c.execute("INSERT INTO ajustes VALUES(?,?)", (k, v))
    c.executemany("INSERT INTO avisos(titulo,texto,fecha) VALUES(?,?,?)",
                  [("Convocatoria Abierta", "Ya Puedes Pre-Registrarte Al Curso De Inglés Escaneando El Código QR O Desde Esta Página.", "2026-11-09"),
                   ("Pago Del Examen de Ubicación", "El Examen Cuesta $500. Se Paga Como Siempre: Banco o Tec, Financieros y Factura En La Coordinación.", "2026-11-09")])

# ---------------------------------------------------------------- utilidades
def ajuste(k, d=""):
    r = db().execute("SELECT valor FROM ajustes WHERE clave=?", (k,)).fetchone()
    return r["valor"] if r else d
def set_ajuste(k, v):
    db().execute("INSERT INTO ajustes VALUES(?,?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", (k, str(v))); db().commit()

def err(msg, code=400, **kw):
    return jsonify(error=msg, **kw), code

def new_code():
    a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    s = "".join(secrets.choice(a) for _ in range(8))
    return s[:4] + "-" + s[4:]

def norm_code(s): return re.sub(r"[^A-Z0-9]", "", (s or "").upper())
def code_key(s):
    n = norm_code(s); return n[:4] + "-" + n[4:]

def bloqueado(clave):
    r = db().execute("SELECT n,hasta FROM intentos WHERE clave=?", (clave,)).fetchone()
    if r and r["hasta"] and dt.datetime.fromisoformat(r["hasta"]) > now(): return True
    return False
def fallo(clave):
    d = db(); r = d.execute("SELECT n FROM intentos WHERE clave=?", (clave,)).fetchone()
    n = (r["n"] if r else 0) + 1
    hasta = iso(now() + dt.timedelta(minutes=BLOQUEO_MIN)) if n >= MAX_INTENTOS else None
    d.execute("INSERT INTO intentos VALUES(?,?,?) ON CONFLICT(clave) DO UPDATE SET n=?,hasta=?", (clave, n, hasta, n, hasta)); d.commit()
    return n
def limpiar(clave):
    db().execute("DELETE FROM intentos WHERE clave=?", (clave,)); db().commit()

def promedio(c):
    v = [c[k] for k in ("u1", "u2", "u3", "u4")]
    return round(sum(v) / 4, 1) if all(x is not None for x in v) else None

def recalcular_grupo(gid):
    """Si un grupo se queda sin alumnos o sin calificaciones, vuelve a 'pendiente' (publicado=0, capturado=0)."""
    if not gid: return
    d = db()
    n = d.execute("SELECT COUNT(*) FROM alumnos WHERE grupo_id=? AND baja=0", (gid,)).fetchone()[0]
    con = d.execute("SELECT COUNT(*) FROM alumnos a JOIN calificaciones c ON c.alumno_id=a.id WHERE a.grupo_id=? AND a.baja=0", (gid,)).fetchone()[0]
    if n == 0 or con == 0:
        d.execute("UPDATE grupos SET publicado=0, capturado=0 WHERE id=?", (gid,)); d.commit()

# ---------------------------------------------------------------- seguridad
@app.before_request
def _https():
    if os.environ.get("FORCE_HTTPS") == "1" and request.scheme != "https":
        return redirect(request.url.replace("http://", "https://", 1), 301)

@app.before_request
def _csrf():
    if request.method in ("POST", "PUT", "DELETE") and request.path.startswith("/api/") and request.path != "/api/csrf":
        if not session.get("csrf") or request.headers.get("X-CSRF-Token") != session["csrf"]:
            return err("Tu Sesión Expiró. Recarga La Página E Inténtalo De Nuevo.", 403)

@app.after_request
def _headers(r):
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "same-origin"
    if request.path.startswith("/api/"): r.headers["Cache-Control"] = "no-store"
    return r

def need(rol):
    if session.get("rol") != rol: abort(401)
@app.errorhandler(401)
def _401(_): return err("Necesitas Iniciar Sesión Con Tu Usuario.", 401)
@app.errorhandler(413)
def _413(_): return err("El Archivo Es Demasiado Grande (Máximo 5 MB).", 413)

@app.get("/api/csrf")
def csrf():
    session.permanent = False
    if not session.get("csrf"): session["csrf"] = secrets.token_hex(16)
    return jsonify(token=session["csrf"], rol=session.get("rol"), nombre=session.get("nombre"))

@app.get("/")
def index(): return render_template("index.html")

# ---------------------------------------------------------------- público
@app.get("/api/publico")
def publico():
    return jsonify(periodo_abierto=ajuste("periodo_abierto") == "1", examen_fecha=ajuste("examen_fecha"), examen_lugar=ajuste("examen_lugar"), monto=500,
                   avisos=[dict(r) for r in db().execute("SELECT id,titulo,texto,fecha FROM avisos ORDER BY id DESC")])

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
@app.post("/api/preregistro")
def preregistro():
    j = request.get_json(silent=True) or {}
    v = lambda k: str(j.get(k, "")).strip()
    nombre, control, carrera, tel, correo, tipo = v("nombre"), v("control"), v("carrera"), re.sub(r"[\s\-()]", "", v("telefono")), v("correo"), v("tipo")
    if len(nombre) < 5: return err("Escribe Tu Nombre Completo.", campo="nombre")
    if not re.fullmatch(r"\d{6,10}", control): return err("El Número De Control Debe Tener Solo Números (6 A 10 Dígitos).", campo="control")
    if len(carrera) < 2: return err("Escribe Tu Carrera.", campo="carrera")
    try: sem = int(v("semestre")); assert 1 <= sem <= 15
    except Exception: return err("El Semestre Debe Ser Un Número Del 1 Al 15.", campo="semestre")
    if not re.fullmatch(r"\d{10}", tel): return err("El Teléfono Debe Tener 10 Dígitos.", campo="telefono")
    if not EMAIL.match(correo): return err("Escribe Un Correo Válido, Por Ejemplo nombre@correo.com.", campo="correo")
    if tipo not in ("Inscripción", "Reinscripción"): return err("Elige Si Es Inscripción O Reinscripción.", campo="tipo")
    d = db()
    ex = d.execute("SELECT folio,baja FROM alumnos WHERE control=?", (control,)).fetchone()
    if ex and ex["baja"]: return err("Este Número De Control Tiene Un Registro Dado De Baja. Pide A La Coordinación Que Lo Reactive.", 409, campo="control")
    if ex: return err("Este Número de Control Ya Está Pre-Registrado. Tu Folio Es %s." % ex["folio"], 409, campo="control", folio=ex["folio"])
    extra = d.execute("SELECT 1 FROM extras WHERE control=?", (control,)).fetchone()
    if ajuste("periodo_abierto") != "1" and not extra:
        return err("El Periodo De Pre-Registro Está Cerrado. Pide A La Coordinación Una Fecha Extra.", 403)
    code = new_code()
    try:
        d.execute("BEGIN IMMEDIATE")
        n = d.execute("SELECT COALESCE(MAX(id),0)+1 FROM alumnos").fetchone()[0]
        folio = "CLE-2026-%04d" % (140 + n)
        d.execute("INSERT INTO alumnos(folio,nombre,control,carrera,semestre,telefono,correo,tipo,codigo_hash,creado) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (folio, nombre, control, carrera, sem, tel, correo, tipo, generate_password_hash(code, HASH), iso(now())))
        d.execute("DELETE FROM extras WHERE control=?", (control,))
        d.commit()
    except sqlite3.IntegrityError:
        d.rollback(); return err("Este Número De Control Ya Está Pre-Registrado.", 409, campo="control")
    return jsonify(folio=folio, codigo=code), 201

@app.post("/api/consulta")
def consulta():
    j = request.get_json(silent=True) or {}
    control, codigo = str(j.get("control", "")).strip(), str(j.get("codigo", ""))
    clave = "al:" + control
    if bloqueado(clave): return err("Demasiados Intentos. El Acceso Quedó Bloqueado %d Minutos; Pide Ayuda en La Coordinación." % BLOQUEO_MIN, 429)
    a = db().execute("SELECT * FROM alumnos WHERE control=?", (control,)).fetchone()
    if not a or not check_password_hash(a["codigo_hash"], code_key(codigo)):
        n = fallo(clave); q = MAX_INTENTOS - n
        if q <= 0: return err("Demasiados Intentos. El Acceso Quedó Bloqueado %d Minutos; Pide Ayuda En La Coordinación." % BLOQUEO_MIN, 429)
        return err("Número de Control O Código Incorrecto. Te Quedan %d Intento%s. Revisa Mayúsculas y Guiones." % (q, "" if q == 1 else "s"), 401, intentos=q)
    limpiar(clave)
    if a["baja"]: return err("Tu Registro Está Dado De Baja. Si Quieres Retomar El Curso, Acércate A La Coordinación.", 403)
    out = dict(nombre=a["nombre"], folio=a["folio"], tipo=a["tipo"], nivel=a["nivel"], pago=bool(a["pago"]), pago_fecha=a["pago_fecha"],
               examen_fecha=ajuste("examen_fecha"), examen_lugar=ajuste("examen_lugar"), grupo=None, calificaciones=None, general=None, publicado=False)
    if a["grupo_id"]:
        gr = db().execute("SELECT * FROM grupos WHERE id=?", (a["grupo_id"],)).fetchone()
        out["grupo"] = gr["nombre"]; out["publicado"] = bool(gr["publicado"])
        c = db().execute("SELECT * FROM calificaciones WHERE alumno_id=?", (a["id"],)).fetchone()
        if gr["publicado"] and c:
            out["calificaciones"] = [c["u1"], c["u2"], c["u3"], c["u4"]]; out["general"] = promedio(c)
            out["aprobado"] = all(c[k] is not None for k in ("u1", "u2", "u3", "u4")) and sum(c[k] for k in ("u1", "u2", "u3", "u4")) / 4 >= 70
    return jsonify(out)

# ---------------------------------------------------------------- sesión del personal
@app.post("/api/login")
def login():
    j = request.get_json(silent=True) or {}
    u, p = str(j.get("usuario", "")).strip().lower(), str(j.get("clave", ""))
    clave = "st:" + u
    if bloqueado(clave): return err("Demasiados Intentos. Espera %d Minutos." % BLOQUEO_MIN, 429)
    r = db().execute("SELECT * FROM usuarios WHERE usuario=?", (u,)).fetchone()
    if not r or not check_password_hash(r["clave_hash"], p):
        fallo(clave); return err("Usuario O Contraseña Incorrectos.", 401)
    limpiar(clave)
    csrf_tok = session.get("csrf") or secrets.token_hex(16)
    session.clear(); session.update(rol=r["rol"], usuario=r["usuario"], nombre=r["nombre"], csrf=csrf_tok)
    return jsonify(rol=r["rol"], nombre=r["nombre"])

@app.post("/api/logout")
def logout():
    tok = session.get("csrf"); session.clear(); session["csrf"] = tok
    return jsonify(ok=True)

# ---------------------------------------------------------------- Coordinación
def lista_alumnos(q="", estado=""):
    sql = "SELECT a.*, g.nombre AS grupo FROM alumnos a LEFT JOIN grupos g ON g.id=a.grupo_id WHERE a.baja=%d" % (1 if estado == "baja" else 0); args = []
    if q: sql += " AND (lower(a.nombre) LIKE ? OR a.control LIKE ? OR lower(a.folio) LIKE ?)"; args += ["%" + q.lower() + "%"] * 3
    if estado == "pendiente": sql += " AND a.pago=0"
    if estado == "recibido": sql += " AND a.pago=1"
    return db().execute(sql + " ORDER BY a.id", args).fetchall()

@app.get("/api/coord/alumnos")
def c_alumnos():
    need("coordinacion")
    rows = lista_alumnos(request.args.get("q", "").strip(), request.args.get("estado", ""))
    tot = db().execute("SELECT COUNT(*) t, COALESCE(SUM(pago),0) p FROM alumnos WHERE baja=0").fetchone()
    nb = db().execute("SELECT COUNT(*) FROM alumnos WHERE baja=1").fetchone()[0]
    return jsonify(alumnos=[dict(id=r["id"], folio=r["folio"], nombre=r["nombre"], control=r["control"], tipo=r["tipo"], nivel=r["nivel"], grupo_id=r["grupo_id"],
                                 pago=bool(r["pago"]), pago_fecha=r["pago_fecha"], carrera=r["carrera"], semestre=r["semestre"], telefono=r["telefono"], correo=r["correo"],
                                 baja=bool(r["baja"]), baja_motivo=r["baja_motivo"], baja_fecha=r["baja_fecha"]) for r in rows], total=tot["t"], recibidos=tot["p"], pendientes=tot["t"] - tot["p"], bajas=nb,
                   grupos=[dict(id=x["id"], nombre=x["nombre"]) for x in db().execute("SELECT id,nombre FROM grupos ORDER BY nombre")])

def get_alumno(i):
    a = db().execute("SELECT * FROM alumnos WHERE id=?", (i,)).fetchone()
    if not a: abort(404)
    return a

@app.post("/api/coord/alumnos/<int:i>/pago")
def c_pago(i):
    need("coordinacion"); a = get_alumno(i)
    db().execute("UPDATE alumnos SET pago=1,pago_fecha=? WHERE id=?", (iso(now()), i)); db().commit()
    return jsonify(ok=True)

@app.post("/api/coord/alumnos/<int:i>/nivel")
def c_nivel(i):
    need("coordinacion"); get_alumno(i)
    n = str((request.get_json(silent=True) or {}).get("nivel", "")).strip()
    if n not in ("", "1", "2", "3", "4", "5"): return err("El Nivel Debe Ser del 1 Al 5.")
    db().execute("UPDATE alumnos SET nivel=? WHERE id=?", (n, i)); db().commit(); return jsonify(ok=True)

@app.post("/api/coord/alumnos/<int:i>/grupo")
def c_grupo(i):
    need("coordinacion"); a = get_alumno(i)
    gid = (request.get_json(silent=True) or {}).get("grupo_id") or None
    if gid is not None and not db().execute("SELECT 1 FROM grupos WHERE id=?", (gid,)).fetchone(): return err("Ese grupo no existe.")
    db().execute("UPDATE alumnos SET grupo_id=? WHERE id=?", (gid, i)); db().commit()
    recalcular_grupo(a["grupo_id"]); recalcular_grupo(gid); return jsonify(ok=True)

@app.post("/api/coord/alumnos/<int:i>/reset-codigo")
def c_reset(i):
    need("coordinacion"); get_alumno(i); code = new_code()
    db().execute("UPDATE alumnos SET codigo_hash=? WHERE id=?", (generate_password_hash(code, HASH), i)); db().commit()
    a = get_alumno(i); limpiar("al:" + a["control"])
    return jsonify(codigo=code, nombre=a["nombre"])

@app.post("/api/coord/alumnos/<int:i>/editar")
def c_editar(i):
    need("coordinacion"); get_alumno(i)
    j = request.get_json(silent=True) or {}; v = lambda k: str(j.get(k, "")).strip()
    nombre, control, carrera, tel, correo, tipo = v("nombre"), v("control"), v("carrera"), re.sub(r"[\s\-()]", "", v("telefono")), v("correo"), v("tipo")
    if len(nombre) < 5: return err("Escribe El Nombre Completo.", campo="nombre")
    if not re.fullmatch(r"\d{6,10}", control): return err("El Número de Control Debe Tener Solo Números (6 A 10 Dígitos).", campo="control")
    if len(carrera) < 2: return err("Escribe La Carrera.", campo="carrera")
    try: sem = int(v("semestre")); assert 1 <= sem <= 15
    except Exception: return err("El Semestre Debe Ser Un Número del 1 Al 15.", campo="semestre")
    if not re.fullmatch(r"\d{10}", tel): return err("El Teléfono Debe Tener 10 Dígitos.", campo="telefono")
    if not EMAIL.match(correo): return err("Escribe Un Correo Válido.", campo="correo")
    if tipo not in ("Inscripción", "Reinscripción"): return err("Elige Inscripción o Reinscripción.", campo="tipo")
    d = db(); a = get_alumno(i); pago = 1 if j.get("pago") else 0
    try:
        d.execute("UPDATE alumnos SET nombre=?,control=?,carrera=?,semestre=?,telefono=?,correo=?,tipo=?,pago=?,pago_fecha=? WHERE id=?",
                  (nombre, control, carrera, sem, tel, correo, tipo, pago, (a["pago_fecha"] or iso(now())) if pago else None, i)); d.commit()
    except sqlite3.IntegrityError:
        d.rollback(); return err("Ese Número de Control Ya Pertenece A Otro Alumno.", 409, campo="control")
    if control != a["control"]: limpiar("al:" + a["control"])
    return jsonify(ok=True)

@app.post("/api/coord/alumnos/<int:i>/baja")
def c_baja(i):
    need("coordinacion"); a = get_alumno(i)
    m = str((request.get_json(silent=True) or {}).get("motivo", "")).strip()[:200]
    if not m: return err("Elige O Escribe El Motivo De La Baja.")
    db().execute("UPDATE alumnos SET baja=1,baja_motivo=?,baja_fecha=?,grupo_id=NULL WHERE id=?", (m, iso(now()), i))
    db().execute("DELETE FROM calificaciones WHERE alumno_id=?", (i,)); db().commit()
    recalcular_grupo(a["grupo_id"])
    return jsonify(ok=True)

@app.post("/api/coord/alumnos/<int:i>/reactivar")
def c_reactivar(i):
    need("coordinacion"); get_alumno(i)
    db().execute("UPDATE alumnos SET baja=0,baja_motivo=NULL,baja_fecha=NULL WHERE id=?", (i,)); db().commit()
    return jsonify(ok=True)

@app.route("/api/coord/alumnos/<int:i>", methods=["DELETE"])
def c_eliminar(i):
    need("coordinacion"); a = get_alumno(i)
    if not a["baja"]: return err("Primero Da De Baja Al Alumno; Solo Se Puede Eliminar Un Registro Que Ya Está Dado De Baja.")
    d = db(); d.execute("DELETE FROM calificaciones WHERE alumno_id=?", (i,)); d.execute("DELETE FROM alumnos WHERE id=?", (i,)); d.commit()
    limpiar("al:" + a["control"]); return jsonify(ok=True)

@app.get("/api/coord/export.xlsx")
def c_export():
    need("coordinacion")
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = Workbook(); ws = wb.active; ws.title = "Pre-Registros"
    cols = ["Folio", "Nombre", "Número de control", "Carrera", "Semestre", "Teléfono", "Correo", "Tipo", "Nivel", "Grupo", "Pago Recibido", "Fecha de Pago", "Fecha de Registro"]
    ws.append(cols)
    for r in lista_alumnos(request.args.get("q", "").strip(), request.args.get("estado", "")):
        gname = db().execute("SELECT nombre FROM grupos WHERE id=?", (r["grupo_id"],)).fetchone()
        ws.append([r["folio"], r["nombre"], r["control"], r["carrera"], r["semestre"], r["telefono"], r["correo"], r["tipo"], r["nivel"] or "Por asignar",
                   gname["nombre"] if gname else "Sin grupo", "Sí" if r["pago"] else "No", r["pago_fecha"] or "", r["creado"]])
    for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="14285A"); c.alignment = Alignment(horizontal="center")
    for i, w in enumerate([16, 28, 18, 24, 10, 14, 28, 14, 12, 20, 14, 20, 20], 1): ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    b = io.BytesIO(); wb.save(b); b.seek(0)
    return send_file(b, as_attachment=True, download_name="preregistros_CLE.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/api/coord/ajustes")
def c_ajustes():
    need("coordinacion")
    return jsonify(periodo_abierto=ajuste("periodo_abierto") == "1", examen_fecha=ajuste("examen_fecha"), examen_lugar=ajuste("examen_lugar"),
                   extras=[r["control"] for r in db().execute("SELECT control FROM extras ORDER BY creado")])
@app.post("/api/coord/periodo")
def c_periodo():
    need("coordinacion"); set_ajuste("periodo_abierto", "1" if (request.get_json(silent=True) or {}).get("abierto") else "0"); return jsonify(ok=True)
@app.post("/api/coord/examen")
def c_examen():
    need("coordinacion"); j = request.get_json(silent=True) or {}
    set_ajuste("examen_fecha", str(j.get("fecha", "")).strip()[:120]); set_ajuste("examen_lugar", str(j.get("lugar", "")).strip()[:160]); return jsonify(ok=True)
@app.post("/api/coord/extras")
def c_extra_add():
    need("coordinacion"); c = str((request.get_json(silent=True) or {}).get("control", "")).strip()
    if not re.fullmatch(r"\d{6,10}", c): return err("El Número De Control Debe Tener Solo Números (6 A 10 Dígitos).")
    if db().execute("SELECT 1 FROM alumnos WHERE control=?", (c,)).fetchone(): return err("Ese número de control ya está pre-registrado.")
    db().execute("INSERT OR REPLACE INTO extras VALUES(?,?)", (c, iso(now()))); db().commit(); return jsonify(ok=True)
@app.route("/api/coord/extras/<c>", methods=["DELETE"])
def c_extra_del(c):
    need("coordinacion"); db().execute("DELETE FROM extras WHERE control=?", (c,)); db().commit(); return jsonify(ok=True)
@app.post("/api/coord/avisos")
def c_aviso_add():
    need("coordinacion"); j = request.get_json(silent=True) or {}; t, x = str(j.get("titulo", "")).strip(), str(j.get("texto", "")).strip()
    if len(t) < 3 or len(x) < 3: return err("Escribe El Título y El Texto Del Aviso.")
    db().execute("INSERT INTO avisos(titulo,texto,fecha) VALUES(?,?,?)", (t[:100], x[:500], dt.date.today().isoformat())); db().commit(); return jsonify(ok=True)
@app.route("/api/coord/avisos/<int:i>", methods=["DELETE"])
def c_aviso_del(i):
    need("coordinacion"); db().execute("DELETE FROM avisos WHERE id=?", (i,)); db().commit(); return jsonify(ok=True)

@app.get("/api/coord/qr.png")
def c_qr():
    need("coordinacion"); import qrcode
    url = request.url_root.rstrip("/") + "/#/preregistro"
    img = qrcode.make(url, box_size=10, border=2); b = io.BytesIO(); img.save(b, "PNG"); b.seek(0)
    r = send_file(b, mimetype="image/png", as_attachment=request.args.get("d") == "1", download_name="QR_preregistro_CLE.png"); r.headers["X-Link"] = url; return r
@app.get("/api/coord/link")
def c_link():
    need("coordinacion"); return jsonify(url=request.url_root.rstrip("/") + "/#/preregistro")

@app.get("/api/coord/grupos")
def c_grupos():
    need("coordinacion"); out = []
    for gr in db().execute("SELECT * FROM grupos ORDER BY nombre"):
        n = db().execute("SELECT COUNT(*) FROM alumnos WHERE grupo_id=?", (gr["id"],)).fetchone()[0]
        out.append(dict(id=gr["id"], nombre=gr["nombre"], docente=db().execute("SELECT nombre FROM usuarios WHERE usuario=?", (gr["docente"],)).fetchone()["nombre"],
                        alumnos=n, estado="publicado" if gr["publicado"] else ("capturado" if gr["capturado"] else "pendiente")))
    return jsonify(grupos=out)

@app.get("/api/coord/grupo/<int:gid>/pdf")
def c_pdf(gid):
    need("coordinacion")
    gr = db().execute("SELECT * FROM grupos WHERE id=?", (gid,)).fetchone() or abort(404)
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    ss = getSampleStyleSheet(); NAVY = colors.HexColor("#14285A")
    h = ParagraphStyle("h", parent=ss["Title"], textColor=NAVY, fontName="Times-Bold", fontSize=20)
    b = io.BytesIO(); doc = SimpleDocTemplate(b, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=48, bottomMargin=40, title="Calificaciones " + gr["nombre"])
    doc_n = db().execute("SELECT nombre FROM usuarios WHERE usuario=?", (gr["docente"],)).fetchone()["nombre"]
    estado = "Publicado" if gr["publicado"] else ("Borrador" if gr["capturado"] else "Pendiente")
    data = [["N.º control", "Nombre", "U1", "U2", "U3", "U4", "General"]]
    for a in db().execute("SELECT * FROM alumnos WHERE grupo_id=? ORDER BY nombre", (gid,)):
        c = db().execute("SELECT * FROM calificaciones WHERE alumno_id=?", (a["id"],)).fetchone()
        f = lambda x: "" if x is None else ("%g" % x)
        data.append([a["control"], a["nombre"], f(c["u1"]) if c else "", f(c["u2"]) if c else "", f(c["u3"]) if c else "", f(c["u4"]) if c else "", f(promedio(c)) if c and promedio(c) is not None else ""])
    t = Table(data, colWidths=[80, 190, 40, 40, 40, 40, 60], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EEF2FB"), colors.white]), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#9AA5B8")),
                           ("ALIGN", (2, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, -1), 10)]))
    doc.build([Paragraph("EnglishTec · Coordinación de Lenguas Extranjeras", ss["Normal"]), Paragraph("Calificaciones · " + gr["nombre"], h),
               Paragraph("Docente: %s · Estado: %s · Generado El %s · Datos Simulados" % (doc_n, estado, now().strftime("%d/%m/%Y %H:%M")), ss["Normal"]), Spacer(1, 12), t])
    b.seek(0); return send_file(b, mimetype="application/pdf", as_attachment=True, download_name="calificaciones_%s.pdf" % re.sub(r"\W+", "_", gr["nombre"]))

@app.get("/api/coord/respaldo")
def c_backup():
    need("coordinacion"); d = db(); out = {"generado": iso(now())}
    for t in ["grupos", "alumnos", "calificaciones", "ajustes", "extras", "avisos"]:
        out[t] = [dict(r) for r in d.execute("SELECT * FROM " + t)]
    b = io.BytesIO(json.dumps(out, ensure_ascii=False, indent=1).encode()); b.seek(0)
    return send_file(b, mimetype="application/json", as_attachment=True, download_name="respaldo_CLE_%s.json" % dt.date.today().isoformat())

# ---------------------------------------------------------------- Docente
def mi_grupo(gid):
    need("docente")
    gr = db().execute("SELECT * FROM grupos WHERE id=? AND docente=?", (gid, session["usuario"])).fetchone()
    if not gr: abort(403)
    return gr
@app.errorhandler(403)
def _403(_): return err("No Tienes Permiso Para Esta Acción.", 403)

@app.get("/api/docente/grupos")
def d_grupos():
    need("docente")
    rows = db().execute("SELECT * FROM grupos WHERE docente=? ORDER BY nombre", (session["usuario"],)).fetchall()
    return jsonify(grupos=[dict(id=r["id"], nombre=r["nombre"], estado="publicado" if r["publicado"] else ("capturado" if r["capturado"] else "pendiente")) for r in rows])

@app.get("/api/docente/grupo/<int:gid>")
def d_grupo(gid):
    gr = mi_grupo(gid); out = []
    for a in db().execute("SELECT * FROM alumnos WHERE grupo_id=? ORDER BY nombre", (gid,)):
        c = db().execute("SELECT * FROM calificaciones WHERE alumno_id=?", (a["id"],)).fetchone()
        out.append(dict(control=a["control"], nombre=a["nombre"], u=[c[k] for k in ("u1", "u2", "u3", "u4")] if c else [None] * 4, general=promedio(c) if c else None))
    return jsonify(nombre=gr["nombre"], publicado=bool(gr["publicado"]), capturado=bool(gr["capturado"]), alumnos=out)

def validar_nota(x):
    if x is None or str(x).strip() == "": return None, "Falta Una Calificación"
    try: v = float(str(x).replace(",", "."))
    except ValueError: return None, "«%s» No Es Un Número" % x
    if not 0 <= v <= 100: return None, "La Calificación %g Debe Estar Entre 0 y 100" % v
    return round(v, 1), None

def guardar_filas(gid, filas, borrar=False):
    d = db(); ok, errores = 0, []
    ctrl = {r["control"]: r["id"] for r in d.execute("SELECT id,control FROM alumnos WHERE grupo_id=?", (gid,))}
    pub = d.execute("SELECT publicado FROM grupos WHERE id=?", (gid,)).fetchone()[0]
    for n, f in filas:
        c = str(f.get("control", "")).strip()
        if c not in ctrl: errores.append(dict(fila=n, motivo="El Número de Control %s No Pertenece A Este Grupo" % (c or "(vacío)"))); continue
        if borrar and all(x is None or str(x).strip() == "" for x in f["u"]):      # las 4 casillas vacías = borrar captura (solo captura manual)
            if pub: errores.append(dict(fila=n, motivo="No Se Pueden Borrar Las Calificaciones De Un Grupo Ya Publicado")); continue
            d.execute("DELETE FROM calificaciones WHERE alumno_id=?", (ctrl[c],)); ok += 1; continue
        vals, bad = [], None
        for i, x in enumerate(f["u"], 1):
            v, e = validar_nota(x)
            if e: bad = "Unidad %d: %s" % (i, e); break
            vals.append(v)
        if bad: errores.append(dict(fila=n, motivo=bad)); continue
        d.execute("INSERT INTO calificaciones VALUES(?,?,?,?,?) ON CONFLICT(alumno_id) DO UPDATE SET u1=excluded.u1,u2=excluded.u2,u3=excluded.u3,u4=excluded.u4", (ctrl[c], *vals)); ok += 1
    if ok: d.execute("UPDATE grupos SET capturado=1 WHERE id=?", (gid,))
    d.commit(); recalcular_grupo(gid); return ok, errores

@app.post("/api/docente/grupo/<int:gid>/guardar")
def d_guardar(gid):
    mi_grupo(gid); filas = (request.get_json(silent=True) or {}).get("filas", [])
    ok, errores = guardar_filas(gid, [(i + 1, f) for i, f in enumerate(filas)], True)
    return jsonify(correctas=ok, errores=errores)

def leer_tabla(file):
    name = (file.filename or "").lower(); raw = file.read()
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook
        try: ws = load_workbook(io.BytesIO(raw), data_only=True).active
        except Exception: raise ValueError("No Pude Abrir El Archivo. Guárdalo Como Excel (.xlsx) y vuelve a intentarlo.")
        return [list(r) for r in ws.iter_rows(values_only=True)]
    if name.endswith(".csv"):
        txt = raw.decode("utf-8-sig", "ignore"); dele = ";" if txt.count(";") > txt.count(",") else ","
        return [r for r in csv.reader(io.StringIO(txt), delimiter=dele)]
    raise ValueError("El Archivo Debe Ser de Excel (.xlsx) o CSV.")

@app.post("/api/docente/grupo/<int:gid>/importar")
def d_importar(gid):
    mi_grupo(gid); f = request.files.get("archivo")
    if not f: return err("Elige Primero Tu Archivo de Excel.")
    try: tabla = leer_tabla(f)
    except ValueError as e: return err(str(e))
    hi = next((i for i, r in enumerate(tabla) if any(re.search(r"control", str(c or ""), re.I) for c in r)), None)
    if hi is None: return err("No Encontré La Columna del Número de Control. Revisa Que Tu Excel Tenga Una Columna Llamada «Número de Control».")
    head = [str(c or "") for c in tabla[hi]]
    cc = next(i for i, c in enumerate(head) if re.search(r"control", c, re.I))
    cols = {}
    for i, c in enumerate(head):
        m = re.search(r"(?:unidad|tema|u|parcial)\s*\.?\s*([1-4])\b", c.strip(), re.I)
        if m and int(m.group(1)) not in cols: cols[int(m.group(1))] = i
    if len(cols) < 4: return err("No Encontré Las 4 Columnas de Unidades. Cada Una Debe Llamarse, Por Ejemplo, «Unidad 1», «Unidad 2», «Unidad 3» y «Unidad 4».")
    filas = []
    for k, r in enumerate(tabla[hi + 1:], hi + 2):
        if not any(str(x or "").strip() for x in r): continue
        ctl = str(r[cc] if cc < len(r) else "").strip()
        if ctl.endswith(".0"): ctl = ctl[:-2]
        filas.append((k, dict(control=ctl, u=[r[cols[i]] if cols[i] < len(r) else None for i in (1, 2, 3, 4)])))
    if not filas: return err("El Archivo No Tiene Filas Con Alumnos.")
    ok, errores = guardar_filas(gid, filas)
    return jsonify(correctas=ok, errores=errores)

@app.post("/api/docente/grupo/<int:gid>/publicar")
def d_publicar(gid):
    gr = mi_grupo(gid)
    n = db().execute("SELECT COUNT(*) FROM alumnos a JOIN calificaciones c ON c.alumno_id=a.id WHERE a.grupo_id=?", (gid,)).fetchone()[0]
    if n == 0: return err("Primero Captura o Importa Las Calificaciones del Grupo.")
    db().execute("UPDATE grupos SET publicado=1,capturado=1 WHERE id=?", (gid,)); db().commit(); return jsonify(ok=True, alumnos=n)

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)