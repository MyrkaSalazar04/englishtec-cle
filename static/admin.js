"use strict";
/* Extensión del panel de Coordinación: editar, dar de baja, reactivar y eliminar alumnos.
   Se carga después de app.js y reemplaza la lista de pre-registros. */
(function(){const s=document.createElement("style");s.textContent=`
dialog.dlg{border:1px solid var(--cardb);border-radius:22px;padding:22px;width:min(560px,92vw);max-height:90vh;overflow:auto;background:var(--bg2);color:var(--txt);box-shadow:var(--shadow)}
dialog.dlg::backdrop{background:rgba(5,10,30,.6)}
dialog.dlg h2{margin-top:0}
.acc{display:flex;flex-direction:column;gap:6px;min-width:130px}
.btn.danger{background:linear-gradient(135deg,#7E2610,#4A1208);box-shadow:none}
.tag{display:inline-block;background:var(--chip);border-radius:8px;padding:2px 8px;font-size:13px}
.chk{display:flex;gap:8px;align-items:center;margin-top:14px;font-weight:800}.chk input{width:22px;height:22px;min-height:0}
`;document.head.appendChild(s)})();

function dialogo(html){
  let d=document.getElementById("dlg");if(d)d.remove();
  d=document.createElement("dialog");d.id="dlg";d.className="dlg";d.innerHTML=html;document.body.appendChild(d);
  d.addEventListener("click",e=>{if(e.target===d)d.close()});d.showModal();return d;
}
const MOTIVOS=["No Pudo Pagar El Curso","Se Le Complicó El Horario","Se Arrepintió / Ya No Desea Cursarlo","Baja Temporal (Retomará Después)","Otro Motivo"];

function editarAlumno(a){
  const d=dialogo(`<h2>Editar Alumno</h2><p class="note">Folio ${esc(a.folio)}. Corrige Solo Lo Necesario.</p>
  <form id="fe" novalidate>
  <label for="e_nombre">Nombre Completo</label><input id="e_nombre" name="nombre" value="${esc(a.nombre)}">
  <div class="row"><div><label for="e_control">Número de control</label><input id="e_control" name="control" inputmode="numeric" value="${esc(a.control)}"></div>
  <div><label for="e_carrera">Carrera</label><input id="e_carrera" name="carrera" value="${esc(a.carrera)}"></div></div>
  <div class="row"><div><label for="e_semestre">Semestre</label><input id="e_semestre" name="semestre" inputmode="numeric" value="${esc(a.semestre)}"></div>
  <div><label for="e_tipo">Trámite</label><select id="e_tipo" name="tipo"><option ${a.tipo==="Inscripción"?"selected":""}>Inscripción</option><option ${a.tipo==="Reinscripción"?"selected":""}>Reinscripción</option></select></div></div>
  <div class="row"><div><label for="e_telefono">Teléfono (10 Dígitos)</label><input id="e_telefono" name="telefono" inputmode="tel" value="${esc(a.telefono)}"></div>
  <div><label for="e_correo">Correo</label><input id="e_correo" name="correo" value="${esc(a.correo)}"></div></div>
  <label class="chk"><input type="checkbox" id="e_pago" ${a.pago?"checked":""}> Pago recibido</label>
  <div id="em" role="alert"></div>
  <button class="btn" type="submit">Guardar Cambios</button> <button class="btn alt" type="button" id="ec">Cancelar</button></form>`);
  $("#ec",d).onclick=()=>d.close();
  $("#fe",d).onsubmit=async e=>{e.preventDefault();$$("input",d).forEach(i=>i.classList.remove("bad"));
    const j=Object.fromEntries(new FormData(e.target));j.pago=$("#e_pago",d).checked;
    const r=await api(`/api/coord/alumnos/${a.id}/editar`,{json:j});
    if(!r.ok){$("#em",d).innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;const i=r.data.campo&&$("#e_"+r.data.campo,d);if(i){i.classList.add("bad");i.focus()}return}
    d.close();toast("Datos del Alumno Actualizados");cAlumnos()};
}

