# Gera a página de produção do Kadu (kadu.html) a partir da prévia aprovada (kadu-interacoes.html).
# A prévia continua sendo a fonte: tudo que muda aqui é só o que a versão real precisa
# (tela cheia transparente, tempos reais, ponte com o Python).
import pathlib, re, sys

ORIGEM = pathlib.Path(sys.argv[1])
DESTINO = pathlib.Path(sys.argv[2])
s = ORIGEM.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:90], c)
    s = s.replace(a, b)


# ------------------------------------------------------------------ cabeçalho
rep("<title>Kadu: Cuidados e Menu</title>", "<title>Kadu</title>")
rep('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Lexend:wght@400;500&display=swap">',
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Lexend:wght@400;500&display=swap">\n'
    '<script>window.KADU_PROD=true;</script>\n<script>/*QWEBCHANNEL*/</script>')

# ------------------------------------------------------------------ CSS: só o Kadu, tela cheia e transparente
CSS = r"""
/* ===== versão real: a "mesa" vira a tela inteira, transparente; o resto da prévia some ===== */
html,body{background:transparent!important;margin:0!important;padding:0!important;overflow:hidden!important;height:100%}
body>.wrap{display:block!important;max-width:none!important;margin:0!important}
.wrap>header,.wrap>.painel,.wrap>.nota,.mesa>.janela,.mesa-topo,.estado,#chipAgente,.tarefas>span,#bandeja,#dicaB{display:none!important}
.wrap>.mesa{position:fixed!important;top:0!important;left:0!important;width:var(--tw,100vw)!important;height:var(--th,100vh)!important;transform-origin:0 0;max-height:none!important;min-height:0!important;
  border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important}
.tarefas{background:none!important;backdrop-filter:none!important;pointer-events:none!important;height:0!important}
.menu-b{bottom:8px!important;right:auto!important;transform-origin:calc(100% - 46px) 100%}
.menu-b::after{right:40px!important}
body.so-voz #balao:not(.interativo){opacity:0!important;pointer-events:none!important}
"""
i = s.index("</style>")
s = s[:i] + CSS + s[i:]

# ------------------------------------------------------------------ JS: constantes de produção
rep("const mesa=$('mesa'),kadu=$('kadu'),balao=$('balao'),txt=$('txt'),tag=$('tag'),estadoEl=$('estado');",
    "const mesa=$('mesa'),kadu=$('kadu'),balao=$('balao'),txt=$('txt'),tag=$('tag'),estadoEl=$('estado');\n"
    "const PROD=!!window.KADU_PROD,TX=PROD?0.025:1;   // TX: no PC as necessidades passam bem mais devagar que na prévia\n"
    "let ponte=null,telaCheia=false,falaSemVoz=false,ultVozPy=0;const modoEf=()=>telaCheia?'foco':modo;")
# posição e limites: sem a barra de tarefas falsa
rep("pos={x:r.width-W-30,y:r.height-H-65};aplicaPos()}", "pos={x:r.width-W-(PROD?40:30),y:r.height-H-(PROD?16:65)};aplicaPos()}")
rep("pos.y=Math.max(40,Math.min(r.height-H-42,pos.y));", "pos.y=Math.max(PROD?0:40,Math.min(r.height-H-(PROD?2:42),pos.y));")
rep("b:r.height-50,w:r.width,h:r.height}}", "b:r.height-(PROD?6:50),w:r.width,h:r.height}}")
rep("chao=R.height-50,larg=R.width;", "chao=R.height-(PROD?14:50),larg=R.width;")
# ele só "acorda" com o mouse quando o cursor chega perto (a tela inteira é a mesa)
rep("  if(mouse.dentro)acorda(true)});",
    "  if(mouse.dentro&&(!PROD||Math.hypot(mouse.x-(pos.x+W/2),mouse.y-(pos.y+H/2))<260))acorda(true)});")
# sono depois de 8 min parado (na prévia, 25 s)
rep("t-ultInteracao>25000;sono=", "t-ultInteracao>(PROD?480000:25000);sono=")
# necessidades em tempo real
rep("if(dormindo){N.energia=clamp(N.energia+3);}else{N.fome=clamp(N.fome-.25);N.energia=clamp(N.energia-.12);N.humor=clamp(N.humor-.1)}",
    "if(dormindo){N.energia=clamp(N.energia+3*TX);}else{N.fome=clamp(N.fome-.25*TX);N.energia=clamp(N.energia-.12*TX);N.humor=clamp(N.humor-.1*TX)}")
