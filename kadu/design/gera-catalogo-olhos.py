# Catálogo de olhos novos do Kadu — cada expressão anima orelhas (base e ponta), olhos e corpo de forma independente.
import math
D="#1B1530"
def kf(nome,quadros):
    return "@keyframes "+nome+"{"+"".join(f"{p}{{transform:{t}}}" for p,t in quadros)+"}\n"
def onda(nome,f,dur_pts=40):
    # gera keyframes a partir de uma função p(0..1)->transform
    return "@keyframes "+nome+"{"+"".join(f"{100*k/dur_pts:.2f}%{{transform:{f(k/dur_pts)}}}" for k in range(dur_pts+1))+"}\n"
def regra(k,parte,anim): return f".k.{k} .{parte}{{animation:{anim}}}\n"

T=[]  # (chave, nome, descrição, olhoE, olhoD, atras, frente, css)

# 1 PIDÃO — olha para cima em 3D; olhos tremem cada um num tempo; orelhas para trás balançando opostas
T.append(("pidao","Pidão","Efeito 3D de baixo para cima: inclina o rosto para trás e olha para você com olhos enormes. Cada olho treme e pulsa no seu tempo, as orelhas inclinam um pouquinho para trás e balançam devagar e o corpo encolhe e estica como quem implora.",
 f'<ellipse cx="40.6" cy="58.6" rx="6.6" ry="8" fill="{D}"/><ellipse class="br" cx="42.4" cy="54.2" rx="3" ry="3.4" fill="#fff"/><circle cx="38.4" cy="61.6" r="1.4" fill="#fff"/>',
 f'<ellipse cx="59.4" cy="58.6" rx="6.6" ry="8" fill="{D}"/><ellipse class="br" cx="61.2" cy="54.2" rx="3" ry="3.4" fill="#fff"/><circle cx="57.2" cy="61.6" r="1.4" fill="#fff"/>',"","",
 kf("pid-corpo",[("0%,100%","scale(1.03,.95)"),("50%","scale(1.05,.92) translateY(-1px)")])+
 kf("pid-oA",[("0%,100%","rotate(-7deg)"),("50%","rotate(-11deg)")])+kf("pid-oB",[("0%,100%","rotate(50deg)"),("50%","rotate(56deg)")])+
 kf("pid-p",[("0%,100%","rotate(3deg)"),("50%","rotate(-3deg)")])+
 kf("pid-olE",[("0%,100%","scale(1) translateY(0)"),("30%","scale(1.07) translateY(-.6px)"),("60%","scale(.98)")])+
 kf("pid-olD",[("0%,100%","scale(1.04)"),("45%","scale(.97) translateY(.4px)"),("75%","scale(1.08) translateY(-.6px)")])+
 kf("pid-br",[("0%,100%","translate(0,0)"),("50%","translate(.6px,-.5px)")])+
 regra("pidao","corpo","pid-corpo 2.8s ease-in-out infinite")+regra("pidao","oA","pid-oA 2.8s ease-in-out infinite")+regra("pidao","oB","pid-oB 2.8s ease-in-out infinite")+
 regra("pidao","pA","pid-p 2.8s ease-in-out -.4s infinite")+regra("pidao","pB","pid-p 2.8s ease-in-out -1.8s infinite")+
 regra("pidao","olE","pid-olE 1.9s ease-in-out infinite")+regra("pidao","olD","pid-olD 2.3s ease-in-out infinite")+regra("pidao","br","pid-br .25s linear infinite alternate")))

# 2 CHORANDO — soluço: o corpo dá trancos; orelhas caídas tremendo; olhos apertam alternados
rio=lambda x:f'<rect x="{x-5}" y="64.5" width="10" height="33" rx="4.2" fill="url(#gRio)"/><path class="rio-b" d="M{x-2.4},68 V97" stroke="#E8F7FF" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="6 5 2 6" fill="none"/>'
T.append(("chorando","Chorando (cachoeira)","Estilo emoji: olhos fechados apertados e uma cachoeira larga descendo de cada olho até a borda do corpo, pingando ali. O corpo soluça em trancos, as orelhas baixam um pouco e tremem e os olhos apertam alternados. Já está na prévia principal.",
 f'<path d="M36,65.6 Q41,59.6 46,65.6" stroke="{D}" stroke-width="3.6" fill="none" stroke-linecap="round"/>',
 f'<path d="M54,65.6 Q59,59.6 64,65.6" stroke="{D}" stroke-width="3.6" fill="none" stroke-linecap="round"/>',
 '<g clip-path="url(#cpCabeca)">'+rio(41)+rio(59)+'</g><g class="pinga"><circle cx="39" cy="90" r="1.3" fill="#6FC3FF"/><circle cx="61" cy="90" r="1.3" fill="#6FC3FF"/></g>',"",
 kf("ch-corpo",[("0%,40%,100%","scale(1,1)"),("8%","scale(1.03,.95) translateY(1px)"),("16%","scale(.99,1.02)"),("24%","scale(1.03,.95) translateY(1px)"),("32%","scale(1,1)")])+
 kf("ch-oA",[("0%,100%","rotate(-11deg)"),("50%","rotate(-9deg)")])+kf("ch-oB",[("0%,100%","rotate(58deg)"),("50%","rotate(55deg)")])+
 kf("ch-p",[("0%,100%","rotate(4deg)"),("50%","rotate(7deg)")])+
 kf("ch-olho",[("0%,100%","scaleY(1)"),("50%","scaleY(.7) translateY(.6px)")])+
 regra("chorando","corpo","ch-corpo 1.4s ease-in-out infinite")+regra("chorando","oA","ch-oA .5s ease-in-out infinite")+regra("chorando","oB","ch-oB .62s ease-in-out infinite")+
 regra("chorando","pA","ch-p .5s ease-in-out -.2s infinite")+regra("chorando","pB","ch-p .62s ease-in-out -.3s infinite")+
 regra("chorando","olE","ch-olho .7s ease-in-out infinite")+regra("chorando","olD","ch-olho .7s ease-in-out -.35s infinite")))

