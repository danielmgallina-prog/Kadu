"""Kadu de verdade: a mesma página da prévia aprovada, rodando numa janela transparente em tela cheia.

Como funciona
-------------
* A janela cobre a área útil da tela principal (sem a barra de tarefas), é transparente e fica por cima.
* A página (``kadu_pagina/kadu.html``) desenha o Kadu e todos os menus. Ela avisa quais retângulos
  recebem clique; fora deles o clique atravessa para a área de trabalho (Windows: WS_EX_TRANSPARENT).
* O mouse é mandado para a página mesmo quando o clique atravessa, para os olhos seguirem o cursor.
* Respostas do Gemini chegam pelo ``kadu_fala.json`` (``jarvis.kadu_ponte``); o estado do assistente
  pelo ``jarvis_state``; o log técnico e o progresso da abertura pelas linhas do daemon.
* Preferências (as mesmas do daemon, como ``saida``), bichinho, posição e diário ficam no kadu.json.

A interface usada pelo app continua a do rosto antigo: ``show()``, ``raise_()``, ``set_tray_menu()``,
``set_expression()`` e o atributo ``enviar_falar``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import QByteArray, QFile, QIODevice, QObject, QPoint, QRect, Qt, QTimer, QUrl, pyqtSlot
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QVBoxLayout, QWidget

from jarvis import kadu_ponte
from jarvis.activity import JarvisState, get_jarvis_state
from jarvis.debug import debug_log

try:  # o motor de página vem com o PyQt6-WebEngine
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEB_OK = True
except Exception as _exc:  # pragma: no cover - só acontece sem o WebEngine instalado
    WEB_OK = False
    _ERRO_WEB = _exc

PASTA = Path(__file__).with_name("kadu_pagina")
ESTADOS = {JarvisState.LISTENING: "ouvindo", JarvisState.THINKING: "pensando",
           JarvisState.DICTATION_PROCESSING: "pensando", JarvisState.SPEAKING: "falando",
           JarvisState.DICTATING: "ouvindo"}


def _cfg_dir() -> Path:
    try:
        from jarvis.config import get_config_path
        return Path(get_config_path()).parent
    except Exception:
        return Path.home() / ".config" / "jarvis"


def _le_json(p: Path, padrao):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _grava_json(p: Path, dados) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(p.parent), prefix=".kadu-", delete=False) as f:
            tmp = f.name
            json.dump(dados, f, ensure_ascii=False)
        os.replace(tmp, p)
        tmp = None
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass


# ------------------------------------------------------------------ ícone da bandeja (mini Kadu)
_OLHOS = {
    "neutro": '<ellipse cx="9.6" cy="15" rx="1.1" ry="1.6"/><ellipse cx="14.4" cy="15" rx="1.1" ry="1.6"/>',
    "ouvindo": '<circle cx="9.5" cy="14.8" r="1.7"/><circle cx="14.5" cy="14.8" r="1.7"/>',
    "surpreso": '<circle cx="9.5" cy="14.8" r="1.7"/><circle cx="14.5" cy="14.8" r="1.7"/>',
    "pensando": '<ellipse cx="10" cy="13.8" rx="1.1" ry="1.5"/><ellipse cx="14.8" cy="13.8" rx="1.1" ry="1.5"/>',
    "feliz": '<path d="M8.3 15.6q1.3-1.8 2.6 0M13.1 15.6q1.3-1.8 2.6 0" fill="none" stroke-width="1.4"/>',
    "triste": '<path d="M8.5 14.4h2.4v1.2a1.2 1.2 0 0 1-2.4 0z M13.1 14.4h2.4v1.2a1.2 1.2 0 0 1-2.4 0z" stroke-width=".6"/>',
    "bravo": '<path d="M8.4 14l2.6 1v1a1.3 1.3 0 0 1-2.6 0z M15.6 14l-2.6 1v1a1.3 1.3 0 0 0 2.6 0z" stroke-width=".5"/>',
    "dorme": '<path d="M8.4 15.2q1.2 1 2.4 0M13.2 15.2q1.2 1 2.4 0" fill="none" stroke-width="1.3"/>',
    "oculto": '<path d="M8.4 15.2q1.2 1 2.4 0M13.2 15.2q1.2 1 2.4 0" fill="none" stroke-width="1.3"/>',
    "tonto": '<path d="M8.6 14l2 2m0-2l-2 2M13.4 14l2 2m0-2l-2 2" fill="none" stroke-width="1.2"/>',
}
_SELOS = {"fome": "#FF8A1F", "mudo": "#E8435A", "foco": "#8E6BFF"}


def icone_kadu(cara: str = "neutro", selo: str = "") -> QIcon:
    try:
        from PyQt6.QtSvg import QSvgRenderer
    except Exception:
        return QIcon()
    olhos = _OLHOS.get(cara, _OLHOS["neutro"])
    orelhas = 'transform="rotate(14 12 13) translate(0 1)"' if cara in ("triste", "dorme", "oculto") else ""
    selo_svg = f'<circle cx="19.5" cy="19.5" r="4" fill="{_SELOS[selo]}" stroke="#0D0B1C" stroke-width="1.2"/>' if selo in _SELOS else ""
    opac = ' opacity=".55"' if cara == "oculto" else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g{opac}>
<g fill="#E9E2FF" {orelhas}><rect x="7.4" y="1" width="3.6" height="10" rx="1.8"/><rect x="12.4" y="1.2" width="3.6" height="9.6" rx="1.8" transform="rotate(22 14 10)"/></g>
<path d="M12 8.2c5 0 7.6 2.8 7.6 6.6S16.4 21 12 21s-7.6-2.4-7.6-6.2S7 8.2 12 8.2z" fill="#fff"/>
<g fill="#1B1530" stroke="#1B1530" stroke-linecap="round" stroke-linejoin="round">{olhos}</g></g>{selo_svg}</svg>'''
    r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    icone = QIcon()
    for tam in (16, 20, 24, 32, 48, 64):
        pm = QPixmap(tam, tam)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        r.render(p)
        p.end()
        icone.addPixmap(pm)
    return icone


# ------------------------------------------------------------------ Windows: clique-através, botões do mouse, Spotify
class _Win:
    def __init__(self):
        self.ok = sys.platform == "win32"
        if self.ok:
            import ctypes
            from ctypes import wintypes
            self.ct, self.wt = ctypes, wintypes
            self.u32 = ctypes.windll.user32

    def clique_atraves(self, hwnd: int, atravessa: bool) -> None:
        if not self.ok:
            return
        GWL_EXSTYLE, WS_EX_TRANSPARENT, WS_EX_LAYERED = -20, 0x20, 0x80000
        estilo = self.u32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED
        estilo = (estilo | WS_EX_TRANSPARENT) if atravessa else (estilo & ~WS_EX_TRANSPARENT)
        self.u32.SetWindowLongW(hwnd, GWL_EXSTYLE, estilo)

    def botao_apertado(self) -> bool:
        if not self.ok:
            return False
        return bool((self.u32.GetAsyncKeyState(0x01) & 0x8000) or (self.u32.GetAsyncKeyState(0x02) & 0x8000))

    def spotify_tocando(self) -> bool:
        """Spotify mostra "Artista - Música" no título da janela enquanto toca."""
        if not self.ok:
            return False
        try:
            import psutil
            pids = {p.pid for p in psutil.process_iter(["name"]) if (p.info.get("name") or "").lower() == "spotify.exe"}
        except Exception:
            return False
        if not pids:
            return False
        achou = [False]
        ct, wt, u32 = self.ct, self.wt, self.u32
        PROC = ct.WINFUNCTYPE(ct.c_bool, wt.HWND, wt.LPARAM)

        def cb(hwnd, _):
            if not u32.IsWindowVisible(hwnd):
                return True
            pid = wt.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ct.byref(pid))
            if pid.value in pids:
                n = u32.GetWindowTextLengthW(hwnd)
                if n:
                    buf = ct.create_unicode_buffer(n + 1)
                    u32.GetWindowTextW(hwnd, buf, n + 1)
                    if " - " in buf.value:
                        achou[0] = True
                        return False
            return True

        try:
            u32.EnumWindows(PROC(cb), 0)
        except Exception:
            return False
        return achou[0]


# ------------------------------------------------------------------ ponte página <-> Python
class Ponte(QObject):
    def __init__(self, janela: "KaduWindow"):
        super().__init__(janela)
        self.j = janela

    @pyqtSlot()
    def pronta(self):
        self.j._pagina_pronta()

    @pyqtSlot(str, str)
    def salvar(self, chave, valor):
        self.j._salvar(chave, valor)

    @pyqtSlot(str)
    def regioes(self, valor):
        try:
            d = json.loads(valor)
            self.j._regioes = [QRect(*r) for r in d.get("r", [])]
            self.j._captura_tudo = bool(d.get("tudo"))
            self.j._menus_abertos = bool(d.get("menus"))
            self.j._grande = bool(d.get("grande"))
            k = d.get("k")
            self.j._caixa_kadu = QRect(*k) if isinstance(k, list) and len(k) == 4 else None
        except Exception:
            pass

    @pyqtSlot(str, str)
    def icone(self, cara, selo):
        self.j._icone(cara, selo)

    @pyqtSlot(str)
    def falar(self, texto):
        if self.j.enviar_falar:
            self.j.enviar_falar(texto)

    @pyqtSlot(str)
    def perguntar(self, texto):
        self.j._perguntar(texto)

    @pyqtSlot()
    def alternarMic(self):
        if self.j.alternar_mic:
            self.j._mic_pedido = True
            self.j.alternar_mic()

    @pyqtSlot()
    def ouvir(self):
        if self.j.pedir_ouvir:
            self.j.pedir_ouvir()

    @pyqtSlot()
    def sair(self):
        self.j._js("kadu.salvarTudo()")
        if self.j.ao_sair:
            QTimer.singleShot(300, self.j.ao_sair)

    @pyqtSlot()
    def reiniciar(self):
        self.j._comeca_abertura()
        if self.j.reiniciar_assistente:
            self.j.reiniciar_assistente()

    @pyqtSlot()
    def menuClassico(self):
        if self.j._tray_menu is not None:
            self.j._tray_menu.popup(QCursor.pos())

    @pyqtSlot(bool)
    def iniciarComWindows(self, sim):
        self.j._iniciar_com_windows(bool(sim))

    @pyqtSlot()
    def foco(self):
        self.j._dar_foco()


# ------------------------------------------------------------------ adaptador para a "vida própria" (kadu_vida)
class _VidaAdapter(QObject):
    """Faz o kadu_vida (comentários, lembretes, reações a apps, tela cheia) conversar com a página."""

    def __init__(self, janela: "KaduWindow"):
        super().__init__(janela)
        self.j = janela
        self.oculto = True
        self.animando = False
        self.segurando = False
        self.balao_on = False
        self.estado = "esperando"
        self.emo_ate = 0.0

    @property
    def prefs(self):
        return {"modo": self.j._prefs.get("modo", "equilibrado")}

    def fala(self, texto, tipo="resposta", emocao="neutro", dur=None, falar=False):
        self.j._js(f"kadu.comenta({json.dumps(texto)},{json.dumps(tipo)},{json.dumps(emocao)})")


# ------------------------------------------------------------------ janela
class KaduWindow(QWidget):
    TICK_MS = 33

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kadu")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("background: transparent;")

        # ganchos que o app liga
        self.enviar_falar: Optional[Callable[[str], None]] = None
        self.enviar_pergunta: Optional[Callable[[str], bool]] = None
        self.alternar_mic: Optional[Callable[[], None]] = None
        self.pedir_ouvir: Optional[Callable[[], None]] = None
        self.ao_sair: Optional[Callable[[], None]] = None
        self.reiniciar_assistente: Optional[Callable[[], None]] = None
        self.definir_icone_bandeja: Optional[Callable[[QIcon], None]] = None
        self._tray_menu: Optional[QMenu] = None

        self._win = _Win()
        self._cfg = _cfg_dir() / "kadu.json"
        self._diario_arq = _cfg_dir() / "kadu_diario.json"
        self._prefs = _le_json(self._cfg, {})
        self._pronta = False
        self._fila_js: list[str] = []
        self._regioes: list[QRect] = []
        self._captura_tudo = False
        self._menus_abertos = False
        self._atravessa: Optional[bool] = None
        self._ult_mouse = QPoint(-1, -1)
        self._ult_mouse_t = 0.0
        self._botao_antes = False
        self._estado = None
        self._mic_pedido = False
        self._ultima_fala_id = (kadu_ponte.ler() or {}).get("id")
        self._ultimo_texto = ""
        self._grande = True
        self._caixa_kadu: Optional[QRect] = None
        self._off = QPoint(0, 0)
        # abertura
        self._abrindo = False
        self._abertura_t0 = 0.0
        self._passo = 0
        self._pronto = False
        self._erro = ""
        # monitores
        self._cpu_alta = 0
        self._ult_bateria = 0.0
        self._ult_cpu = 0.0
        self._musica = False
        self._tela_cheia = False

        self._ajusta_tela()
        if not WEB_OK:
            debug_log(f"kadu: WebEngine indisponível: {_ERRO_WEB}", "face")
            return

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.view.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.view.setStyleSheet("background: transparent;")
        st = self.view.settings()
        st.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        st.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        st.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        lay.addWidget(self.view)

        self.ponte = Ponte(self)
        self.canal = QWebChannel(self.view.page())
        self.canal.registerObject("ponte", self.ponte)
        self.view.page().setWebChannel(self.canal)
        self._carrega_pagina()

        self.vida_adapter = _VidaAdapter(self)
        try:
            from desktop_app import kadu_vida
            self.vida = kadu_vida.Vida(self.vida_adapter)
        except Exception as exc:
            self.vida = None
            debug_log(f"kadu: vida própria indisponível: {exc}", "face")

        self._tick = QTimer(self)
        self._tick.setInterval(self.TICK_MS)
        self._tick.timeout.connect(self._passo_rapido)
        self._lento = QTimer(self)
        self._lento.setInterval(1000)
        self._lento.timeout.connect(self._passo_lento)
        self._monitor = QTimer(self)
        self._monitor.setInterval(15000)
        self._monitor.timeout.connect(self._monitora_sistema)

    # ------------------------------------------------------------ página
    def _carrega_pagina(self):
        html = (PASTA / "kadu.html").read_text(encoding="utf-8")
        f = QFile(":/qtwebchannel/qwebchannel.js")
        js = ""
        if f.open(QIODevice.OpenModeFlag.ReadOnly):
            js = bytes(f.readAll()).decode("utf-8")
            f.close()
        html = html.replace("<script>/*QWEBCHANNEL*/</script>", "<script>" + js + "</script>")
        self.view.setHtml(html, QUrl.fromLocalFile(str(PASTA) + os.sep))

    def _js(self, codigo: str, fila: bool = True):
        if not WEB_OK:
            return
        if not self._pronta:
            if fila:
                self._fila_js.append(codigo)
            return
        self.view.page().runJavaScript(codigo)

    def _pagina_pronta(self):
        self._pronta = True
        dados = {
            "prefs": {k: self._prefs.get(k) for k in ("modo", "saida", "tamanho", "animacao", "windows") if k in self._prefs},
            "pet": self._prefs.get("pet"),
            "pos": self._prefs.get("pos_web"),
            "diario": _le_json(self._diario_arq, []),
        }
        a = self._area()
        self.view.page().runJavaScript(f"kadu.tela({a.width()},{a.height()})")
        self.view.page().runJavaScript(f"kadu.iniciar({json.dumps(json.dumps(dados, ensure_ascii=False))})")
        for c in self._fila_js:
            self.view.page().runJavaScript(c)
        self._fila_js.clear()
        if self._abrindo:
            self.view.page().runJavaScript("kadu.abrir()")
            if self._passo:
                self.view.page().runJavaScript(f"kadu.passo({self._passo},'')")
            if self._erro:
                self.view.page().runJavaScript(f"kadu.falhou({json.dumps(self._erro)})")
            elif self._pronto:
                self.view.page().runJavaScript("kadu.pronto('')")
        else:
            self.view.page().runJavaScript("kadu.mostrar()")

    # ------------------------------------------------------------ geometria
    def _area(self) -> QRect:
        tela = QGuiApplication.primaryScreen()
        return tela.availableGeometry() if tela is not None else QRect(0, 0, 1280, 720)

    def _ajusta_tela(self):
        """Começa em tela cheia; o laço rápido encolhe a janela em volta do Kadu quando dá."""
        self._janela_alvo(self._area(), QPoint(0, 0))
        if self._pronta:
            a = self._area()
            self._js(f"kadu.tela({a.width()},{a.height()})")

    def _janela_alvo(self, ret: QRect, off: QPoint):
        if ret != self.geometry():
            self.setGeometry(ret)
        if off != self._off:
            self._off = QPoint(off)
            self._js(f"kadu.offset({off.x()},{off.y()})", fila=False)

    # Janela pequena: renderizar uma janela transparente do tamanho da tela inteira, 60 vezes por
    # segundo, pesa muito no Windows. Quando o Kadu está só parado/falando, a janela fica do tamanho
    # dele + espaço para balão, leque e efeitos; ela volta a cobrir a tela para menus, diário,
    # arrastar, bolinha e abertura.
    MARGEM = (330, 340, 330, 70)   # esquerda, cima, direita, baixo

    def _encaixa_janela(self):
        a = self._area()
        k = self._caixa_kadu
        if self._grande or k is None or self._abrindo:
            self._janela_alvo(a, QPoint(0, 0))
            return
        atual = self.geometry()
        kg = k.translated(a.topLeft())          # caixa do Kadu em coordenadas da tela
        folga = atual.adjusted(150, 150, -150, -40)
        if atual != a and folga.contains(kg):   # ainda cabe bem na janela pequena atual
            return
        e, c, d, b = self.MARGEM
        ret = QRect(kg.x() - e, kg.y() - c, kg.width() + e + d, kg.height() + c + b).intersected(a)
        self._janela_alvo(ret, ret.topLeft() - a.topLeft())

    # ------------------------------------------------------------ interface antiga
    def set_tray_menu(self, menu: QMenu) -> None:
        self._tray_menu = menu

    def set_expression(self, *_):
        pass

    def show(self):
        self._ajusta_tela()
        super().show()
        if not WEB_OK:
            return
        if not self._tick.isActive():
            self._tick.start()
            self._lento.start()
            self._monitor.start()
            if self.vida:
                self.vida.iniciar()
        if not self._abrindo:
            self._js("kadu.mostrar()", fila=False)

    def raise_(self):
        super().raise_()

    def alternar(self):
        """Clique no ícone da bandeja: mostra/esconde o Kadu (com animação)."""
        if not self.isVisible():
            self.show()
            return
        self._js("kadu.alternar()", fila=False)

    def menu_bandeja(self, pos_global: QPoint):
        if not self.isVisible():
            super().show()
        x = pos_global.x() - self._area().x()
        y = pos_global.y() - self._area().y()
        self._dar_foco(True)  # tira o foco da janelinha de ícones escondidos do Windows, que então fecha
        self._js(f"kadu.menuBandeja({int(x)},{int(y)})")

    # ------------------------------------------------------------ ganchos do app
    def log_linha(self, linha: str):
        """Cada linha do log do assistente: vai para o diário técnico e move a abertura."""
        t = (linha or "").strip()
        if not t:
            return
        self._js(f"kadu.log({json.dumps(t[:400])})")
        if not self._abrindo or self._pronto:
            return
        if "daemon started" in t or "Jarvis daemon" in t:
            self._avanca(1, "Assistente iniciado")
        elif re.search(r"Whisper .*(loaded|ready)", t):
            m = re.search(r"Whisper '([^']+)' loaded on (\w+)", t)
            self._avanca(2, f"Reconhecimento de voz '{m.group(1)}' pronto ({m.group(2)})" if m else "Reconhecimento de voz pronto")
            self._avanca(3, "Voz pt-BR pronta")
        elif "Listening!" in t:
            self._avanca(3, "")
            self._fim_abertura(True)
        elif t.startswith("❌"):
            self._fim_abertura(False, t.lstrip("❌ ").strip())

    def daemon_iniciando(self):
        self._comeca_abertura()

    def daemon_parou(self, inesperado: bool = True):
        if inesperado:
            if self._abrindo and not self._pronto:
                self._fim_abertura(False, "O assistente parou durante a abertura")
            else:
                self._js("kadu.falhou('O assistente parou. Clique com o botão direito no ícone para ligar de novo.')")

    def chat_evento(self, linha: str):
        """Eventos do chat (perguntas digitadas): garante que o Kadu nunca fica preso pensando."""
        try:
            from jarvis.daemon import CHAT_IPC_PREFIX
            if not linha.startswith(CHAT_IPC_PREFIX):
                return
            d = json.loads(linha[len(CHAT_IPC_PREFIX):])
        except Exception:
            return
        tipo, dados = d.get("type"), d.get("data")
        if tipo == "busy":
            self._js("kadu.falhou('Calma, ainda tô respondendo a pergunta anterior. Tenta de novo já já.')")
        elif tipo == "complete":
            if isinstance(dados, str) and dados.strip():
                texto = dados.strip()
                # normalmente a resposta já chegou pelo kadu_fala.json; se não chegou, mostra agora
                QTimer.singleShot(900, lambda: None if texto == self._ultimo_texto else
                                  self._js(f"kadu.resposta({json.dumps(texto)},'neutro','chat')"))
            else:
                self._js("kadu.falhou('Não consegui responder agora. Tenta perguntar de novo?')")

    def definir_mic(self, pausado: bool):
        self._js(f"kadu.mic({'true' if pausado else 'false'},{'true' if self._mic_pedido else 'false'})")
        self._mic_pedido = False

    def _comeca_abertura(self):
        self._abrindo, self._pronto, self._erro, self._passo = True, False, "", 0
        self._abertura_t0 = time.monotonic()
        self._js("kadu.abrir()", fila=False)

    def _avanca(self, n: int, sub: str):
        if n <= self._passo:
            return
        self._passo = n
        self._js(f"kadu.passo({n},{json.dumps(sub)})")

    def _fim_abertura(self, ok: bool, msg: str = ""):
        if not self._abrindo:
            return
        self._abrindo = False
        if ok:
            self._pronto = True
            self._js(f"kadu.pronto({json.dumps(f'Pronto em {int(time.monotonic() - self._abertura_t0)} s')})")
        else:
            self._erro = msg or "O assistente não conseguiu iniciar"
            self._js(f"kadu.falhou({json.dumps(self._erro)})")

    # ------------------------------------------------------------ salvar
    def _salvar(self, chave: str, valor: str):
        try:
            dados = json.loads(valor)
        except ValueError:
            return
        if chave == "diario":
            _grava_json(self._diario_arq, dados)
            return
        atual = _le_json(self._cfg, {})
        if chave == "prefs" and isinstance(dados, dict):
            atual.update({k: v for k, v in dados.items() if v is not None})
        elif chave == "pet":
            atual["pet"] = dados
        elif chave == "pos":
            atual["pos_web"] = dados
        else:
            return
        self._prefs = atual
        _grava_json(self._cfg, atual)

    def _iniciar_com_windows(self, sim: bool):
        if sys.platform != "win32":
            return
        try:
            pasta = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            atalho = pasta / "Kadu.vbs"
            lancador = Path.home() / "GIT" / "kadu" / "Kadu.vbs"
            if sim and lancador.exists():
                atalho.write_text(f'CreateObject("WScript.Shell").Run """{lancador}""", 0, False\r\n', encoding="utf-8")
            elif not sim and atalho.exists():
                atalho.unlink()
        except Exception as exc:
            debug_log(f"kadu: iniciar com o Windows falhou ({type(exc).__name__})", "face")

    # ------------------------------------------------------------ pergunta digitada
    def _perguntar(self, texto: str):
        ok = False
        if self.enviar_pergunta:
            try:
                ok = bool(self.enviar_pergunta(texto))
            except Exception:
                ok = False
        if not ok:
            self._js("kadu.falhou('O assistente está desligado agora. Liga ele no menu do ícone e tenta de novo.')")

    def _dar_foco(self, forcar: bool = False):
        # o clique do usuário já ativa a janela; só forçamos a ativação quando vem do ícone da bandeja
        if forcar:
            self.activateWindow()
        if WEB_OK:
            self.view.setFocus()

    def _icone(self, cara: str, selo: str):
        if self.definir_icone_bandeja:
            try:
                self.definir_icone_bandeja(icone_kadu(cara, selo))
            except Exception as exc:
                debug_log(f"kadu: ícone da bandeja falhou ({type(exc).__name__})", "face")

    # ------------------------------------------------------------ laços
    def _passo_rapido(self):
        if not self.isVisible():
            return
        if self._pronta:
            self._encaixa_janela()
        g = QCursor.pos()
        p = g - self.geometry().topLeft()
        dentro = self._captura_tudo or any(r.contains(p) for r in self._regioes)
        atravessa = not dentro
        if atravessa != self._atravessa:
            self._atravessa = atravessa
            try:
                self._win.clique_atraves(int(self.winId()), atravessa)
            except Exception as exc:
                debug_log(f"kadu: clique-através falhou: {exc}", "face")
        agora = time.monotonic()
        if atravessa and p != self._ult_mouse and agora - self._ult_mouse_t > 0.05:
            self._ult_mouse, self._ult_mouse_t = QPoint(p), agora
            m = g - self._area().topLeft()   # o mouse vai em coordenadas da tela inteira
            self._js(f"kadu.mouse({m.x()},{m.y()})")
        # clique fora com menu aberto: fecha os menus
        apertado = self._win.botao_apertado()
        if apertado and not self._botao_antes and atravessa and self._menus_abertos:
            self._js("kadu.foraClique()")
        self._botao_antes = apertado
        # estado do assistente
        try:
            st = get_jarvis_state().state
        except Exception:
            st = JarvisState.IDLE
        novo = ESTADOS.get(st, "esperando")
        if novo != self._estado:
            self._estado = novo
            self._js(f"kadu.estado('{novo}')")
        # resposta nova do Gemini (ou a pergunta que ele ouviu)
        dados = kadu_ponte.ler()
        if dados and dados.get("id") != self._ultima_fala_id:
            self._ultima_fala_id = dados.get("id")
            if dados.get("origem") != "usuario":
                self._ultimo_texto = (dados.get("texto") or "").strip()
            self._js(f"kadu.resposta({json.dumps(dados.get('texto', ''))},{json.dumps(dados.get('emocao', 'neutro'))},{json.dumps(dados.get('origem', 'resposta'))})")

    def _passo_lento(self):
        if not self.isVisible() or not self._pronta:
            return
        # a vida própria precisa saber se o Kadu está livre para falar
        self.view.page().runJavaScript("kadu.podeFalar()", self._pode_falar)
        if self.vida and self.vida.tela_cheia != self._tela_cheia:
            self._tela_cheia = self.vida.tela_cheia
            self._js(f"kadu.telaCheia({'true' if self._tela_cheia else 'false'})")
        # abertura que travou: depois de 4 min mostra o Kadu mesmo assim
        if self._abrindo and time.monotonic() - self._abertura_t0 > 240:
            self._fim_abertura(True)
        # Spotify tocando -> curtindo som
        if int(time.monotonic()) % 15 == 0:
            tocando = self._win.spotify_tocando()
            if tocando != self._musica:
                self._musica = tocando
                self._js(f"kadu.musica({'true' if tocando else 'false'})")

    def _pode_falar(self, pode):
        a = self.vida_adapter
        a.oculto = not bool(pode)

    def _monitora_sistema(self):
        try:
            import psutil
        except Exception:
            return
        agora = time.monotonic()
        try:
            bat = psutil.sensors_battery()
            if bat and not bat.power_plugged and bat.percent <= 15 and agora - self._ult_bateria > 1800:
                self._ult_bateria = agora
                self._js("kadu.sistema('bateria')")
        except Exception:
            pass
        try:
            uso = psutil.cpu_percent(interval=None)
            self._cpu_alta = self._cpu_alta + 1 if uso >= 90 else 0
            if self._cpu_alta >= 3 and agora - self._ult_cpu > 1200:
                self._ult_cpu = agora
                self._cpu_alta = 0
                self._js("kadu.sistema('cpu')")
        except Exception:
            pass

    def closeEvent(self, ev):
        self._js("kadu.salvarTudo()")
        super().closeEvent(ev)
