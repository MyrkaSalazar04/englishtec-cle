"use strict";
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const app=$("#app"); let CSRF="", SES={rol:null,nombre:null};

/* ---------- Utilidades ---------- */
function toast(t){const e=$("#toast");e.textContent=t;e.classList.add("on");clearTimeout(toast.t);toast.t=setTimeout(()=>e.classList.remove("on"),2800)}
async function api(url,opt={}){
  opt.headers=Object.assign({"X-CSRF-Token":CSRF},opt.headers||{});
  if(opt.json!==undefined){opt.method=opt.method||"POST";opt.headers["Content-Type"]="application/json";opt.body=JSON.stringify(opt.json)}
  let r; try{r=await fetch(url,opt)}catch(e){return {ok:false,status:0,data:{error:"No Hay Conexión Con El Servidor. Revisa Tu Internet e Inténtalo de Nuevo."}}}
  let data={}; try{data=await r.json()}catch(e){}
  if(r.status===401&&SES.rol&&!data.intentos){SES={rol:null};}
  return {ok:r.ok,status:r.status,data};
}
async function boot(){const r=await api("/api/csrf");CSRF=r.data.token;SES={rol:r.data.rol,nombre:r.data.nombre}}
const flag=id=>`<svg viewBox="0 0 60 40" aria-hidden="true"><use href="#f-${id}"/></svg>`;
const volver=(t="Volver Al Inicio")=>`<a class="btn back" href="#/">← ${t}</a>`;
const pagoPill=p=>p?'<span class="pill">Pago Recibido</span>':'<span class="pill warn">Pago Pendiente</span>';
const fdate=s=>s?s.slice(0,10).split("-").reverse().join("/"):"";

/* ---------- Tema ---------- */
const SUN='<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';
const MOON='<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>';
function paintTheme(){const d=document.documentElement.dataset.theme==="dark",b=$("#theme");b.innerHTML=d?SUN:MOON;b.setAttribute("aria-label",d?"Cambiar a Tema Claro":"Cambiar a Tema Oscuro")}
$("#theme").onclick=()=>{const n=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=n;try{localStorage.setItem("et_theme",n)}catch(e){}paintTheme()};
paintTheme();

/* ---------- Palabras Flotantes ---------- */
(function(){const w=["Hello","Welcome","Learn","Speak","Grammar","Thank you","Goodbye","Friend","Dream","Read","Listen","Write","Level up","Good luck"],box=$("#words");
 w.forEach((t,i)=>{const s=document.createElement("span");s.textContent=t;s.style.left=(4+(i*7.1)%90)+"%";s.style.animationDuration=(22+(i*3)%14)+"s";s.style.animationDelay=(-i*2.3)+"s";box.appendChild(s)})})();

/* ---------- Escena 3D ---------- */
function scene(){return `<div class="scene" id="scene" aria-hidden="true"><div class="stage" id="stage"><div class="orbit">
 <div class="flag f1">${flag("uk")}</div><div class="flag f2">${flag("us")}</div><div class="flag f3">${flag("ca")}</div><div class="flag f4">${flag("au")}</div></div>
 <div class="globe"><b></b><b></b><b></b><b></b><b></b></div></div>
 <div class="tile t1">A</div><div class="tile t2">B</div><div class="tile t3">C</div>
 <div class="bubble b1">Hello!</div><div class="bubble b2">Welcome</div><div class="bubble b3">Let's learn</div>
 <i class="spark" style="left:45%;top:12%"></i><i class="spark" style="left:12%;top:50%;animation-delay:-1s"></i><i class="spark" style="right:14%;top:44%;animation-delay:-1.7s"></i></div>`}
function tilt(){const s=$("#scene"),st=$("#stage");if(!s||matchMedia("(prefers-reduced-motion: reduce)").matches)return;
 s.onmousemove=e=>{const r=s.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;st.style.transform=`rotateY(${x*28}deg) rotateX(${-y*20}deg)`};
 s.onmouseleave=()=>st.style.transform=""}

