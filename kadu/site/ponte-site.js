/* ================= PONTE COM O SITE =================
   No site o Kadu vive num iframe transparente por cima da página. O kadu-embed.js (na página):
   - deixa o clique atravessar o iframe, menos onde o Kadu e os menus dele estão (as "regiões");
   - manda a posição do mouse para os olhos seguirem;
   - repassa os comandos da página (falar, expressão, mostrar, esconder...).
   O bichinho (fome, energia, acessórios, posição) fica salvo no navegador do visitante. */
if(window.KADU_SITE){
  const CHAVE='kadu-site-v1';
  const ler=()=>{try{return JSON.parse(localStorage.getItem(CHAVE)||'{}')}catch(e){return {}}};
  const grava=(k,v)=>{try{const d=ler();d[k]=JSON.parse(v);localStorage.setItem(CHAVE,JSON.stringify(d))}catch(e){}};
  const mae=(tipo,dados={})=>{try{parent.postMessage(Object.assign({kadu:tipo},dados),'*')}catch(e){}};
  ponte={salvar:grava,regioes:j=>mae('regioes',{j}),falar(){},foco(){},ouvir(){},alternarMic(){},perguntar(){},
    sair(){if(!oculto)esconder()},menuClassico(){},iniciarComWindows(){},reiniciar(){},icone(){},pronta(){}};
  const CFG={saudacao:'Oi! Eu sou o Kadu. Pode me cutucar!',frases:[
    'Psiu... já viu os projetos lá embaixo?','Tô de olho no seu mouse, hein!','Me dá uma cenourinha? Clica em mim!',
    'Arrasta eu pra onde quiser.','Esfrega o mouse na minha cabeça... é bom demais!','Gostou do que viu? Manda um oi pro DG!'],
    comentarios:true,intervalo:[45,90],mostrarAoAbrir:true};
  let proxComentario=0,iniciado=false,_alvoToque=null;
  // toques repassados pela página não são ponteiros "de verdade": capturar não pode quebrar o arraste
  for(const f of ['setPointerCapture','releasePointerCapture']){const o=Element.prototype[f];Element.prototype[f]=function(id){try{return o.call(this,id)}catch(e){}}}
  // rodinha do mouse em cima do Kadu continua rolando a página
  addEventListener('wheel',e=>{mae('rolar',{dy:e.deltaY,dx:e.deltaX})},{passive:true});
  const sorteiaProx=()=>{const [a,b]=CFG.intervalo;proxComentario=performance.now()+(a+Math.random()*(b-a))*1000};
  function comeca(){if(iniciado)return;iniciado=true;
    const d=ler();window.kadu.iniciar(JSON.stringify({prefs:Object.assign({saida:'balao'},d.prefs||{},{saida:'balao'}),pet:d.pet,pos:d.pos}));
    if(CFG.mostrarAoAbrir&&!d.escondido)setTimeout(()=>{window.kadu.mostrar();if(CFG.saudacao)setTimeout(()=>fala(CFG.saudacao,'resposta','Kadu','animado',4200),1500)},400);
    sorteiaProx();mae('pronto')}
  setInterval(()=>{if(!iniciado||!CFG.comentarios||!CFG.frases.length)return;
    if(performance.now()<proxComentario)return;
    if(window.kadu.podeFalar()){fala(CFG.frases[Math.floor(Math.random()*CFG.frases.length)],'espontaneo','Kadu','feliz',4800)}sorteiaProx()},1000);
  const expressao=(nome,ms=2500)=>{if(!EXP[nome])return false;emoFala=nome;emoAte=performance.now()+ms;acorda(true);
    try{IMPULSO[nome]&&IMPULSO[nome]()}catch(e){}return true};
  addEventListener('message',e=>{const m=e.data;if(!m||typeof m!=='object'||!m.kaduCmd)return;
    switch(m.kaduCmd){
      case 'config':Object.assign(CFG,m.cfg||{});comeca();break;
      case 'mouse':window.kadu.mouse(m.x,m.y);break;
      case 'mouseFora':mouse.dentro=false;break;
      case 'foraClique':window.kadu.foraClique();break;
      case 'falar':if(!oculto)fala(String(m.texto||''),'resposta',m.rotulo||'Kadu',m.emo||'neutro',m.ms||Math.min(9000,3200+String(m.texto||'').length*45));break;
      case 'expressao':expressao(m.nome,m.ms);break;
      case 'mostrar':window.kadu.mostrar();grava('escondido','false');break;
      case 'esconder':window.kadu.esconder();grava('escondido','true');break;
      case 'alternar':window.kadu.alternar();break;
      case 'olhar':olhaPara=(m.x==null)?null:{x:m.x,y:m.y};break;
      case 'pular':F.syV-=2.4;F.yV-=90;break;
      case 'expressoes':mae('expressoes',{lista:Object.keys(EXP)});break;
      case 'ponteiro':{const o={bubbles:true,cancelable:true,composed:true,pointerId:7,pointerType:'touch',isPrimary:true,clientX:m.x,clientY:m.y,screenX:m.x,screenY:m.y,button:0,buttons:m.tipo==='pointerup'?0:1};
        if(m.tipo==='pointerdown')_alvoToque=document.elementFromPoint(m.x,m.y);
        const alvo=_alvoToque||document.elementFromPoint(m.x,m.y);if(!alvo)break;
        mouse={x:m.x,y:m.y,dentro:true};
        if(m.tipo!=='pointerup')alvo.dispatchEvent(new PointerEvent(m.tipo,o));
        if(m.tipo==='pointermove'&&alvo!==document.elementFromPoint(m.x,m.y))document.elementFromPoint(m.x,m.y)?.dispatchEvent(new PointerEvent('pointermove',o));
        if(m.tipo==='pointerup'){const fim=document.elementFromPoint(m.x,m.y);(fim||alvo).dispatchEvent(new PointerEvent('pointerup',o));
          if(fim===alvo||(alvo.contains&&alvo.contains(fim)))alvo.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:m.x,clientY:m.y}));_alvoToque=null}
        break}
    }});
  // quando o mouse está DENTRO do iframe (em cima do Kadu), avisa a página para ela decidir se o clique continua aqui
  addEventListener('pointermove',e=>mae('mouse',{x:e.clientX,y:e.clientY}),{passive:true});
  addEventListener('pointerdown',()=>mae('toque'),{passive:true});
  // sem a página mãe (abriu o kadu.html direto): começa sozinho, útil para testar
  setTimeout(()=>{if(!iniciado&&parent===window)comeca()},300);
  mae('carregou');
}