# 3 MAREJADO — água sobe nos olhos; corpo arrepia; orelhas vão baixando
agua=lambda cx,id:f'<clipPath id="{id}" clipPathUnits="userSpaceOnUse"><ellipse cx="{cx}" cy="64" rx="4.6" ry="6.8"/></clipPath><ellipse cx="{cx}" cy="64" rx="4.6" ry="6.8" fill="{D}"/><g clip-path="url(#{id})"><path class="nivel" d="M{cx-11},66 Q{cx-5.5},64.2 {cx},66 T{cx+11},66 T{cx+22},66 V80 H{cx-11}Z" fill="#6FC3FF" fill-opacity=".85"/></g><ellipse class="br" cx="{cx+1.6}" cy="60.8" rx="1.8" ry="2.2" fill="#fff"/><circle cx="{cx-1.4}" cy="63.4" r=".8" fill="#fff"/>'
T.append(("marejado","Marejado","Os olhos vão se enchendo de água por dentro e o nível balança, cada olho com um ritmo. As orelhas vão baixando um pouquinho, as pontas tremem, e o corpo dá arrepios de quem está segurando o choro.",
 agua(41,"cpM1"),agua(59,"cpM2"),"","",
 kf("ma-corpo",[("0%,100%","scale(1,1)"),("45%","scale(1.01,.98)"),("50%","scale(1.02,.97) translateX(.4px)"),("53%","translateX(-.4px)"),("56%","scale(1.01,.98)")])+
 kf("ma-oA",[("0%","rotate(-2deg)"),("60%,100%","rotate(-10deg)")])+kf("ma-oB",[("0%","rotate(40deg)"),("60%,100%","rotate(54deg)")])+
 kf("ma-p",[("0%,100%","rotate(0)"),("50%","rotate(2.5deg)")])+kf("ma-nivel",[("0%,100%","translate(0,0)"),("50%","translate(-5px,-1px)")])+
 kf("ma-br",[("0%,100%","translate(0,0)"),("50%","translate(.4px,.3px)")])+
 regra("marejado","corpo","ma-corpo 2.4s ease-in-out infinite")+regra("marejado","oA","ma-oA 4s ease-out infinite alternate")+regra("marejado","oB","ma-oB 4.6s ease-out infinite alternate")+
 regra("marejado","pA","ma-p .3s linear infinite")+regra("marejado","pB","ma-p .34s linear -.1s infinite")+
 ".k.marejado .olE .nivel{animation:ma-nivel 1.1s ease-in-out infinite}.k.marejado .olD .nivel{animation:ma-nivel 1.4s ease-in-out -.5s infinite}\n"+
 regra("marejado","br","ma-br .18s linear infinite")))

# 4 CARREGANDO — círculos girando em sentidos opostos; orelhas giram devagar como antenas procurando sinal
spin=lambda cx:f'<circle cx="{cx}" cy="64" r="5" stroke="{D}" stroke-width="3" fill="none" stroke-linecap="round" stroke-dasharray="20 12"/>'
T.append(("carregando","Carregando","Cada olho vira um círculo de carregamento: um gira para um lado e o outro para o outro, em velocidades diferentes. As orelhas viram antenas procurando sinal, girando devagar e alternadas, e o corpo pulsa de leve. Para quando está esperando o Gemini ou rodando uma ferramenta.",
 spin(41),spin(59),"","",
 kf("ca-gira",[("to","rotate(360deg)")])+kf("ca-giraR",[("to","rotate(-360deg)")])+
 kf("ca-oA",[("0%,100%","rotate(-5deg)"),("50%","rotate(4deg)")])+kf("ca-oB",[("0%,100%","rotate(30deg)"),("50%","rotate(44deg)")])+
 kf("ca-p",[("0%,100%","rotate(-4deg)"),("50%","rotate(4deg)")])+kf("ca-corpo",[("0%,100%","scale(1)"),("50%","scale(1.015,.985)")])+
 regra("carregando","olE","ca-gira .9s linear infinite")+regra("carregando","olD","ca-giraR 1.2s linear infinite")+
 regra("carregando","oA","ca-oA 2.4s ease-in-out infinite")+regra("carregando","oB","ca-oB 2.4s ease-in-out -1.2s infinite")+
 regra("carregando","pA","ca-p 1.2s ease-in-out infinite")+regra("carregando","pB","ca-p 1.2s ease-in-out -.6s infinite")+regra("carregando","corpo","ca-corpo .9s ease-in-out infinite")))