function bajaAlumno(a){
  const d=dialogo(`<h2>Dar de baja</h2><p><b>${esc(a.nombre)}</b> · ${esc(a.control)}</p>
  <p class="note">Al Dar De Baja, El Alumno Se Elimina Definitivamente Del Curso: Deja De Aparecer En Su Grupo Y En Las Listas De Los Docentes, Y Se Eliminan Sus Calificaciones. Si Más Adelante Decide Retomar El Curso, Debe Realizar El Proceso De Pago Y La Coordinación Le Asigna El Grupo Del Nivel Que Dejó.</p>
  <form id="fb"><label for="b_m">Motivo</label><select id="b_m">${MOTIVOS.map(m=>`<option>${m}</option>`).join("")}</select>
  <label for="b_d">Detalle (opcional)</label><input id="b_d" placeholder="Ej. Cambió de Turno de Trabajo">
  <div id="bm" role="alert"></div><button class="btn danger" type="submit">Confirmar baja</button> <button class="btn alt" type="button" id="bc">Cancelar</button></form>`);
  $("#bc",d).onclick=()=>d.close();
  $("#fb",d).onsubmit=async e=>{e.preventDefault();const det=$("#b_d",d).value.trim();
    const r=await api(`/api/coord/alumnos/${a.id}/baja`,{json:{motivo:$("#b_m",d).value+(det?": "+det:"")}});
    if(!r.ok){$("#bm",d).innerHTML=`<div class="msg err">${esc(r.data.error)}</div>`;return}
    d.close();toast("Alumno dado de baja");cAlumnos()};
}

