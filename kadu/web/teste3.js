const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1366,height:728}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));const fs=require('fs');let html=fs.readFileSync('kadu.html','utf8');
html=html.replace('<script>/*QWEBCHANNEL*/</script>',`<script>window.qt={webChannelTransport:{}};window.QWebChannel=function(t,cb){setTimeout(()=>cb({objects:{ponte:new Proxy({},{get:(o,n)=>(...a)=>{(window.__ch=window.__ch||[]).push(n)}})}}),50)}</script>`);
await p.setContent(html);await p.waitForTimeout(500);await p.evaluate(()=>{kadu.iniciar('{}');kadu.mostrar()});await p.waitForTimeout(2000);
await p.evaluate(()=>{kadu.estado('pensando');kadu.resposta('A Linda, claro!','apaixonado','resposta')});await p.waitForTimeout(1200);
const antes=await p.evaluate(()=>document.getElementById('txt').textContent);
await p.evaluate(()=>kadu.estado('falando'));await p.waitForTimeout(1200);
const depois=await p.evaluate(()=>document.getElementById('txt').textContent);
console.log(JSON.stringify({antes,depois,errs}));await b.close()})();