# 5 IDEIA — aperta os olhos pensando, os olhos acendem, orelhas pulam uma depois da outra, corpo dá um pulinho
luz=lambda cx:f'<g class="esc"><ellipse class="oo" cx="{cx}" cy="64" rx="4.4" ry="6.6" fill="{D}"/><ellipse class="brl" cx="{cx+1.8}" cy="60.8" rx="1.7" ry="2" fill="#fff"/><rect class="lid" x="{cx-6}" y="50" width="12" height="7.6" fill="url(#pelo)"/></g><g class="luz"><circle cx="{cx}" cy="64" r="11" fill="url(#gLuz)"/><ellipse cx="{cx}" cy="64" rx="4.6" ry="6.8" fill="#FFE27A"/><ellipse cx="{cx+1.6}" cy="61" rx="1.6" ry="2" fill="#fff"/></g>'
T.append(("ideia","Ideia!","Os olhos funcionam como lâmpada: ele aperta os olhos pensando, os olhos acendem amarelos (o esquerdo primeiro, o direito logo depois) e voltam grandes e brilhantes. As orelhas pulam uma depois da outra e o corpo dá um pulinho de “achei!”.",
 luz(41),luz(59),"","",
 kf("id-lid",[("0%,8%","translateY(0)"),("16%,34%","translateY(4.6px)"),("40%,100%","translateY(-2px)")])+
 "@keyframes id-luz{0%,36%{opacity:0;transform:scale(.8)}40%{opacity:1;transform:scale(1.2)}54%{opacity:1;transform:scale(1)}60%,100%{opacity:0}}\n"+
 "@keyframes id-esc{0%,37%{opacity:1}39%,58%{opacity:0}62%,100%{opacity:1}}\n@keyframes id-brl{0%,55%{opacity:0}64%,100%{opacity:1}}\n"+
 kf("id-oo",[("0%,55%","scale(1)"),("64%","scale(1.22)"),("72%","scale(1.06)"),("100%","scale(1.1)")])+
 kf("id-oA",[("0%,38%","rotate(-2deg)"),("44%","rotate(-5deg) translateY(-3px)"),("52%","rotate(2deg)"),("60%","rotate(-1deg)"),("100%","rotate(0)")])+
 kf("id-oB",[("0%,42%","rotate(40deg)"),("48%","rotate(24deg) translateY(-3px)"),("56%","rotate(36deg)"),("64%","rotate(30deg)"),("100%","rotate(32deg)")])+
 kf("id-p",[("0%,40%","rotate(0)"),("48%","rotate(-6deg)"),("58%","rotate(4deg)"),("70%,100%","rotate(0)")])+
 kf("id-corpo",[("0%,10%","translateY(0)"),("20%,34%","scale(1.02,.97)"),("42%","translateY(-5px) scale(.97,1.05)"),("52%","translateY(0) scale(1.04,.95)"),("60%,100%","scale(1,1)")])+
 ".k.ideia .lid{animation:id-lid 3.2s ease-in-out infinite}.k.ideia .luz{transform-box:fill-box;transform-origin:center;animation:id-luz 3.2s ease-out infinite}.k.ideia .olD .luz{animation-delay:.08s}\n"+
 ".k.ideia .esc{animation:id-esc 3.2s linear infinite}.k.ideia .olD .esc{animation-delay:.08s}.k.ideia .brl{animation:id-brl 3.2s ease-out infinite}\n"+
 ".k.ideia .oo{transform-box:fill-box;transform-origin:center;animation:id-oo 3.2s ease-out infinite}\n"+
 regra("ideia","oA","id-oA 3.2s ease-out infinite")+regra("ideia","oB","id-oB 3.2s ease-out infinite")+regra("ideia","pA","id-p 3.2s ease-out infinite")+regra("ideia","pB","id-p 3.2s ease-out .1s infinite")+regra("ideia","corpo","id-corpo 3.2s ease-out infinite")))