/* ---------- Enrutador ---------- */
const routes={"":vInicio,"/":vInicio,"/preregistro":vPre,"/consulta":vConsulta,"/coordinacion":vCoord,"/docente":vDocente};
async function go(){
  const h=(location.hash||"#/").slice(1)||"/"; const f=routes[h]||vInicio;
  const t=h.startsWith("/coord")?"coordinacion":h==="/docente"?"docente":"alumno";
  $$("nav .tab").forEach(a=>{const on=a.dataset.t===t;a.classList.toggle("on",on);on?a.setAttribute("aria-current","page"):a.removeAttribute("aria-current")});
  await f(); window.scrollTo(0,0);
}
window.addEventListener("hashchange",go);

/* ---------- ALUMNO: Inicio ---------- */
async function vInicio(){
  const r=await api("/api/publico"),p=r.data;
  app.innerHTML=`<section class="card hero"><div><div class="flags-row">${["uk","us","ca","au"].map(flag).join("")}</div>
  <h1>Tu Inglés Empieza Aquí</h1><p>Pre-Regístrate a Los Cursos de Inglés y Consulta Tus Calificaciones Desde Tu Celular, Sin Filas Ni Hojas Impresas.</p>
  <p><span class="pill ${p.periodo_abierto?"":"warn"}">${p.periodo_abierto?"Pre-Registro Abierto":"Pre-registro cerrado"}</span></p>
  <a class="btn" href="#/preregistro">Pre-Registrarme</a> <a class="btn alt" href="#/consulta">Consultar Calificaciones</a></div>${scene()}</section>
  <section class="card"><h2>Avisos de La Coordinación</h2>${p.avisos.length?p.avisos.map(a=>`<div class="aviso"><b>${esc(a.titulo)}</b><br>${esc(a.texto)}<br><small>${fdate(a.fecha)}</small></div>`).join(""):"<p>No hay avisos por ahora.</p>"}
  <h2>Examen de Ubicación</h2><p><b>Fecha:</b> ${esc(p.examen_fecha||"Por Confirmar")}<br><b>Lugar:</b> ${esc(p.examen_lugar||"Por Confirmar")}<br><b>Costo:</b> $${p.monto}</p></section>`;
  tilt();
}

/* ---------- ALUMNO: Pre-Registro ---------- */
async function vPre(){
  const r=await api("/api/publico"),p=r.data;
  app.innerHTML=`<section class="card"><h1>Pre-Registro A Cursos de Inglés</h1>
  <div class="steps"><span>1 · Tus Datos</span><span>2 · Recibes Tu Folio y Código</span><span>3 · Pagas El Examen</span></div>
  <p class="note">Tu Nivel Lo Asigna La Coordinación Después del Examen de Ubicación; Aquí No Se Elige. Prototipo Con Datos Simulados: No Uses Tus Datos Reales.</p>
  ${p.periodo_abierto?"":`<div class="msg err">El Periodo de Pre-Registro Está Cerrado. Si La Coordinación Te Dio Una Fecha Extra, Puedes Continuar.</div>`}
  <form id="f" novalidate>
   <label for="nombre">Nombre Completo</label><input id="nombre" name="nombre" autocomplete="name" placeholder="Nombre y apellidos">
   <div class="row"><div><label for="control">Número de Control</label><input id="control" name="control" inputmode="numeric" placeholder="Solo números"></div>
   <div><label for="carrera">Carrera</label><input id="carrera" name="carrera" placeholder="Ej. Sistemas Computacionales"></div></div>
   <div class="row"><div><label for="semestre">Semestre</label><input id="semestre" name="semestre" inputmode="numeric" placeholder="Ej. 5"></div>
   <div><label for="tipo">Trámite</label><select id="tipo" name="tipo"><option value="">Elige Una Opción</option><option>Inscripción</option><option>Reinscripción</option></select></div></div>
   <div class="row"><div><label for="telefono">Teléfono (10 dígitos)</label><input id="telefono" name="telefono" inputmode="tel" autocomplete="tel" placeholder="4880000000"></div>
   <div><label for="correo">Correo</label><input id="correo" name="correo" type="email" autocomplete="email" placeholder="nombre@correo.com"></div></div>
   <div id="m" role="alert"></div><button class="btn" id="go" type="submit">Enviar Pre-Registro</button> ${volver()}</form></section>`;
  $("#f").onsubmit=async e=>{e.preventDefault();$$("input",e.target).forEach(i=>i.classList.remove("bad"));
   const j=Object.fromEntries(new FormData(e.target));const b=$("#go");b.disabled=true;
   const r=await api("/api/preregistro",{json:j});b.disabled=false;
   if(!r.ok){$("#m").innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;if(r.data.campo){const i=$("#"+r.data.campo);if(i){i.classList.add("bad");i.focus()}}return}
   app.innerHTML=`<section class="card" style="text-align:center"><div class="flip"><div>✓</div></div><h1 style="display:inline-block">¡Listo, ${esc(j.nombre.split(" ")[0])}!</h1>
    <p>Tu Pre-Registro Quedó Guardado. Tu Folio Es</p><div class="big">${esc(r.data.folio)}</div>
    <p style="margin-top:14px"><b>Guarda Tu Código Personal.</b> Con Él y Tu Número de Control Consultarás Tus Calificaciones. Solo Se Muestra Esta Vez.</p>
    <div class="big" id="cod">${esc(r.data.codigo)}</div>
    <button class="btn alt sm" id="cp" style="margin-top:10px">Copiar Código</button>
    <div class="note" style="text-align:left;margin-top:16px"><b>Siguiente Paso:</b> Paga El Examen de Ubicación ($${p.monto}) y Avisa a La Coordinación; Ellos Marcarán Tu Pago Como Recibido.</div>
      <a class="btn" href="#/consulta">Ir A Consultar</a> <a class="btn back" href="#/">Volver Al Inicio</a></section>`;
   $("#cp").onclick=()=>{navigator.clipboard&&navigator.clipboard.writeText(r.data.codigo).then(()=>toast("Código Copiado"),()=>toast("Cópialo a Mano"))};
  };
}

