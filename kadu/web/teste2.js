const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1366,height:728}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));const fs=require('fs');let html=fs.readFileSync('kadu.html','utf8');
html=html.replace('<script>/*QWEBCHANNEL*/</script>',`<script>window.qt={webChannelTransport:{}};window.QWebChannel=function(t,cb){const f=n=>()=>{};setTimeout(()=>cb({objects:{ponte:new Proxy({},{get:()=>()=>{}})}}),50)}</script>`);
await p.setContent(html);await p.waitForTimeout(500);await p.evaluate(()=>{kadu.iniciar('{}');kadu.mostrar()});await p.waitForTimeout(1500);
await p.evaluate(()=>kadu.menuBandeja(1180,620));await p.waitForTimeout(600);await p.screenshot({path:'tray.png'});console.log(errs);await b.close()})();
