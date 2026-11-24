import io, os, re, time, threading, requests
from openpyxl import Workbook, load_workbook
B=os.environ.get("BASE","http://localhost:5055")
def sess():
    s=requests.Session(); t=s.get(B+"/api/csrf").json()["token"]; s.headers["X-CSRF-Token"]=t; return s
def login(u,p):
    s=sess(); r=s.post(B+"/api/login",json={"usuario":u,"clave":p}); assert r.status_code==200,r.text; return s
def nuevo(i):
    return dict(nombre="Alumno Prueba %d"%i,control=str(30000000+i),carrera="Sistemas",semestre="5",telefono="4881112233",correo="a%d@ejemplo.mx"%i,tipo="Inscripción")
def test_preregistro_ok_y_folio():
    s=sess(); r=s.post(B+"/api/preregistro",json=nuevo(int(time.time())%100000)); assert r.status_code==201; d=r.json()
    assert re.fullmatch(r"CLE-2026-\d{4}",d["folio"]) and re.fullmatch(r"[A-Z0-9]{4}-[A-Z0-9]{4}",d["codigo"])
def test_validaciones_mensaje_campo():
    s=sess(); j=nuevo(1); j["telefono"]="123"; r=s.post(B+"/api/preregistro",json=j); assert r.status_code==400 and r.json()["campo"]=="telefono"
    j=nuevo(1); j["correo"]="mal"; assert s.post(B+"/api/preregistro",json=j).json()["campo"]=="correo"
    j=nuevo(1); j["control"]="12ab"; assert s.post(B+"/api/preregistro",json=j).json()["campo"]=="control"
def test_duplicado():
    s=sess(); j=nuevo(900001); s.post(B+"/api/preregistro",json=j); r=s.post(B+"/api/preregistro",json=j); assert r.status_code==409 and "folio" in r.json()
def test_csrf_requerido():
    s=requests.Session(); s.get(B+"/api/csrf"); r=s.post(B+"/api/preregistro",json=nuevo(5)); assert r.status_code in (400,403)
def test_consulta_correcta_y_general():
    r=sess().post(B+"/api/consulta",json={"control":"20000001","codigo":"k7m4 2q9x"}); assert r.status_code==200; d=r.json()
    assert d["calificaciones"]==[90,85,88,92] and d["general"]==88.8 and d["nivel"]=="5"
def test_consulta_no_publicada_oculta():
    d=sess().post(B+"/api/consulta",json={"control":"20000012","codigo":"H6D2-9NVC"}).json(); assert d["calificaciones"] is None and d["publicado"] is False
def test_bloqueo_tras_5_intentos():
    s=sess()
    for i in range(4): assert s.post(B+"/api/consulta",json={"control":"20000058","codigo":"XXXX-XXXX"}).status_code==401
    assert s.post(B+"/api/consulta",json={"control":"20000058","codigo":"XXXX-XXXX"}).status_code==429
    assert s.post(B+"/api/consulta",json={"control":"20000058","codigo":"J2M6-8WVE"}).status_code==429
def test_codigo_no_en_claro():
    import sqlite3; c=sqlite3.connect(os.environ.get("DB","/tmp/cle_t/cle.db")); h=c.execute("SELECT codigo_hash FROM alumnos LIMIT 1").fetchone()[0]; assert h.startswith("pbkdf2:")
def test_rutas_protegidas():
    s=sess(); assert s.get(B+"/api/coord/alumnos").status_code==401 and s.get(B+"/api/docente/grupos").status_code==401
    d=login("docente1","Docente-2026"); assert d.get(B+"/api/coord/alumnos").status_code in (401,403)
def test_login_mal():
    assert sess().post(B+"/api/login",json={"usuario":"coordinacion","clave":"x"}).status_code==401
def test_coord_pago_nivel_grupo_reset():
    c=login("coordinacion","Coord-2026"); a=c.get(B+"/api/coord/alumnos?q=20000007").json()["alumnos"][0]
    assert c.post(B+f"/api/coord/alumnos/{a['id']}/pago").json()["ok"]
    assert c.post(B+f"/api/coord/alumnos/{a['id']}/nivel",json={"nivel":"2"}).status_code==200
    assert c.post(B+f"/api/coord/alumnos/{a['id']}/nivel",json={"nivel":"9"}).status_code==400
    n=c.post(B+f"/api/coord/alumnos/{a['id']}/reset-codigo").json()["codigo"]
    d=sess().post(B+"/api/consulta",json={"control":"20000007","codigo":n}).json(); assert d["pago"] and d["nivel"]=="2"