/* ---------- ALUMNO: Consulta ---------- */
async function vConsulta(){
  app.innerHTML=`<section class="card"><h1>Consulta Tus Resultados</h1>
  <form id="f" novalidate><label for="control">Número de Control</label><input id="control" inputmode="numeric" autocomplete="username" placeholder="Solo Números">
  <label for="codigo">Código Personal</label><input id="codigo" autocomplete="off" autocapitalize="characters" placeholder="Ej. K7M4-2Q9X">
  <div id="m" role="alert"></div><button class="btn" id="go" type="submit">Consultar</button> ${volver()}</form>
  <p class="note" style="margin-top:16px">¿Olvidaste Tu Código? Pide Uno Nuevo En La Coordinación. Datos Simulados: Prueba con 20000001 · GQ49-6RAF</p></section><div id="res"></div>`;
  $("#f").onsubmit=async e=>{e.preventDefault();const b=$("#go");b.disabled=true;
   const r=await api("/api/consulta",{json:{control:$("#control").value,codigo:$("#codigo").value}});b.disabled=false;
   if(!r.ok){$("#m").innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;$("#res").innerHTML="";return}
   $("#m").innerHTML="";const d=r.data;let g="";
   if(d.calificaciones){g=`<div class="tablewrap"><table><thead><tr><th>Unidad</th><th>Calificación</th></tr></thead><tbody>${d.calificaciones.map((v,i)=>`<tr><td>Unidad ${i+1}</td><td>${v}</td></tr>`).join("")}</tbody></table></div>
      <div class="grade-total" style="margin-top:14px"><span>Calificación General</span><span class="n">${d.general}</span></div>
      <div class="msg ${d.aprobado?"ok":"err"}" role="status">${d.aprobado?"Resultado: Aprobado":"Resultado: Reprobado"}</div>`}
   else g=`<div class="msg ok" style="background:var(--row);color:var(--txt)">${d.grupo?"Tus Calificaciones Aún No Están Publicadas. Tu Docente Las Publicará Al Terminar La Captura.":"Todavía No Tienes Grupo Asignado. La Coordinación Te Lo Asignará."}</div>`;
   $("#res").innerHTML=`<section class="card"><h2>Hola, ${esc(d.nombre)}</h2><p>Folio <b>${esc(d.folio)}</b> · ${esc(d.tipo)}</p>
   <p>${pagoPill(d.pago)} ${d.nivel?`<span class="lvl">Nivel ${esc(d.nivel)}</span>`:`<span class="pill warn">Nivel Por Asignar</span>`}</p>
   ${d.pago_fecha?`<p>Pago Registrado el ${fdate(d.pago_fecha)}.</p>`:""}
   <p><b>Examen de Ubicación:</b> ${esc(d.examen_fecha||"Por Confirmar")} · ${esc(d.examen_lugar||"")}</p>
   ${d.grupo?`<h2>${esc(d.grupo)}</h2>`:""}${g}</section>`;
  };
}