rep("if(livre&&t-ultPedido>30000){", "if(livre&&t-ultPedido>(PROD?600000:30000)){")
rep("pomodoroAte=performance.now()+25000;", "pomodoroAte=performance.now()+(PROD?25*60000:25000);")
# modo foco também quando há app em tela cheia
s = s.replace("if(modo!=='foco')fala(sorteia(['Ei... tem uma cenourinha", "if(modoEf()!=='foco')fala(sorteia(['Ei... tem uma cenourinha")
s = s.replace("else if(N.humor<30&&modo!=='foco')", "else if(N.humor<30&&modoEf()!=='foco')")
# comentários automáticos: no PC quem agenda é o Python (com os tempos reais e o app aberto)
rep("function agendaAuto(){clearInterval(timerAuto);const s=modos[modo].seg;if(!s)return;",
    "function agendaAuto(){clearInterval(timerAuto);if(PROD)return;const s=modos[modo].seg;if(!s)return;")

# ------------------------------------------------------------------ fala: voz pelo Python, "só voz" e "só balão"
rep("  if(window.__registra)window.__registra(texto,emo,tipo);",
    "  if(window.__registra)window.__registra(texto,emo,tipo);\n"
    "  if(PROD&&ponte&&!falaSemVoz&&!abrindo&&!(window.__menuAberto&&window.__menuAberto())&&!(window.__noDiario&&window.__noDiario())&&prefsDemo.saida!=='balao'&&performance.now()-ultVozPy>2500){ultVozPy=performance.now();ponte.falar(texto)}")

# ------------------------------------------------------------------ preferências salvas
rep("      if(nome==='Saída')prefsDemo.saida=v;", "      if(nome==='Saída'){prefsDemo.saida=v;salvaPrefs()}")
rep("      if(nome==='Ao ligar o PC')prefsDemo.windows=v==='sim';", "      if(nome==='Ao ligar o PC'){prefsDemo.windows=v==='sim';salvaPrefs();if(ponte)ponte.iniciarComWindows(prefsDemo.windows)}")
rep("      if(nome==='Animação de entrada')$('animSel').value=v;", "      if(nome==='Animação de entrada'){$('animSel').value=v;salvaPrefs()}")
rep("  modo=b.dataset.modo;document.querySelectorAll('.modos button')", "  modo=b.dataset.modo;salvaPrefs();document.querySelectorAll('.modos button')")
rep("m.querySelectorAll('[data-saida-b]').forEach(b=>b.onclick=()=>{prefsDemo.saida=b.dataset.saidaB;abreMenuB()});",
    "m.querySelectorAll('[data-saida-b]').forEach(b=>b.onclick=()=>{prefsDemo.saida=b.dataset.saidaB;salvaPrefs();abreMenuB()});")

# ------------------------------------------------------------------ microfone, barra de conversa e diário reais
rep("function alternaMic(){micMudo=!micMudo;",
    "function alternaMic(){if(PROD&&ponte){fechaTudo();ponte.alternarMic();return}micMudo=!micMudo;")
rep("$('btMic').onclick=()=>{if(gravando){",
    "$('btMic').onclick=()=>{if(PROD){if(micMudo){fala('O microfone está pausado. Liga no menu 🎤.','resposta','Kadu','neutro',3000);return}\n"
    "  barra.classList.add('gravando');$('btMic').classList.add('gravando');ondasVivas(true);F.syV-=1.5;if(ponte)ponte.ouvir();\n"
    "  clearTimeout(gravando);gravando=setTimeout(()=>{ondasVivas(false);barra.classList.remove('gravando');$('btMic').classList.remove('gravando');gravando=null},6000);return}\n"
    "  if(gravando){")
rep("function envia(){const t=campo.value.trim();if(!t)return;fechaBarra();registraPergunta(t);setEstado('pensando');",
    "function envia(){const t=campo.value.trim();if(!t)return;fechaBarra();registraPergunta(t);setEstado('pensando');\n"
    "  if(PROD){ultimaPerguntaEnviada=t;if(ponte)ponte.perguntar(t);return}")