def test_busqueda_y_filtro():
    c=login("coordinacion","Coord-2026"); assert len(c.get(B+"/api/coord/alumnos?q=Torres").json()["alumnos"])==1
    assert all(not x["pago"] for x in c.get(B+"/api/coord/alumnos?estado=pendiente").json()["alumnos"])
def test_export_xlsx_qr_pdf_respaldo():
    c=login("coordinacion","Coord-2026"); r=c.get(B+"/api/coord/export.xlsx"); ws=load_workbook(io.BytesIO(r.content)).active; assert ws.max_row>=13
    q=c.get(B+"/api/coord/qr.png"); assert q.content[:4]==b"\x89PNG"
    p=c.get(B+"/api/coord/grupo/1/pdf"); assert p.content[:4]==b"%PDF"
    assert "alumnos" in c.get(B+"/api/coord/respaldo").json()
def test_periodo_cerrado_y_extra():
    c=login("coordinacion","Coord-2026"); c.post(B+"/api/coord/periodo",json={"abierto":False})
    s=sess(); j=nuevo(800001); assert s.post(B+"/api/preregistro",json=j).status_code==403
    c.post(B+"/api/coord/extras",json={"control":j["control"]}); assert s.post(B+"/api/preregistro",json=j).status_code==201
    c.post(B+"/api/coord/periodo",json={"abierto":True})
def xl(rows,head=("Número de control","Unidad 1","Unidad 2","Unidad 3","Unidad 4")):
    wb=Workbook(); ws=wb.active; ws.append(list(head)); [ws.append(r) for r in rows]; b=io.BytesIO(); wb.save(b); b.seek(0); return b
def test_docente_importar_con_error_y_publicar():
    d=login("docente1","Docente-2026")
    f=xl([["20000012",80,81,82,83],["20000023",90,"abc",70,80],["99999999",1,2,3,4],["20000040",101,50,50,50],["20000058",70,70,70,70]])
    r=d.post(B+"/api/docente/grupo/2/importar",files={"archivo":("c.xlsx",f)}); j=r.json(); assert j["correctas"]==2 and len(j["errores"])==3 and all("fila" in e for e in j["errores"])
    assert d.post(B+"/api/docente/grupo/2/publicar").json()["ok"]
    s=sess(); k=s.post(B+"/api/consulta",json={"control":"20000012","codigo":"H6D2-9NVC"}).json(); assert k["calificaciones"]==[80,81,82,83]
def test_docente_ajeno_403():
    assert login("docente1","Docente-2026").get(B+"/api/docente/grupo/3").status_code==403
def test_importar_encabezado_invalido():
    d=login("docente2","Docente-2026"); r=d.post(B+"/api/docente/grupo/3/importar",files={"archivo":("c.xlsx",xl([["20000007",1,2,3,4]],head=("Matrícula","A","B","C","D")))}); assert r.status_code==400
def test_importar_csv():
    d=login("docente2","Docente-2026"); csv="Número de control;Unidad 1;Unidad 2;Unidad 3;Unidad 4\n20000007;80,5;90;70;60\n"
    r=d.post(B+"/api/docente/grupo/3/importar",files={"archivo":("c.csv",csv.encode())}); assert r.json()["correctas"]==1
def test_https_redirect_header_y_headers():
    r=requests.get(B+"/",headers={"X-Forwarded-Proto":"http"},allow_redirects=False); assert r.status_code in (200,301,302,308)
    assert "nosniff" in requests.get(B+"/").headers.get("X-Content-Type-Options","")
def test_carga_100_usuarios():
    ok=[];lat=[]
    def w(i):
        t=time.time(); r=requests.get(B+"/api/publico"); lat.append(time.time()-t); ok.append(r.status_code==200)
    th=[threading.Thread(target=w,args=(i,)) for i in range(100)]; [t.start() for t in th]; [t.join() for t in th]
    assert all(ok) and sorted(lat)[94]<3
