# Gera a versão para SITE do Kadu a partir da versão de produção (que por sua vez vem da prévia aprovada).
# Uso: python3 construir_site.py ../design/kadu-interacoes.html kadu.html
import pathlib, subprocess, sys, tempfile
AQUI = pathlib.Path(__file__).parent
ORIGEM, DESTINO = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
tmp = pathlib.Path(tempfile.mkdtemp()) / "prod.html"
subprocess.run([sys.executable, str(AQUI.parent / "web" / "construir.py"), str(ORIGEM), str(tmp)], check=True)
s = tmp.read_text(encoding="utf-8")

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:90], c)
    s = s.replace(a, b)

rep("<script>window.KADU_PROD=true;</script>\n<script>/*QWEBCHANNEL*/</script>", "<script>window.KADU_PROD=true;window.KADU_SITE=true;</script>")
# menu do site: só cuidar do bichinho + visual (nada de microfone, conversa, diário, ajustes do PC)
rep("const BTN=25,MARGEM=10;",
    "if(window.KADU_SITE){ITENS_MENU.length=0;ITENS_MENU.push(...ITENS_CUIDAR.filter(i=>i[0]!=='voltar'),['cartola','Visual',()=>abreBmenu('visual')])}\nconst BTN=25,MARGEM=10;")
# no site a tela não tem barra de tarefas: margem de baixo pequena
CSS = r"""
/* ===== versão site ===== */
#barraFala,#diario,#menuB,#pomo{display:none!important}
"""
i = s.index("</style>"); s = s[:i] + CSS + s[i:]

SITE = (AQUI / "ponte-site.js").read_text(encoding="utf-8")
rep("if(PROD&&window.qt&&window.QWebChannel){", SITE + "\nif(!window.KADU_SITE&&PROD&&window.qt&&window.QWebChannel){")
DESTINO.write_text(s, encoding="utf-8")
print("ok", DESTINO, len(s))