/* ---------- Login del Personal ---------- */
function loginView(rol,titulo){
  app.innerHTML=`<section class="card" style="max-width:460px;margin:auto"><h1>${titulo}</h1><p class="note">Acceso solo para personal. Prototipo: coordinacion / Coord-2026 · docente1 / Docente-2026</p>
  <form id="f"><label for="u">Usuario</label><input id="u" autocomplete="username" autocapitalize="none"><label for="p">Contraseña</label><input id="p" type="password" autocomplete="current-password">
  <div id="m" role="alert"></div><button class="btn" type="submit">Entrar</button> ${volver()}</form></section>`;
  $("#f").onsubmit=async e=>{e.preventDefault();const r=await api("/api/login",{json:{usuario:$("#u").value,clave:$("#p").value}});
   if(!r.ok){$("#m").innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;return}
   SES={rol:r.data.rol,nombre:r.data.nombre};
   if(r.data.rol!==rol){await api("/api/logout",{json:{}});SES={rol:null};$("#m").innerHTML=`<div class="msg err">Esta cuenta no corresponde a esta sección.</div>`;return}
   go()};
}
const salir=()=>`<span><a class="btn back sm" href="#/">← Volver Al Inicio</a> <button class="btn alt sm" id="out">Cerrar Sesión</button></span>`;
function bindOut(){const o=$("#out");if(o)o.onclick=async()=>{await api("/api/logout",{json:{}});SES={rol:null};toast("Sesión cerrada");go()}}

