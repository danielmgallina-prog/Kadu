/* ================= PONTE COM O APP (Python) =================
   A página roda numa janela transparente em tela cheia. O Python:
   - recebe as "regiões clicáveis" para deixar o resto do clique atravessar para a área de trabalho;
   - manda a posição do mouse (para os olhos seguirem) e o estado do assistente;
   - entrega as respostas do Gemini, o log técnico e o progresso da abertura;
   - salva preferências, bichinho, posição e diário no kadu.json. */
function salvaPrefs(){if(!ponte)return;document.body.classList.toggle('so-voz',prefsDemo.saida==='voz');
  ponte.salvar('prefs',JSON.stringify({modo,saida:prefsDemo.saida,tamanho:String(Math.round(W)),animacao:$('animSel').value,windows:!!prefsDemo.windows}))}
const TW=()=>mesa.offsetWidth||innerWidth,TH=()=>mesa.offsetHeight||innerHeight;
const _salvaT={};
function salvaLogo(qual){if(!ponte)return;clearTimeout(_salvaT[qual]);_salvaT[qual]=setTimeout(()=>{try{
  if(qual==='diario')ponte.salvar('diario',JSON.stringify(diarioLista.slice(0,120)));
  if(qual==='pet')ponte.salvar('pet',JSON.stringify(N));
  if(qual==='pos')ponte.salvar('pos',JSON.stringify({x:pos.x/Math.max(1,TW()),y:pos.y/Math.max(1,TH())}));}catch(e){}},700)}
if(PROD){setInterval(()=>salvaLogo('pet'),20000);addEventListener('beforeunload',()=>{try{ponte&&ponte.salvar('pet',JSON.stringify(N))}catch(e){}})}

// ---- regiões que recebem o mouse; o resto da tela deixa o clique passar
let _regAnt='';
function _rect(el,pad,R){if(!el)return;const r=el.getBoundingClientRect();if(r.width<1||r.height<1)return;
  R.push([Math.round(r.left-pad),Math.round(r.top-pad),Math.round(r.width+2*pad),Math.round(r.height+2*pad)])}
function _menus(){return radialAberto||bmenu.classList.contains('on')||vitrineAberta||barra.classList.contains('on')||menuBAberto||$('diario').classList.contains('on')}
function enviaRegioes(){if(!ponte)return;const R=[];
  if(!oculto||kadu.classList.contains('espiando'))_rect(kadu,0,R);
  if(radialAberto)radial.querySelectorAll('.rbtn').forEach(b=>_rect(b,4,R));
  if(bmenu.classList.contains('on'))_rect(bmenu,4,R);
  if(vitrineAberta)$('vitrine').querySelectorAll('.ac-item,.seta-c,.ac-info,.fecha-v,.saldo').forEach(e=>_rect(e,3,R));
  if(balao.classList.contains('on')&&balao.classList.contains('interativo'))_rect(balao,4,R);
  if(barra.classList.contains('on'))_rect(barra,6,R);
  if($('diario').classList.contains('on'))_rect($('diario'),4,R);
  if(menuBAberto)_rect($('menuB'),4,R);
  // tela inteira só quando precisa (menus, diário, arrastar, bolinha, abertura...); no resto a janela fica pequena em volta dele
  const grande=_menus()||segurando||!!item||abrindo||kaduNoDiario||(balao.classList.contains('on')&&balao.classList.contains('interativo'))||!!document.querySelector('.bola,.peca,.clarao');
  const j=JSON.stringify({r:R,tudo:!!(segurando||item),menus:_menus(),grande,k:[Math.round(pos.x),Math.round(pos.y),Math.round(W),Math.round(H)]});
  if(j!==_regAnt){_regAnt=j;ponte.regioes(j)}}
if(PROD)setInterval(enviaRegioes,50);
let _pensandoDesde=0;if(PROD)setInterval(()=>{if(estado==='pensando'){if(!_pensandoDesde)_pensandoDesde=performance.now();else if(performance.now()-_pensandoDesde>75000){_pensandoDesde=0;setEstado('esperando')}}else _pensandoDesde=0},2000);