# 6 PESQUISANDO — inclina para o lado da lupa; olho esquerdo aperta; uma orelha se inclina como quem escuta
T.append(("lupa","Pesquisando","Um olho normal que aperta de vez em quando e o outro aumentado por uma lupa que vasculha de um lado para o outro. O corpo se inclina na direção da lupa, uma orelha se dobra para a frente como quem está atento e a outra dá umas mexidinhas.",
 f'<ellipse cx="41" cy="64" rx="3.6" ry="5.4" fill="{D}"/>',
 f'<g class="lupa"><circle cx="59" cy="63" r="9.5" fill="#fff" fill-opacity=".35" stroke="#6C3EF4" stroke-width="2.4"/><path d="M65.8,69.8 L72,76" stroke="#6C3EF4" stroke-width="3.4" stroke-linecap="round"/><ellipse cx="59" cy="63" rx="5.6" ry="7.6" fill="{D}"/><circle cx="61" cy="59.5" r="1.8" fill="#fff"/></g>',"","",
 kf("lu-corpo",[("0%,100%","rotate(3deg)"),("50%","rotate(5deg) translateX(.6px)")])+
 kf("lu-lupa",[("0%,100%","translate(0,0)"),("25%","translate(-3px,1.5px)"),("55%","translate(1.5px,-1px)"),("80%","translate(-1px,2px)")])+
 kf("lu-olE",[("0%,70%,100%","scaleY(1)"),("78%,86%","scaleY(.45)")])+
 kf("lu-oA",[("0%,60%,100%","rotate(-1deg)"),("64%","rotate(-5deg)"),("68%","rotate(1deg)"),("72%","rotate(-3deg)")])+
 kf("lu-oB",[("0%,100%","rotate(44deg)"),("50%","rotate(50deg)")])+kf("lu-pB",[("0%,100%","rotate(6deg)"),("50%","rotate(12deg)")])+
 regra("lupa","corpo","lu-corpo 3s ease-in-out infinite")+regra("lupa","lupa","lu-lupa 2.6s ease-in-out infinite")+regra("lupa","olE","lu-olE 2.6s ease-in-out infinite")+
 regra("lupa","oA","lu-oA 2.2s ease-in-out infinite")+regra("lupa","oB","lu-oB 3s ease-in-out infinite")+regra("lupa","pB","lu-pB 3s ease-in-out -.5s infinite")))

# 7 CURTINDO SOM — dança: olhos saltam independentes no ritmo (um no tempo, outro no contratempo), orelhas também
BEAT=.5; CIC=6.0
def corpo_m(p):
    t=p*CIC; per=BEAT*4 if p<.6 else BEAT*2
    r=(3 if p<.6 else 5)*math.sin(2*math.pi*t/per)
    return f"rotate({r:.2f}deg)"
def olhos_m(p):
    t=p*CIC; b=BEAT if p<.6 else BEAT*.5; x=(t%b)/b
    sobe=math.sin(math.pi*min(1,x/.55))**1.5 if x<.55 else 0
    h=(2.4 if p<.6 else 3.2)*sobe; sq=1+(.12 if x>.55 and x<.7 else 0)
    return f"translateY({-h:.2f}px) scale({sq:.3f},{2-sq:.3f})"
def orelha_m(base,amp,fase):
    def f(p):
        t=p*CIC; b=BEAT if p<.6 else BEAT*.5
        return f"rotate({base+amp*math.sin(2*math.pi*t/(b*2)+fase):.2f}deg)"
    return f
def ponta_m(fase):
    def f(p):
        t=p*CIC; b=BEAT if p<.6 else BEAT*.5
        return f"rotate({3*math.sin(2*math.pi*t/(b*2)+fase-1.1):.2f}deg)"
    return f
olho_m=lambda cx,lado:(f'<g class="calmo"><path d="M{cx-4.6},65.6 Q{cx},59.4 {cx+4.6},65.6" stroke="{D}" stroke-width="3.2" fill="none" stroke-linecap="round"/></g>'
  f'<g class="forte"><clipPath id="cpB{lado}" clipPathUnits="userSpaceOnUse"><path d="{"M33,59 L48.6,64.4 L48.6,80 L33,80Z" if lado=="E" else "M51.4,64.4 L67,59 L67,80 L51.4,80Z"}"/></clipPath><ellipse clip-path="url(#cpB{lado})" cx="{cx}" cy="65" rx="4.6" ry="6.4" fill="{D}"/></g>')
