"use strict";
/* Código nuevo de un alumno: se muestra en una ventana (igual que en el pre-registro) con botón Copiar.
   Se carga después de admin.js. */
(function(){
  const base=cAlumnos;
  cAlumnos=async function(){
    await base();
    $$("[data-rs]").forEach(b=>{b.onclick=async()=>{
      const tr=b.closest("tr"),ctl=tr.children[2].textContent,nom=tr.children[1].textContent;
      if(!confirm(`¿Generar Un Código Nuevo Para ${nom}? El Anterior Dejará De Funcionar.`))return;
      const r=await api(`/api/coord/alumnos/${b.dataset.rs}/reset-codigo`,{json:{}});
      if(!r.ok){toast(r.data.error||"No Se Pudo Generar El Código");return}
      const d=dialogo(`<div style="text-align:center"><div class="flip"><div>✓</div></div>
        <h2>Nuevo Código Generado</h2>
        <p>Se Generó Y Asignó Un Nuevo Código A <b>${esc(r.data.nombre)}</b> (Control ${esc(ctl)}).</p>
        <div class="big" id="nc">${esc(r.data.codigo)}</div>
        <button class="btn alt sm" id="ncc" type="button" style="margin-top:10px">Copiar Código</button>
        <p class="note" style="text-align:left;margin-top:16px">Entrégaselo Al Alumno Por Teams o En Persona. El Código Anterior Dejó De Funcionar y Se Quitó El Bloqueo. Solo Se Muestra Esta Vez.</p>
        <button class="btn" id="ncx" type="button">Listo</button></div>`);
      $("#ncx",d).onclick=()=>d.close();
      $("#ncc",d).onclick=async()=>{
        try{await navigator.clipboard.writeText(r.data.codigo);toast("Código Copiado")}
        catch(e){const rg=document.createRange();rg.selectNodeContents($("#nc",d));const sl=getSelection();sl.removeAllRanges();sl.addRange(rg);
          let ok=false;try{ok=document.execCommand("copy")}catch(_){}toast(ok?"Código Copiado":"Selecciónalo y Copia Con Ctrl + C")}};
    }});
  };
})();