rep("const diarioLista=[];let ultimaPergunta=null;", "const diarioLista=[];let ultimaPergunta=null,ultimaPerguntaEnviada='';const tecLinhas=[];")
# diário técnico com o log de verdade
i = s.index("  if(aba==='tec'){c.innerHTML=`<pre class=\"tec\">${[")
j = s.index(".join('\\n')}</pre>`;}", i) + len(".join('\\n')}</pre>`;}")
s = s[:i] + ("  if(aba==='tec'){const esc=t=>t.replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));"
             "c.innerHTML=`<pre class=\"tec\">${(PROD?tecLinhas:[['--:--:--','Sem registros ainda','']]).slice(-300).map(([h,t,c])=>`<span style=\"color:#7D74A8\">${h}</span>  <span class=\"${c}\">${esc(t)}</span>`).join('\\n')}</pre>`;"
             "c.scrollTop=c.scrollHeight}") + s[j:]
# guarda o diário
rep("ultimaPergunta=null;if(diarioLista.length>40)diarioLista.pop()};", "ultimaPergunta=null;if(diarioLista.length>120)diarioLista.pop();salvaLogo('diario')};")

# ------------------------------------------------------------------ bandeja: itens extras
rep("    ${it('diario','diario','Diário')}",
    "    ${it('diario','diario','Diário')}\n    ${PROD?it('pomodoro','energia',pomodoroAte?'Pomodoro rodando':'Pomodoro (25 min)')+it('estudo','diario','Modo estudo'):''}")
rep("const acoes={mostra:()=>oculto?mostrar():esconder(),",
    "const acoes={pomodoro:()=>{if(oculto)mostrar();setTimeout(()=>$('s-pomodoro').click(),oculto?900:0)},estudo:()=>{if(oculto)mostrar();setTimeout(()=>$('s-estudo').click(),oculto?900:0)},"
    "mais:()=>{if(ponte)ponte.menuClassico()},mostra:()=>oculto?mostrar():esconder(),")
rep("${it('ajustes','ajustes','Ajustes')}${it('sair','sair','Sair do Kadu','','perigo')}",
    "${it('ajustes','ajustes','Ajustes')}${PROD?it('mais','ajustes','Mais opções do assistente'):''}${it('sair','sair','Sair do Kadu','','perigo')}")
rep("sair:()=>fala('No app de verdade, isto fecha o Kadu. Até mais!','resposta','Kadu','feliz',3000)}",
    "sair:()=>{if(PROD&&ponte){fala('Até mais!','resposta','Kadu','feliz',1500);setTimeout(()=>ponte.sair(),900)}else fala('No app de verdade, isto fecha o Kadu. Até mais!','resposta','Kadu','feliz',3000)}}")
rep("bmenu.querySelector('[data-sair]')?.addEventListener('click',()=>{fechaTudo();fala('No app de verdade, isto fecha o Kadu. Até mais!','resposta','Kadu','feliz',3000)})}",
    "bmenu.querySelector('[data-sair]')?.addEventListener('click',()=>{fechaTudo();if(PROD&&ponte){fala('Até mais!','resposta','Kadu','feliz',1500);setTimeout(()=>ponte.sair(),900)}else fala('No app de verdade, isto fecha o Kadu. Até mais!','resposta','Kadu','feliz',3000)})}")

# ------------------------------------------------------------------ abertura acompanhando o carregamento real
rep("async function abertura(comErro){", "let passoExt=0,fimExt=null,erroExt='',subExt={};\nasync function abertura(comErro,real=false){if(real){passoExt=0;fimExt=null;erroExt='';subExt={}}")
rep("    if(comErro&&i===3){", "    if((comErro&&i===3)||(real&&fimExt==='erro')){")
rep("falaX('Ligando o cérebro...','resposta','Abrindo','neutro',86400000,{sub:'Gemini não respondeu... tentando de novo'});",
    "falaX(real?(passos[i]?passos[i][0]:'Ligando o cérebro...'):'Ligando o cérebro...','resposta','Abrindo','neutro',86400000,{sub:real?'Algo deu errado... checando':'Gemini não respondeu... tentando de novo'});")
rep("      falaX('Ops... explodiu tudo aqui.','erro','Ops','erro',86400000,{sub:'Gemini não respondeu: sem conexão com a internet (tentei 3 vezes)',",
    "      falaX('Ops... explodiu tudo aqui.','erro','Ops','erro',86400000,{sub:real?(erroExt||'O assistente não conseguiu iniciar'):'Gemini não respondeu: sem conexão com a internet (tentei 3 vezes)',")