T.append(("musica","Curtindo som","O corpo balança de um lado para o outro devagar, e os dois olhos, juntos, dão pulinhos no ritmo da música, num tempo próprio, separado do corpo. Na parte calma são olhinhos fechados de felicidade; na intensa os pulos ficam mais rápidos e ele faz cara de concentrado. As orelhas acompanham de leve. No PC, o ritmo e a intensidade vêm do som que está tocando.",
 olho_m(41,"E"),olho_m(59,"D"),"","",
 onda("mu-corpo",corpo_m,240)+onda("mu-olhos",olhos_m,480)+onda("mu-oA",orelha_m(-2,3,0),240)+onda("mu-oB",orelha_m(38,4,math.pi),240)+onda("mu-pA",ponta_m(0),240)+onda("mu-pB",ponta_m(math.pi),240)+
 "@keyframes mu-calmo{0%,58%{opacity:1}61%,98%{opacity:0}100%{opacity:1}}@keyframes mu-forte{0%,58%{opacity:0}61%,98%{opacity:1}100%{opacity:0}}\n"+
 ".k.musica .calmo{animation:mu-calmo 6s linear infinite}.k.musica .forte{animation:mu-forte 6s linear infinite}\n"+
 ".k.musica .olhos{transform-box:view-box;transform-origin:50px 70px;animation:mu-olhos 6s linear infinite}\n"+
 "".join(regra("musica",p,f"mu-{p} 6s linear infinite") for p in ["corpo","oA","oB","pA","pB"])))

# 8 FOMINHA — olhos pidões de fome olhando a barriga; corpo murcha e suspira; orelhas caídas dando tremidinhas
fome=lambda cx,id,lado:f'<clipPath id="{id}" clipPathUnits="userSpaceOnUse"><path d="{"M33,61.6 L48.6,57.2 L48.6,80 L33,80Z" if lado=="E" else "M51.4,57.2 L67,61.6 L67,80 L51.4,80Z"}"/></clipPath><g clip-path="url(#{id})"><ellipse cx="{cx}" cy="64" rx="5" ry="7.2" fill="{D}"/><ellipse cx="{cx+1.8}" cy="62.2" rx="1.8" ry="2.1" fill="#fff"/><circle cx="{cx-2}" cy="67.6" r=".9" fill="#fff"/></g>'
T.append(("cenoura","Fominha","Olhos pidões com a pálpebra caída para fora. De vez em quando olham para a barriga (cada olho com um pequeno atraso) e voltam para você enquanto sai um “ronc...”. O corpo murcha num suspiro e as orelhas baixam um pouco e dão tremidinhas de fraqueza.",
 fome(41,"cpF1","E"),fome(59,"cpF2","D"),"",
 '<text class="ronc" x="80" y="86" font-family="Fredoka,sans-serif" font-weight="600" font-size="7" fill="#FFD27A" stroke="#1B1530" stroke-width="2" paint-order="stroke">ronc...</text>',
 kf("fo-corpo",[("0%,100%","scale(1,1)"),("40%","scale(1.03,.95)"),("55%","scale(1.04,.94) translateY(.5px)"),("70%","scale(1,1)")])+
 kf("fo-olho",[("0%,55%,100%","translateY(0)"),("65%,82%","translateY(2.6px)")])+
 kf("fo-oA",[("0%,100%","rotate(-9deg)"),("50%","rotate(-11deg)"),("52%","rotate(-9deg)"),("54%","rotate(-12deg)")])+
 kf("fo-oB",[("0%,100%","rotate(54deg)"),("50%","rotate(58deg)"),("53%","rotate(55deg)"),("56%","rotate(59deg)")])+
 kf("fo-p",[("0%,100%","rotate(3deg)"),("50%","rotate(6deg)")])+
 "@keyframes ronc{0%,58%{opacity:0;transform:scale(.6)}66%{opacity:1;transform:translate(0,-2px) scale(1)}86%{opacity:1}100%{opacity:0;transform:translate(2px,-6px)}}.k.cenoura .ronc{transform-box:fill-box;transform-origin:left center;animation:ronc 3.2s ease-out infinite}\n"+
 regra("cenoura","corpo","fo-corpo 3.2s ease-in-out infinite")+regra("cenoura","olE","fo-olho 3.2s ease-in-out infinite")+regra("cenoura","olD","fo-olho 3.2s ease-in-out .12s infinite")+
 regra("cenoura","oA","fo-oA 3.2s ease-in-out infinite")+regra("cenoura","oB","fo-oB 2.6s ease-in-out infinite")+regra("cenoura","pA","fo-p 2s ease-in-out infinite")+regra("cenoura","pB","fo-p 2.4s ease-in-out -1s infinite")))