/* ---------- COORDINACIÓN ---------- */
let ctab="alumnos";
async function vCoord(){
  if(SES.rol!=="coordinacion")return loginView("coordinacion","Coordinación");
  app.innerHTML=`<section class="card"><div class="tools" style="justify-content:space-between"><h1 style="margin:0">Panel de Coordinación</h1>${salir()}</div>
  <div class="tabs2" role="tablist">${[["alumnos","Pre-Registros"],["grupos","Grupos"],["ajustes","Periodo y Avisos"],["qr","QR y Enlace"]].map(([k,t])=>`<button role="tab" data-k="${k}" class="${k===ctab?"on":""}" aria-selected="${k===ctab}">${t}</button>`).join("")}</div><div id="body"></div></section>`;
  bindOut();$$(".tabs2 button").forEach(b=>b.onclick=()=>{ctab=b.dataset.k;vCoord()});
  ({alumnos:cAlumnos,grupos:cGrupos,ajustes:cAjustes,qr:cQR})[ctab]();
}
async function cAlumnos(){
  const q=window._q||"",st=window._st||"";
  const r=await api(`/api/coord/alumnos?q=${encodeURIComponent(q)}&estado=${st}`);if(r.status===401)return go();const d=r.data;
  const xl=`/api/coord/export.xlsx?q=${encodeURIComponent(q)}&estado=${st}`;
  $("#body").innerHTML=`<div class="kpis"><div><b>${d.total}</b>Pre-Registros</div><div><b>${d.recibidos}</b>Pagos Recibidos</div><div><b>${d.pendientes}</b>Pagos Pendientes</div></div>
  <div class="tools"><input id="q" type="search" placeholder="Buscar Por Nombre, Control o Folio" value="${esc(q)}" aria-label="Buscar"><select id="st" aria-label="Filtrar por pago"><option value="">Todos</option><option value="pendiente">Pago pendiente</option><option value="recibido">Pago recibido</option></select>
  <a class="btn sm navy" href="${xl}" download>Exportar a Excel</a></div>
  <div class="tablewrap"><table><thead><tr><th>Folio</th><th>Alumno</th><th>Control</th><th>Trámite</th><th>Pago</th><th>Nivel</th><th>Grupo</th><th>Código</th></tr></thead><tbody>
  ${d.alumnos.map(a=>`<tr><td>${esc(a.folio)}</td><td>${esc(a.nombre)}</td><td>${esc(a.control)}</td><td>${esc(a.tipo)}</td>
   <td>${a.pago?`<span class="pill">Recibido</span>`:`<button class="btn sm" data-pago="${a.id}">Marcar recibido</button>`}</td>
   <td><select class="lv" data-nv="${a.id}" aria-label="Nivel de ${esc(a.nombre)}"><option value="">—</option>${[1,2,3,4,5].map(n=>`<option ${String(n)===String(a.nivel)?"selected":""}>${n}</option>`).join("")}</select></td>
   <td><select class="lv" data-gr="${a.id}" aria-label="Grupo de ${esc(a.nombre)}"><option value="">Sin grupo</option>${d.grupos.map(g=>`<option value="${g.id}" ${g.id===a.grupo_id?"selected":""}>${esc(g.nombre)}</option>`).join("")}</select></td>
   <td><button class="btn sm alt" data-rs="${a.id}">Nuevo código</button></td></tr>`).join("")||`<tr><td colspan="8">Sin resultados.</td></tr>`}</tbody></table></div>`;
  $("#st").value=st;let tm;$("#q").oninput=e=>{clearTimeout(tm);tm=setTimeout(()=>{window._q=e.target.value;cAlumnos().then(()=>{const i=$("#q");i.focus();i.setSelectionRange(i.value.length,i.value.length)})},300)};
  $("#st").onchange=e=>{window._st=e.target.value;cAlumnos()};
  $$("[data-pago]").forEach(b=>b.onclick=async()=>{await api(`/api/coord/alumnos/${b.dataset.pago}/pago`,{json:{}});toast("Pago Marcado Como Recibido");cAlumnos()});
  $$("[data-nv]").forEach(s=>s.onchange=async()=>{const r=await api(`/api/coord/alumnos/${s.dataset.nv}/nivel`,{json:{nivel:s.value}});toast(r.ok?"Nivel Guardado":r.data.error)});
  $$("[data-gr]").forEach(s=>s.onchange=async()=>{const r=await api(`/api/coord/alumnos/${s.dataset.gr}/grupo`,{json:{grupo_id:s.value?+s.value:null}});toast(r.ok?"Grupo Guardado":r.data.error)});
  $$("[data-rs]").forEach(b=>b.onclick=async()=>{if(!confirm("¿Generar Un Código Nuevo? El Anterior Dejará de Funcionar."))return;const r=await api(`/api/coord/alumnos/${b.dataset.rs}/reset-codigo`,{json:{}});
   if(r.ok)alert(`Nuevo Código De ${r.data.nombre}:\n\n${r.data.codigo}\n\nEntrégaselo Al Alumno; No Se Vuelve A Mostrar.`)});
}
async function cGrupos(){
  const r=await api("/api/coord/grupos");if(r.status===401)return go();
  $("#body").innerHTML=`<div class="tablewrap"><table><thead><tr><th>Grupo</th><th>Docente</th><th>Alumnos</th><th>Calificaciones</th><th>Lista</th></tr></thead><tbody>${r.data.grupos.map(g=>`<tr><td>${esc(g.nombre)}</td><td>${esc(g.docente)}</td><td>${g.alumnos}</td>
  <td><span class="pill ${g.estado==="publicado"?"":"warn"}">${g.estado==="publicado"?"Publicadas":g.estado==="capturado"?"Capturadas, Sin Publicar":"Pendientes"}</span></td><td><a class="btn sm navy" href="/api/coord/grupo/${g.id}/pdf" Download>PDF</a></td></tr>`).join("")}</tbody></table></div>`;
}
async function cAjustes(){
  const [a,p]=await Promise.all([api("/api/coord/ajustes"),api("/api/publico")]);if(a.status===401)return go();const s=a.data;
  $("#body").innerHTML=`<h2>Periodo de pre-registro</h2><label class="switch"><input type="checkbox" id="per" ${s.periodo_abierto?"checked":""}> Pre-registro abierto</label>
  <h2 style="margin-top:20px">Fecha extra para un alumno</h2><div class="tools"><input id="ex" inputmode="numeric" placeholder="Número de control" style="max-width:240px"><button class="btn sm" id="exb">Habilitar</button></div>
  <div>${s.extras.map(c=>`<span class="pill warn" style="margin-right:6px">${esc(c)} <a href="#" data-dx="${esc(c)}" aria-label="Quitar ${esc(c)}">✕</a></span>`).join("")||"<small>Nadie Con Fecha Extra.</small>"}</div>
  <h2 style="margin-top:20px">Examen de ubicación</h2><div class="row"><div><label for="ef">Fecha y hora</label><input id="ef" value="${esc(s.examen_fecha)}"></div><div><label for="el">Lugar</label><input id="el" value="${esc(s.examen_lugar)}"></div></div><button class="btn sm" id="exs">Guardar Examen</button>
  <h2 style="margin-top:20px">Publicar aviso</h2><label for="at">Título</label><input id="at"><label for="ax">Texto</label><input id="ax"><button class="btn sm" id="ab">Publicar Aviso</button>
  <div style="margin-top:12px">${p.data.avisos.map(v=>`<div class="aviso"><b>${esc(v.titulo)}</b> <a href="#" data-da="${v.id}">Quitar</a><br>${esc(v.texto)}</div>`).join("")}</div>
  <h2 style="margin-top:20px">Respaldo</h2><a class="btn sm navy" href="/api/coord/respaldo" Download>Descargar Respaldo (JSON)</a>`;
  $("#per").onchange=async e=>{await api("/api/coord/periodo",{json:{abierto:e.target.checked}});toast(e.target.checked?"Pre-Registro Abierto":"Pre-Registro Cerrado")};
  $("#exb").onclick=async()=>{const r=await api("/api/coord/extras",{json:{control:$("#ex").value}});toast(r.ok?"Fecha Extra Habilitada":r.data.error);if(r.ok)cAjustes()};
  $$("[data-dx]").forEach(x=>x.onclick=async e=>{e.preventDefault();await api("/api/coord/extras/"+x.dataset.dx,{method:"DELETE"});cAjustes()});
  $("#exs").onclick=async()=>{await api("/api/coord/examen",{json:{fecha:$("#ef").value,lugar:$("#el").value}});toast("Examen Actualizado")};
  $("#ab").onclick=async()=>{const r=await api("/api/coord/avisos",{json:{titulo:$("#at").value,texto:$("#ax").value}});toast(r.ok?"Aviso Publicado":r.data.error);if(r.ok)cAjustes()};
  $$("[data-da]").forEach(x=>x.onclick=async e=>{e.preventDefault();await api("/api/coord/avisos/"+x.dataset.da,{method:"DELETE"});cAjustes()});
}
async function cQR(){
  const r=await api("/api/coord/link");if(r.status===401)return go();
  $("#body").innerHTML=`<p>Imprime o Comparte Este QR Para Que Los Alumnos Entren Directo Al Pre-Registro. Funciona También Como Enlace Por Teams o WhatsApp.</p>
  <div class="qrbox"><img src="/api/coord/qr.png?t=${Date.now()}" alt="Código QR del Pre-Registro"><div><p><b>Enlace:</b></p><div class="linkbox">${esc(r.data.url)}</div>
  <button class="btn sm" id="cl">Copiar Enlace</button> <a class="btn sm navy" href="/api/coord/qr.png?d=1" Download>Descargar QR</a></div></div>`;
  $("#cl").onclick=()=>navigator.clipboard.writeText(r.data.url).then(()=>toast("Enlace Copiado"),()=>toast("Cópialo A Mano"));
}