// ---- ícone da bandeja acompanha a cara do Kadu
let _iconeAnt='';
if(PROD)setInterval(()=>{if(!ponte)return;const bd=$('bandeja'),sb=$('seloB');const k=(bd?bd.dataset.cara:'neutro')+'|'+(sb&&sb.classList.contains('on')?sb.dataset.s:'');
  if(k!==_iconeAnt){_iconeAnt=k;const [c,sl]=k.split('|');ponte.icone(c,sl==='null'?'':sl)}},300);

// ---- log técnico
function _classeLog(t){if(/❌|error|erro|failed|falh/i.test(t))return'er';if(/⚠|warn|aviso/i.test(t))return'av';if(/✅|ready|loaded|pronto|🎙️|Listening!/i.test(t))return'ok';return''}
let _tecT=null;

let _pendente=null,_pendenteT=null;
window.kadu={
  tela(w,h){mesa.style.setProperty('--tw',w+'px');mesa.style.setProperty('--th',h+'px')},
  offset(x,y){mesa.style.transform=(x||y)?`translate(${-x}px,${-y}px)`:''},
  iniciar(json){let d={};try{d=JSON.parse(json)}catch(e){}
    const p=d.prefs||{};
    if(p.modo&&modos[p.modo]){modo=p.modo;document.querySelectorAll('.modos button').forEach(x=>x.setAttribute('aria-pressed',x.dataset.modo===modo))}
    if(p.saida)prefsDemo.saida=p.saida;if(typeof p.windows==='boolean')prefsDemo.windows=p.windows;
    if(p.animacao)$('animSel').value=p.animacao;
    if(p.tamanho){const b=document.querySelector(`.tam [data-tam="${p.tamanho}"]`);if(b&&String(Math.round(W))!==String(p.tamanho))b.click()}
    document.body.classList.toggle('so-voz',prefsDemo.saida==='voz');
    if(d.pet&&typeof d.pet==='object'){const pt=d.pet;['fome','energia','humor','xp','nivel','cenouras','sujo'].forEach(k=>{if(typeof pt[k]==='number')N[k]=pt[k]});
      if(pt.possui)Object.assign(N.possui,pt.possui);if(pt.usando)Object.assign(N.usando,pt.usando);
      if(pt.papel)N.papel=pt.papel;if(typeof pt.escuros==='boolean')N.escuros=pt.escuros;
      ['oculos','gravata','bone','cachecol','cartola'].forEach(k=>$('ac-'+k).setAttribute('display',N.papel==='mascote'&&N.usando[k]?'inline':'none'));
      $('ac-escuros').setAttribute('display',N.papel==='assistente'&&N.escuros?'inline':'none');
      $('sujeira').setAttribute('opacity',N.papel==='mascote'?N.sujo.toFixed(2):0)}
    if(d.pos&&typeof d.pos.x==='number'){pos.x=d.pos.x*TW();pos.y=d.pos.y*TH();aplicaPos()}else posInicial();
    if(Array.isArray(d.diario)){diarioLista.length=0;d.diario.forEach(e=>diarioLista.push(e))}
    if(typeof d.mic==='boolean')micMudo=d.mic},
  abrir(){abertura(false,true)},
  passo(n,sub){passoExt=Math.max(passoExt,n);if(sub)subExt[n-1]=sub},
  pronto(sub){if(sub)subExt.pronto=sub;fimExt='ok';passoExt=99},
  falhou(msg){if(abrindo){erroExt=msg||'';fimExt='erro'}else{extra='erro';extraAte=performance.now()+6000;falaSemVoz=true;fala(msg||'Opa, deu um problema aqui.','erro','Ops','erro',5000);falaSemVoz=false}},
  mostrar(){if(oculto&&!animando&&!abrindo)mostrar()},
  alternar(){if(animando||abrindo)return;if(oculto)mostrar();else esconder()},
  esconder(){if(!oculto&&!animando)esconder()},
  estado(e){if(e==='falando'&&_pendente){const p=_pendente;_pendente=null;p()}
    if(abrindo)return;if(e==='falando'&&falando)return;
    if(e!==estado){if(e==='ouvindo'||e==='pensando')acorda();if(e==='esperando'&&(falando||balao.classList.contains('on')))return;setEstado(e)}},
  resposta(texto,emo,origem){if(!texto)return;
    if(origem==='usuario'){if(texto.trim()===ultimaPerguntaEnviada.trim()){ultimaPerguntaEnviada='';return}registraPergunta(texto);return}
    const vai=()=>{falaSemVoz=true;
      if(origem==='erro')fala(texto,'erro','Ops','erro',6000);else fala(texto,'resposta','Kadu',emo||'neutro',Math.min(12000,4200+texto.length*45));falaSemVoz=false};
    // A voz só começa depois que o áudio inteiro fica pronto. Para o balão não sair na frente da voz,
    // o Kadu continua "pensando" e solta o balão no instante em que a fala começa (ou em 8 s, no máximo).
    const comVoz=origem!=='erro'&&prefsDemo.saida!=='balao'&&!kaduNoDiario;
    if(origem==='chat'&&comVoz&&ponte)ponte.falar(texto);   // digitou? ele responde em voz alta também
    const mostra=()=>{if(oculto&&!abrindo&&!kaduNoDiario){mostrar();setTimeout(vai,950)}else vai()};
    if(comVoz){clearTimeout(_pendenteT);_pendente=mostra;_pendenteT=setTimeout(()=>{if(_pendente===mostra){_pendente=null;mostra()}},8000)}else mostra()},
  comenta(texto,tipo,emo){if(oculto||abrindo)return;const rot={espontaneo:'Comentário',lembrete:'Lembrete',reacao:'Reação'}[tipo]||'Kadu';fala(texto,tipo,rot,emo||'neutro')},
  podeFalar(){return !oculto&&!abrindo&&!animando&&!segurando&&!item&&!_menus()&&!balao.classList.contains('on')&&estado==='esperando'&&!dormindo},
  sistema(qual){if(oculto||abrindo)return;const b=$({bateria:'s-bateria',cpu:'s-cpu',internet:'s-net'}[qual]);if(b)b.click()},
  telaCheia(b){telaCheia=!!b},
  mic(pausado,avisa){const mudou=micMudo!==!!pausado;micMudo=!!pausado;if(mudou&&avisa&&!oculto)fala(micMudo?'Microfone pausado. Não tô ouvindo nada.':'Microfone ligado de novo!','resposta','Kadu',micMudo?'neutro':'feliz',2800)},
  mouse(x,y){mouse={x,y,dentro:true};if(Math.hypot(x-(pos.x+W/2),y-(pos.y+H/2))<260)acorda(true)},
  foraClique(){if(_menus()){fechaTudo();if(menuBAberto)fechaMenuB()}},
  menuBandeja(x,y){const m=$('menuB');if(menuBAberto){fechaMenuB();return}abreMenuB();const w=m.offsetWidth||252;
    // ícone escondido na setinha (^) do Windows: o menu sobe acima do ponto clicado para não ficar atrás da janelinha
    const fundo=(typeof y==='number'&&y<TH()-4)?Math.max(8,TH()-y+16):8;
    m.style.setProperty('bottom',fundo+'px','important');const cabe=TH()-fundo-12;if(m.scrollHeight>cabe){m.style.maxHeight=cabe+'px';m.style.overflowY='auto'}else{m.style.maxHeight='';m.style.overflowY=''}
    m.style.left=Math.max(8,Math.min(TW()-w-8,x-w+46))+'px'},
  log(linha){const t=String(linha||'').replace(/\s+$/,'');if(!t.trim())return;const h=new Date().toLocaleTimeString('pt-BR');
    tecLinhas.push([h,t,_classeLog(t)]);if(tecLinhas.length>400)tecLinhas.splice(0,tecLinhas.length-400);
    if($('diario').classList.contains('on')&&$('abaTec').getAttribute('aria-pressed')==='true'){clearTimeout(_tecT);_tecT=setTimeout(()=>abreDiario('tec'),250)}},
  musica(on){if(oculto||abrindo)return;if(on){emoFala='musica';emoAte=Infinity}else if(emoFala==='musica'){emoFala=null;emoAte=0}},
  salvarTudo(){try{ponte&&ponte.salvar('pet',JSON.stringify(N));ponte&&ponte.salvar('diario',JSON.stringify(diarioLista.slice(0,120)))}catch(e){}}
};
if(PROD&&window.qt&&window.QWebChannel){new QWebChannel(qt.webChannelTransport,ch=>{ponte=ch.objects.ponte;ponte.pronta()})}