# 9 GLITCH — olhos falham em tempos diferentes; corpo e orelhas dão trancos digitais
gl=lambda x:f'<rect x="{x-4}" y="60" width="8" height="8" fill="#8FD3FF" transform="translate(-1.4 0)"/><rect x="{x-4}" y="60" width="8" height="8" fill="#FF6FA8" transform="translate(1.4 0)"/><rect x="{x-4}" y="60" width="8" height="8" fill="{D}"/>'
T.append(("glitch","Glitch","Os olhos viram quadradinhos que falham com um rastro colorido, cada um em um momento diferente. O corpo dá trancos digitais e as orelhas travam e pulam de posição, como um vídeo engasgando. Para erro de conexão, mais tech que o X.",
 gl(41),gl(59),"",'<rect class="corte" x="22" y="63" width="56" height="1.6" fill="#F4F0FF"/>',
 "@keyframes gl-olE{0%,82%,100%{transform:none}84%{transform:translate(2px,0) skewX(10deg)}87%{transform:translate(-2px,1px)}90%{transform:none}}\n"+
 "@keyframes gl-olD{0%,40%,100%{transform:none}42%{transform:translate(-2px,-1px) scale(1.2,.8)}45%{transform:translate(1.5px,0)}48%{transform:none}}\n"+
 "@keyframes gl-corpo{0%,82%,100%{transform:none}84%{transform:translateX(1.5px)}86%{transform:translateX(-2px) skewX(3deg)}88%{transform:none}}\n"+
 "@keyframes gl-oA{0%,40%{transform:rotate(-2deg)}42%,82%{transform:rotate(-8deg)}84%,100%{transform:rotate(-2deg)}}\n"+
 "@keyframes gl-oB{0%,60%{transform:rotate(38deg)}62%,84%{transform:rotate(50deg)}86%,100%{transform:rotate(38deg)}}\n"+
 "@keyframes gl-corte{0%,83%,100%{opacity:0}85%,89%{opacity:1}}.k.glitch .corte{animation:gl-corte 1.6s steps(1) infinite}\n"+
 regra("glitch","olE","gl-olE 1.6s steps(1) infinite")+regra("glitch","olD","gl-olD 1.9s steps(1) infinite")+regra("glitch","corpo","gl-corpo 1.6s steps(1) infinite")+
 regra("glitch","oA","gl-oA 1.9s steps(1) infinite")+regra("glitch","oB","gl-oB 1.6s steps(1) infinite")))

# 10 INDIFERENTE — olhar de lado lento; uma orelha dá uma mexida preguiçosa; corpo parado
T.append(("indiferente","Indiferente","Olhos em tracinho que piscam devagar e escorregam para o lado de vez em quando (cada um um tiquinho atrasado). O corpo fica quase parado, as orelhas meio murchas e só uma delas dá uma mexida preguiçosa de vez em quando. Para respostas secas: “ok... legal”.",
 f'<path d="M36,64 H46" stroke="{D}" stroke-width="3.2" stroke-linecap="round"/>',f'<path d="M54,64 H64" stroke="{D}" stroke-width="3.2" stroke-linecap="round"/>',"","",
 kf("in-olho",[("0%,30%,100%","translateX(0) scaleY(1)"),("40%,62%","translateX(2.4px)"),("80%","translateX(0) scaleY(1)"),("86%","scaleY(.2)"),("92%","scaleY(1)")])+
 kf("in-oA",[("0%,100%","rotate(-5deg)")])+kf("in-oB",[("0%,70%,100%","rotate(50deg)"),("76%","rotate(42deg)"),("82%","rotate(50deg)")])+
 kf("in-corpo",[("0%,100%","scale(1)"),("50%","scale(1.005,.995)")])+
 regra("indiferente","olE","in-olho 4s ease-in-out infinite")+regra("indiferente","olD","in-olho 4s ease-in-out .08s infinite")+
 regra("indiferente","oA","in-oA 4s infinite")+regra("indiferente","oB","in-oB 4s ease-in-out infinite")+regra("indiferente","corpo","in-corpo 4s ease-in-out infinite")))

# 11 ZEN — flutua respirando; orelhas sobem e descem espelhadas; olhos fechados respiram
T.append(("zen","Zen","Olhos fechados e tranquilos que respiram junto com o corpo. Ele flutua devagar com um brilho suave em volta, e as orelhas sobem e descem espelhadas, bem lentas, com as pontas acompanhando. Para Pomodoro e modo estudo.",
 f'<path d="M36,63 Q41,67.5 46,63" stroke="{D}" stroke-width="3" fill="none" stroke-linecap="round"/>',f'<path d="M54,63 Q59,67.5 64,63" stroke="{D}" stroke-width="3" fill="none" stroke-linecap="round"/>',"","",
 kf("ze-corpo",[("0%,100%","translateY(0) scale(1,1)"),("50%","translateY(-3px) scale(1.01,1.02)")])+
 kf("ze-oA",[("0%,100%","rotate(-2deg)"),("50%","rotate(-6deg)")])+kf("ze-oB",[("0%,100%","rotate(34deg)"),("50%","rotate(40deg)")])+
 kf("ze-p",[("0%,100%","rotate(-2deg)"),("50%","rotate(2deg)")])+kf("ze-olho",[("0%,100%","scaleX(1)"),("50%","scaleX(1.08)")])+
 regra("zen","corpo","ze-corpo 4s ease-in-out infinite")+regra("zen","oA","ze-oA 4s ease-in-out infinite")+regra("zen","oB","ze-oB 4s ease-in-out infinite")+
 regra("zen","pA","ze-p 4s ease-in-out -.6s infinite")+regra("zen","pB","ze-p 4s ease-in-out -2.6s infinite")+regra("zen","olE","ze-olho 4s ease-in-out infinite")+regra("zen","olD","ze-olho 4s ease-in-out infinite")))

