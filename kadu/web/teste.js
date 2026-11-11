// carrega a página de produção no Chromium com uma "ponte" falsa para checar a API
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1366,height:728}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));const chamadas=[];
await p.exposeFunction('__py',(n,a)=>{chamadas.push(n+':'+String(a).slice(0,80))});
const fs=require('fs');let html=fs.readFileSync('kadu.html','utf8');
html=html.replace('<script>/*QWEBCHANNEL*/</script>',`<script>window.qt={webChannelTransport:{}};window.QWebChannel=function(t,cb){const f=n=>(...a)=>window.__py(n,JSON.stringify(a));setTimeout(()=>cb({objects:{ponte:{pronta:f('pronta'),salvar:f('salvar'),regioes:f('regioes'),icone:f('icone'),falar:f('falar'),perguntar:f('perguntar'),alternarMic:f('alternarMic'),ouvir:f('ouvir'),sair:f('sair'),reiniciar:f('reiniciar'),menuClassico:f('menuClassico'),iniciarComWindows:f('iniciarComWindows'),foco:f('foco')}}}),50)}</script>`);
await p.setContent(html);await p.waitForTimeout(600);
await p.evaluate(()=>{kadu.iniciar(JSON.stringify({prefs:{modo:'falante',saida:'voz_balao'},pet:{fome:80,cenouras:9}}));kadu.abrir()});
await p.waitForTimeout(1500);await p.screenshot({path:'p1.png'});
await p.evaluate(()=>{kadu.passo(1,'Abrindo');kadu.passo(2,"Whisper 'base' carregando")});await p.waitForTimeout(1500);
await p.evaluate(()=>{kadu.passo(3,"Whisper carregado na CPU");kadu.pronto('Pronto em 12 s')});await p.waitForTimeout(4500);await p.screenshot({path:'p2.png'});
await p.evaluate(()=>kadu.resposta('Oi! Tudo certo por aqui, bora estudar ponteiros?','animado','resposta'));await p.waitForTimeout(2500);await p.screenshot({path:'p3.png'});
await p.evaluate(()=>{kadu.log('🚀 Jarvis daemon started');kadu.log('❌ Gemini error 503')});
console.log(JSON.stringify(errs));console.log(chamadas.filter(c=>!c.startsWith('regioes')).slice(0,30).join('\n'));console.log(chamadas.filter(c=>c.startsWith('regioes')).slice(-1)[0]);await b.close()})();