async function cAlumnos(){
  const q=window._q||"",st=window._st||"";
  const r=await api(`/api/coord/alumnos?q=${encodeURIComponent(q)}&estado=${st}`);if(r.status===401)return go();const d=r.data;
  const xl=`/api/coord/export.xlsx?q=${encodeURIComponent(q)}&estado=${st}`, bajas=st==="baja";
  const byId=Object.fromEntries(d.alumnos.map(a=>[a.id,a]));
  const fila=a=>bajas?
   `<tr><td>${esc(a.folio)}</td><td>${esc(a.nombre)}</td><td>${esc(a.control)}</td><td>${esc(a.tipo)}</td>
    <td colspan="3"><span class="tag">Baja el ${(a.baja_fecha||"").slice(0,10).split("-").reverse().join("/")}</span><br>${esc(a.baja_motivo)}</td>
    <td><div class="acc"><button class="btn sm" data-rea="${a.id}">Reactivar</button><button class="btn sm danger" data-del="${a.id}">Eliminar definitivamente</button></div></td></tr>`:
   `<tr><td>${esc(a.folio)}</td><td>${esc(a.nombre)}</td><td>${esc(a.control)}</td><td>${esc(a.tipo)}</td>
    <td>${a.pago?`<span class="pill">Recibido</span>`:`<button class="btn sm" data-pago="${a.id}">Marcar recibido</button>`}</td>
    <td><select class="lv" data-nv="${a.id}" aria-label="Nivel de ${esc(a.nombre)}"><option value="">—</option>${[1,2,3,4,5].map(n=>`<option ${String(n)===String(a.nivel)?"selected":""}>${n}</option>`).join("")}</select></td>
    <td><select class="lv" data-gr="${a.id}" aria-label="Grupo de ${esc(a.nombre)}"><option value="">Sin grupo</option>${d.grupos.map(g=>`<option value="${g.id}" ${g.id===a.grupo_id?"selected":""}>${esc(g.nombre)}</option>`).join("")}</select></td>
    <td><div class="acc"><button class="btn sm navy" data-ed="${a.id}">Editar</button><button class="btn sm alt" data-rs="${a.id}">Nuevo código</button><button class="btn sm danger" data-baja="${a.id}">Dar de baja</button></div></td></tr>`;
  $("#body").innerHTML=`<div class="kpis"><div><b>${d.total}</b>pre-registros activos</div><div><b>${d.recibidos}</b>pagos recibidos</div><div><b>${d.pendientes}</b>pagos pendientes</div><div><b>${d.bajas}</b>dados de baja</div></div>
  <div class="tools"><input id="q" type="search" placeholder="Buscar por nombre, control o folio" value="${esc(q)}" aria-label="Buscar"><select id="st" aria-label="Filtrar"><option value="">Activos (todos)</option><option value="pendiente">Pago pendiente</option><option value="recibido">Pago recibido</option><option value="baja">Dados de baja</option></select>
  <a class="btn sm navy" href="${xl}" download>Exportar a Excel</a></div>
  <div class="tablewrap"><table><thead><tr><th>Folio</th><th>Alumno</th><th>Control</th><th>Trámite</th>${bajas?'<th colspan="3">Baja</th>':'<th>Pago</th><th>Nivel</th><th>Grupo</th>'}<th>Acciones</th></tr></thead><tbody>
  ${d.alumnos.map(fila).join("")||`<tr><td colspan="8">Sin resultados.</td></tr>`}</tbody></table></div>`;
  $("#st").value=st;let tm;$("#q").oninput=e=>{clearTimeout(tm);tm=setTimeout(()=>{window._q=e.target.value;cAlumnos().then(()=>{const i=$("#q");i.focus();i.setSelectionRange(i.value.length,i.value.length)})},300)};
  $("#st").onchange=e=>{window._st=e.target.value;cAlumnos()};
  $$("[data-pago]").forEach(b=>b.onclick=async()=>{await api(`/api/coord/alumnos/${b.dataset.pago}/pago`,{json:{}});toast("Pago marcado como recibido");cAlumnos()});
  $$("[data-nv]").forEach(s=>s.onchange=async()=>{const r=await api(`/api/coord/alumnos/${s.dataset.nv}/nivel`,{json:{nivel:s.value}});toast(r.ok?"Nivel guardado":r.data.error)});
  $$("[data-gr]").forEach(s=>s.onchange=async()=>{const r=await api(`/api/coord/alumnos/${s.dataset.gr}/grupo`,{json:{grupo_id:s.value?+s.value:null}});toast(r.ok?"Grupo guardado":r.data.error)});
  $$("[data-rs]").forEach(b=>b.onclick=async()=>{if(!confirm("¿Generar un código nuevo? El anterior dejará de funcionar."))return;const r=await api(`/api/coord/alumnos/${b.dataset.rs}/reset-codigo`,{json:{}});
   if(r.ok)alert(`Nuevo código de ${r.data.nombre}:\n\n${r.data.codigo}\n\nEntrégaselo al alumno; no se vuelve a mostrar.`)});
  $$("[data-ed]").forEach(b=>b.onclick=()=>editarAlumno(byId[b.dataset.ed]));
  $$("[data-baja]").forEach(b=>b.onclick=()=>bajaAlumno(byId[b.dataset.baja]));
  $$("[data-rea]").forEach(b=>b.onclick=async()=>{const r=await api(`/api/coord/alumnos/${b.dataset.rea}/reactivar`,{json:{}});toast(r.ok?"Alumno reactivado. Asígnale grupo en la lista de activos.":r.data.error);cAlumnos()});
  $$("[data-del]").forEach(b=>b.onclick=async()=>{const a=byId[b.dataset.del];if(!confirm(`¿Eliminar DEFINITIVAMENTE a ${a.nombre}?\nSe borran su registro y sus calificaciones y no se puede deshacer.`))return;
   const r=await api(`/api/coord/alumnos/${a.id}`,{method:"DELETE"});toast(r.ok?"Registro eliminado":r.data.error);cAlumnos()});
}