# 12 PEGANDO FOGO — chamas tremulam independentes; orelhas em pé vibrando; corpo saltitando
chama=lambda x:f'<path d="M{x},71 C{x-5},71 {x-5.4},66 {x-3},63 C{x-2.6},65 {x-1.4},65.6 {x-.6},64.6 C{x-1.4},61.6 {x},58.6 {x+2.4},57.4 C{x+2},60.6 {x+5.4},62.6 {x+5},66.6 C{x+4.8},69.4 {x+2.8},71 {x},71Z" fill="#FF8A1F"/><path d="M{x},70.6 C{x-2},70.6 {x-2.2},68.4 {x-1},67 C{x-.4},68 {x+.6},67.6 {x+.6},66.2 C{x+2},67.6 {x+2.4},70.6 {x},70.6Z" fill="#FFE27A"/>'
T.append(("fogo","Pegando fogo","Os olhos viram chamas que tremulam cada uma no seu ritmo. As orelhas ficam em pé com uma vibração leve e o corpo saltita sem parar. Para quando ele fica empolgado ou determinado de verdade.",
 chama(41),chama(59),"","",
 kf("fg-ch",[("0%,100%","scale(1,1) skewX(0)"),("33%","scale(.92,1.1) skewX(-6deg)"),("66%","scale(1.05,.94) skewX(5deg)")])+
 kf("fg-oA",[("0%,100%","rotate(-2deg)"),("50%","rotate(1deg)")])+kf("fg-oB",[("0%,100%","rotate(30deg)"),("50%","rotate(33deg)")])+
 kf("fg-p",[("0%,100%","rotate(-2deg)"),("50%","rotate(2deg)")])+
 kf("fg-corpo",[("0%,100%","translateY(0) scale(1.03,.97)"),("50%","translateY(-3px) scale(.98,1.03)")])+
 ".k.fogo .olE,.k.fogo .olD{transform-box:fill-box;transform-origin:50% 100%}\n"+
 regra("fogo","olE","fg-ch .35s ease-in-out infinite")+regra("fogo","olD","fg-ch .29s ease-in-out -.12s infinite")+
 regra("fogo","oA","fg-oA .12s linear infinite")+regra("fogo","oB","fg-oB .14s linear infinite")+regra("fogo","pA","fg-p .2s linear infinite")+regra("fogo","pB","fg-p .22s linear -.1s infinite")+
 regra("fogo","corpo","fg-corpo .42s ease-in-out infinite")))

# 13 EXAUSTO — pálpebras pesadas fecham em tempos diferentes; cabeça cochila; orelhas moles e penduradas
exa=lambda cx,id:f'<clipPath id="{id}" clipPathUnits="userSpaceOnUse"><rect class="palp" x="{cx-7}" y="65" width="14" height="20"/></clipPath><g clip-path="url(#{id})"><ellipse cx="{cx}" cy="65.4" rx="4.2" ry="6" fill="{D}"/></g>'
T.append(("cansado","Exausto","Pálpebras pesadas: só a metade de baixo dos olhos aparece, e cada olho quase fecha num momento diferente. A cabeça cochila e volta, o corpo murcha e as orelhas baixam um pouco e balançam moles.",
 exa(41,"cpX1"),exa(59,"cpX2"),"","",
 kf("ex-palp",[("0%,70%,100%","translateY(0)"),("82%,88%","translateY(4.8px)")])+
 kf("ex-corpo",[("0%,100%","scale(1.03,.95) rotate(0)"),("60%","scale(1.04,.94) rotate(4deg) translateY(1px)"),("70%","scale(1.03,.95) rotate(-1deg)")])+
 kf("ex-oA",[("0%,100%","rotate(-12deg)"),("50%","rotate(-15deg)")])+kf("ex-oB",[("0%,100%","rotate(60deg)"),("50%","rotate(65deg)")])+
 kf("ex-p",[("0%,100%","rotate(5deg)"),("50%","rotate(9deg)")])+
 ".k.cansado .olE .palp{animation:ex-palp 3.4s ease-in-out infinite}.k.cansado .olD .palp{animation:ex-palp 3.4s ease-in-out .3s infinite}\n"+
 regra("cansado","corpo","ex-corpo 3.4s ease-in-out infinite")+regra("cansado","oA","ex-oA 3.4s ease-in-out infinite")+regra("cansado","oB","ex-oB 3.4s ease-in-out -.8s infinite")+
 regra("cansado","pA","ex-p 3.4s ease-in-out -.3s infinite")+regra("cansado","pB","ex-p 3.4s ease-in-out -1.4s infinite")))