rep("        acoes:[['Tentar de novo',()=>{balao.classList.remove('on');extra=null;abertura(false)}],['Ver diário',()=>abreDiario('tec')]]});",
    "        acoes:[['Tentar de novo',()=>{balao.classList.remove('on');extra=null;if(PROD&&ponte){ponte.reiniciar();abertura(false,true)}else abertura(false)}],['Ver diário',()=>abreDiario('tec')]]});")
rep("    falaX(t,'resposta','Abrindo','neutro',86400000,{sub});await sobe(pct);await espera(reduz?0:420)}",
    "    falaX(t,'resposta','Abrindo','neutro',86400000,{sub:real?(subExt[i]||sub):sub});\n"
    "    if(real){await new Promise(res=>{(function chk(){if(fimExt||passoExt>i)res();else setTimeout(chk,150)})()});if(fimExt==='erro'){i--;continue}\n"
    "      if(subExt[i])falaX(t,'resposta','Abrindo','neutro',86400000,{sub:subExt[i]})}\n"
    "    await sobe(pct);await espera(reduz?0:420)}")
rep("falaX('Tudo pronto!','resposta','Abrindo','feliz',900,{sub:'Pronto em 31 s'});",
    "falaX('Tudo pronto!','resposta','Abrindo','feliz',900,{sub:real?subExt.pronto||'':'Pronto em 31 s'});")
# ao terminar a abertura avisa o Python e salva
rep("    fala(sorteia(['Bom dia! Bora trabalhar?','Acordei! O que vamos fazer hoje?','Tô aqui! Pode chamar.']),'resposta','Kadu','animado',3500)})}",
    "    fala(sorteia(['Bom dia! Bora trabalhar?','Acordei! O que vamos fazer hoje?','Tô aqui! Pode chamar.']),'resposta','Kadu','animado',3500)})}\n"
    "if(PROD){$('s-abertura').onclick=null;$('s-abertura-erro').onclick=null}")

# ------------------------------------------------------------------ salvar posição/tamanho, foco do teclado
rep("function solta(){if(!segurando)return;segurando=false;if(arrastou)soltouEm=performance.now();",
    "function solta(){if(!segurando)return;segurando=false;if(arrastou){soltouEm=performance.now();salvaLogo('pos')}")
rep("      if(nome==='Tamanho'){document.querySelector(`.tam [data-tam=\"${v}\"]`).click();setTimeout(posicionaBmenu,700)}",
    "      if(nome==='Tamanho'){document.querySelector(`.tam [data-tam=\"${v}\"]`).click();setTimeout(()=>{posicionaBmenu();salvaPrefs()},800)}")
rep("function abreBarra(){if(oculto||abrindo)return;fechaRadial();fechaBmenu();barra.classList.add('on');",
    "function abreBarra(){if(oculto||abrindo)return;fechaRadial();fechaBmenu();barra.classList.add('on');if(ponte)ponte.foco();")
rep("function abreDiario(aba){const d=$('diario');", "function abreDiario(aba){const d=$('diario');if(ponte)ponte.foco();")

# ------------------------------------------------------------------ arrastar usa coordenadas da tela (a janela pode mudar de tamanho no meio)
rep("ini={x:e.clientX,y:e.clientY,px:pos.x,py:pos.y};", "ini={x:e.screenX,y:e.screenY,px:pos.x,py:pos.y};")
rep("kadu.addEventListener('pointermove',e=>{if(!segurando)return;const dx=e.clientX-ini.x,dy=e.clientY-ini.y;",
    "kadu.addEventListener('pointermove',e=>{if(!segurando)return;const dx=e.screenX-ini.x,dy=e.screenY-ini.y;")

# ------------------------------------------------------------------ partida: no PC quem manda começar é o Python
rep("posInicial();agendaAuto();requestAnimationFrame(frame);\nsetTimeout(()=>abertura(false),500);",
    "posInicial();agendaAuto();requestAnimationFrame(frame);\nif(!PROD)setTimeout(()=>abertura(false),500);\nelse{oculto=true;kadu.classList.add('fora');}\n/*PONTE*/")

PONTE = open(pathlib.Path(__file__).with_name("ponte.js"), encoding="utf-8").read()
rep("/*PONTE*/", PONTE)
DESTINO.write_text(s, encoding="utf-8")
print("ok", len(s))
