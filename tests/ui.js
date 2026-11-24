const {chromium}=require("playwright");const B="http://localhost:5055";
(async()=>{const br=await chromium.launch();const out=[];const ok=(n,c,x="")=>{out.push((c?"PASS ":"FAIL ")+n+" "+x);};
const ctx=await br.newContext({viewport:{width:360,height:740},deviceScaleFactor:1});const p=await ctx.newPage();const errs=[];p.on("pageerror",e=>errs.push(e.message));
await p.goto(B);await p.waitForSelector(".hero");
ok("inicio 360px sin scroll horizontal",await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
await p.screenshot({path:"/tmp/s_inicio360.png"});
for(const th of["light","dark"]){await p.evaluate(t=>document.documentElement.dataset.theme=t,th);await p.waitForTimeout(600);
 const r=await p.evaluate((th)=>{const lum=c=>{const m=c.match(/[\d.]+/g).map(Number);const a=m.slice(0,3).map(v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4});return .2126*a[0]+.7152*a[1]+.0722*a[2]};
  const bg=getComputedStyle(document.querySelector(".card")).backgroundColor;const bgb=getComputedStyle(document.body).backgroundColor;
  const pairs=[[".card p",".card"],[".card h2",".card"],[".btn.alt",".card"],[".pill",".card"]];const res=[];
  for(const[a,b]of pairs){const e=document.querySelector(a);if(!e)continue;const cc=getComputedStyle(e).color;let bgc=getComputedStyle(e).backgroundColor;if(bgc.startsWith("rgba(0, 0, 0, 0")||bgc==="transparent")bgc=getComputedStyle(document.querySelector(b)).backgroundColor;
   let L1=lum(cc),L2=lum(bgc.replace(/rgba?\(([^)]+)\)/,(m,g)=>"rgb("+g.split(",").slice(0,3).join(",")+")"));if(th==="dark"&&b===".card"){L2=lum("rgb(16,27,66)")}else if(b===".card"){L2=lum("rgb(255,255,255)")}
   if(a===".pill"){L2=lum(getComputedStyle(e).backgroundColor)}
   res.push([a,((Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05)).toFixed(2)])}return res},th);
 ok("contraste "+th+" >=4.5",r.every(x=>+x[1]>=4.5),JSON.stringify(r));}
await p.evaluate(()=>document.documentElement.dataset.theme="light");
await p.click("#theme");ok("toggle tema oscuro",await p.evaluate(()=>document.documentElement.dataset.theme)==="dark");await p.screenshot({path:"/tmp/s_dark360.png"});await p.click("#theme");
// preregistro
await p.goto(B+"/#/preregistro");await p.waitForSelector("#f");
const t0=Date.now();await p.fill("#nombre","Rosa Prueba Lopez");await p.fill("#control","31000001");await p.fill("#carrera","Sistemas");await p.fill("#semestre","9");await p.selectOption("#tipo","Reinscripción");await p.fill("#telefono","4881234567");await p.fill("#correo","rosa@ejemplo.mx");
await p.click("#go");await p.waitForSelector(".big");const folio=await p.textContent(".big");const cod=await p.textContent("#cod");
ok("preregistro devuelve folio y código",/CLE-2026-\d{4}/.test(folio)&&/^[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(cod),folio+" "+cod);ok("tiempo preregistro <60s",Date.now()-t0<60000,(Date.now()-t0)+"ms");
await p.screenshot({path:"/tmp/s_folio.png"});
await p.goto(B+"/#/consulta");await p.goto(B+"/#/preregistro");await p.reload();await p.waitForSelector("#f");await p.fill("#nombre","Rosa");await p.click("#go");await p.waitForSelector(".msg.err");ok("error amigable por campo",(await p.textContent(".msg.err")).includes("nombre"));
// consulta
await p.goto(B+"/#/consulta");await p.waitForSelector("#f");await p.fill("#control","20000001");await p.fill("#codigo","k7m4-2q9x");await p.click("#go");await p.waitForSelector(".grade-total");
ok("consulta muestra 4 unidades y general",(await p.$$("#res tbody tr")).length===4&&(await p.textContent(".grade-total")).includes("88.8"));
ok("consulta 360px sin scroll",await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:"/tmp/s_consulta.png"});
await p.fill("#codigo","MALO-MALO");await p.click("#go");await p.waitForSelector(".msg.err");ok("código erróneo mensaje con intentos",(await p.textContent(".msg.err")).includes("intento"));
// coord
const c2=await br.newContext({viewport:{width:1280,height:800}});const q=await c2.newPage();await q.goto(B+"/#/coordinacion");await q.fill("#u","coordinacion");await q.fill("#p","Coord-2026");await q.click("button[type=submit]");await q.waitForSelector("table");
await q.screenshot({path:"/tmp/s_coord.png"});
await q.fill("#q","Marco");await q.waitForTimeout(700);ok("búsqueda filtra",(await q.$$("tbody tr")).length===1);
await q.click("[data-pago]");await q.waitForTimeout(500);ok("marcar pago recibido",(await q.textContent("tbody")).includes("Recibido"));
const [dl]=await Promise.all([q.waitForEvent("download"),q.click("text=Exportar a Excel")]);ok("descarga Excel",dl.suggestedFilename().endsWith(".xlsx"));
await q.click("text=QR y enlace");await q.waitForSelector(".qrbox img");await q.waitForTimeout(800);ok("QR visible",await q.evaluate(()=>document.querySelector(".qrbox img").naturalWidth>50));await q.screenshot({path:"/tmp/s_qr.png"});
// docente
const c3=await br.newContext({viewport:{width:1280,height:800}});const d=await c3.newPage();await d.goto(B+"/#/docente");await d.fill("#u","docente1");await d.fill("#p","Docente-2026");await d.click("button[type=submit]");await d.waitForSelector("table");
ok("Docente sin plantilla/ejemplo",!(await d.content()).match(/plantilla|ejemplo de/i));
const inp=await d.$$("td input.num");await inp[0].fill("77");await d.click("#sv");await d.waitForSelector(".msg.ok");ok("captura manual guarda",(await d.textContent("#rep")).includes("guardada"));await d.screenshot({path:"/tmp/s_docente.png"});
ok("sin errores JS",errs.length===0,errs.join("|"));
console.log(out.join("\n"));await br.close();})();