def cabeca(k,olE,olD,atras,frente):
    return f'''<svg viewBox="0 -6 100 108" class="k {k}"><g class="corpo">
<g class="oA"><rect x="33.5" y="24" width="15" height="26" rx="7.5" fill="url(#pelo)"/><g class="pA"><rect x="33.5" y="6" width="15" height="28" rx="7.5" fill="url(#pelo)"/></g></g>
<g class="oB"><rect x="40" y="25" width="15" height="25" rx="7.5" fill="url(#pelo)"/><g class="pB"><rect x="40" y="8" width="15" height="27" rx="7.5" fill="url(#pelo)"/></g></g>
<path d="M50,36 C70,36 80,48 80,64 C80,80 66,88 50,88 C34,88 20,80 20,64 C20,48 30,36 50,36 Z" fill="url(#pelo)"/><path d="M43,38.5 Q49,40.5 54,45.5" stroke="#D3C6FB" stroke-width="3" stroke-linecap="round" fill="none"/>
{atras}<g class="olhos"><g class="olE">{olE}</g><g class="olD">{olD}</g></g>{frente}</g></svg>'''
css_k="".join(t[7] for t in T)
tiles="".join(f'<figure class="t">{cabeca(k,e,d,a,f)}<figcaption><b>{n}</b><span>{desc}</span></figcaption></figure>' for k,n,desc,e,d,a,f,_ in T)
html=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Olhos novos do Kadu</title>
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#F4F1FC;--card:#fff;--ink:#1B1530;--muted:#6E6890;--line:#E6E0F7;--desk:#1A1535}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#110E22;--card:#1B1733;--ink:#EEEAFB;--muted:#A79FC8;--line:#2E2852}}}}
:root[data-theme="dark"]{{--bg:#110E22;--card:#1B1733;--ink:#EEEAFB;--muted:#A79FC8;--line:#2E2852}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,system-ui,sans-serif;padding:24px 16px 40px}}
.wrap{{max-width:1080px;margin:0 auto}}
h1{{font:600 26px Fredoka,sans-serif;margin:0 0 4px}} p.sub{{margin:0 0 20px;color:var(--muted);max-width:72ch}}
.grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}}
.t{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;display:flex;flex-direction:column}}
.t svg{{display:block;width:100%;height:200px;background:radial-gradient(120% 100% at 30% 10%,#2A2352,var(--desk));padding:12px 0 4px;box-sizing:border-box;overflow:visible}}
figcaption{{padding:10px 14px 14px;display:flex;flex-direction:column;gap:3px}} figcaption b{{font:600 16px Fredoka,sans-serif}} figcaption span{{font-size:13px;color:var(--muted)}}
/* peças independentes: cada orelha (base e ponta), cada olho e o corpo */
.corpo{{transform-box:view-box;transform-origin:50px 88px}}
.oA{{transform-box:view-box;transform-origin:41px 46px;transform:rotate(0deg)}} .pA{{transform-box:view-box;transform-origin:41px 30px}}
.oB{{transform-box:view-box;transform-origin:47px 46px;transform:rotate(38deg)}} .pB{{transform-box:view-box;transform-origin:47.5px 31px}}
.olE,.olD,.br,.lupa{{transform-box:fill-box;transform-origin:center}}
.rio-b{{animation:rioB .5s linear infinite}} @keyframes rioB{{to{{stroke-dashoffset:-19}}}}
.pinga circle{{animation:pinga .7s ease-in infinite}} .pinga circle+circle{{animation-delay:-.35s}} @keyframes pinga{{0%{{opacity:0;transform:translateY(-2px)}}20%{{opacity:1}}100%{{opacity:0;transform:translateY(9px)}}}}
{css_k}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style></head><body><div class="wrap">
<h1>Olhos novos do Kadu</h1>
<p class="sub">13 expressões feitas só com os olhos, sem sobrancelha e no traço do Kadu. Orelhas perto da pose natural dele, com movimentos suaves (base e ponta separadas); olhos e corpo animados de forma independente. Escolha quais entram (ou todas) e eu coloco no Kadu.</p>
<svg width="0" height="0" style="position:absolute"><defs><radialGradient id="pelo" gradientUnits="userSpaceOnUse" cx="38" cy="40" r="56"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".62" stop-color="#F4F0FF"/><stop offset="1" stop-color="#DCD0FF"/></radialGradient>
<linearGradient id="gRio" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7CCBFF"/><stop offset=".5" stop-color="#4AA8FF"/><stop offset="1" stop-color="#2F86F0"/></linearGradient>
<clipPath id="cpCabeca" clipPathUnits="userSpaceOnUse"><path d="M50,36 C70,36 80,48 80,64 C80,80 66,88 50,88 C34,88 20,80 20,64 C20,48 30,36 50,36 Z"/></clipPath><radialGradient id="gLuz"><stop offset="0" stop-color="#FFF6C2"/><stop offset=".5" stop-color="#FFE27A" stop-opacity=".55"/><stop offset="1" stop-color="#FFE27A" stop-opacity="0"/></radialGradient></defs></svg>
<div class="grade">{tiles}</div></div></body></html>'''
open('kadu-olhos.html','w').write(html)
print(len(T))