/* ---------- DOCENTE ---------- */
let gsel=null;
async function vDocente(){
  if(SES.rol!=="docente")return loginView("docente","Docente");
  const r=await api("/api/docente/grupos");if(r.status===401)return go();
  const gs=r.data.grupos;if(!gsel||!gs.find(g=>g.id===gsel))gsel=gs.length?gs[0].id:null;
  app.innerHTML=`<section class="card"><div class="tools" style="justify-content:space-between"><h1 style="margin:0">Mis Grupos</h1>${salir()}</div>
  <p class="note">Hola, ${esc(SES.nombre)}. Sube Tu Excel de Calificaciones (columnas «Número de Control» y «Unidad 1» a «Unidad 4») o Captura Aquí; Revisa y Publica.</p>
  <div class="tabs2">${gs.map(g=>`<button data-g="${g.id}" class="${g.id===gsel?"on":""}">${esc(g.nombre)} · ${g.estado}</button>`).join("")}</div><div id="body"></div></section>`;
  bindOut();$$("[data-g]").forEach(b=>b.onclick=()=>{gsel=+b.dataset.g;vDocente()});
  if(gsel)dGrupo();
}
async function dGrupo(){
  const r=await api("/api/docente/grupo/"+gsel);if(r.status===401)return go();const g=r.data;
  $("#body").innerHTML=`<h2>${esc(g.nombre)} <span class="pill ${g.publicado?"":"warn"}">${g.publicado?"Publicadas":"Sin Publicar"}</span></h2>
  <div class="tools"><input type="file" id="fx" accept=".xlsx,.csv" aria-label="Archivo de Calificaciones"><button class="btn sm navy" id="imp">Subir Excel</button></div>
  <div id="rep" role="status"></div>
  ${g.alumnos.length?`<div class="tablewrap"><table><thead><tr><th>Control</th><th>Alumno</th><th>U1</th><th>U2</th><th>U3</th><th>U4</th><th>General</th></tr></thead><tbody>
  ${g.alumnos.map(a=>`<tr data-c="${esc(a.control)}"><td>${esc(a.control)}</td><td>${esc(a.nombre)}</td>${a.u.map((v,i)=>`<td><input class="num" inputmode="decimal" value="${v==null?"":v}" aria-label="Unidad ${i+1} de ${esc(a.nombre)}"></td>`).join("")}<td><b>${a.general==null?"—":a.general}</b></td></tr>`).join("")}</tbody></table></div>
  <button class="btn" id="sv">Guardar Captura</button> <button class="btn navy" id="pb">Publicar a los alumnos</button>`:"<p>Este Grupo Todavía No Tiene Alumnos Asignados Por La Coordinación.</p>"}`;
  const rep=(d)=>{let h=`<div class="msg ${d.errores.length?"err":"ok"}">${d.correctas} fila(s) guardada(s).${d.errores.length?` ${d.errores.length} Con Error, Corrígelas:`:""}</div>`;
   if(d.errores.length)h+=`<ul>${d.errores.map(e=>`<li>Fila ${e.fila}: ${esc(e.motivo)}</li>`).join("")}</ul>`;$("#rep").innerHTML=h};
  $("#imp").onclick=async()=>{const f=$("#fx").files[0];if(!f){$("#rep").innerHTML='<div class="msg err">Elige Primero Tu Archivo de Excel.</div>';return}
   const fd=new FormData();fd.append("archivo",f);const r=await api(`/api/docente/grupo/${gsel}/importar`,{method:"POST",body:fd});
   if(!r.ok){$("#rep").innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;return}
   await dGrupo();rep(r.data)};
  const sv=$("#sv");if(sv){
   sv.onclick=async()=>{const filas=$$("tbody tr").map(tr=>({control:tr.dataset.c,u:$$("input",tr).map(i=>i.value)}));
    const r=await api(`/api/docente/grupo/${gsel}/guardar`,{json:{filas}});await dGrupo();rep(r.data)};
   $("#pb").onclick=async()=>{if(!confirm("Al Publicar, Cada Alumno Podrá Ver Sus Calificaciones. ¿Continuar?"))return;
    const r=await api(`/api/docente/grupo/${gsel}/publicar`,{json:{}});if(!r.ok){$("#rep").innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;return}toast("Calificaciones Publicadas");vDocente()}}
}

boot().then(go);