"""Kadu: o coelhinho animado que substitui o rosto do Jarvis.

Uma janela pequena, transparente e sempre por cima, que anda junto com o Kadu.
Tudo é desenhado com QPainter nas mesmas coordenadas do desenho original
(viewBox -10 -14 120 126), então as formas batem com a prévia aprovada.

Entradas:
* estado do assistente (arquivo ``jarvis_state``): ouvindo, pensando, falando;
* última fala (``kadu_ponte``): texto do balão + emoção;
* mouse: olhar, segurar, arrastar, chacoalhar.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QPoint, pyqtSignal
from PyQt6.QtGui import (QAction, QActionGroup, QBrush, QColor, QCursor, QFont, QFontMetricsF,
                         QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient)
from PyQt6.QtWidgets import QApplication, QMenu, QWidget

from jarvis.activity import JarvisState, get_jarvis_state
from jarvis.debug import debug_log
from jarvis import kadu_ponte
from desktop_app import kadu_vida
from desktop_app.themes import apply_theme

# ---------------------------------------------------------------- cores
INK = QColor("#1B1530")
PELO_LUZ, PELO_MEIO, PELO_SOMBRA = QColor("#FFFFFF"), QColor("#FAF8FF"), QColor("#D3C6FB")
ROXO = QColor("#6C3EF4")
AURA = QColor("#8E6BFF")
LAGRIMA = QColor("#5AA9FF")
TERRA, TERRA_LUZ = QColor("#3B2F70"), QColor("#6E5CB8")
CARTOLA, CARTOLA_ABA, CARTOLA_FAIXA = QColor("#241C45"), QColor("#3A2F6B"), QColor("#6C3EF4")
BURACO, BURACO_BORDA = QColor("#0B0918"), QColor("#5B4A9B")

TAMANHOS = {"P": 100, "M": 150, "G": 200}
ANIMACOES = ("toca", "cartola", "pulinhos", "cavando")
MODOS = ("foco", "equilibrado", "falante")
SAIDAS = ("voz_balao", "voz", "balao")

# ea/eb: orelhas | olho: formato | lid: [cobertura esq, inclinação esq, cobertura dir, inclinação dir]
EXP = {
    "neutro":     dict(ea=0,   eb=38, olho="oval",     dy=0),
    "feliz":      dict(ea=-3,  eb=30, olho="feliz",    dy=-1),
    "animado":    dict(ea=-4,  eb=22, olho="estrela",  dy=-1, pula=1),
    "encantado":  dict(ea=-2,  eb=20, olho="estrela",  dy=-2),
    "apaixonado": dict(ea=-6,  eb=30, olho="coracao",  dy=-1, flutua=1),
    "piada":      dict(ea=-8,  eb=46, olho="pisca",    dy=0,  tilt=7, ri=1),
    "zoando":     dict(ea=-10, eb=52, olho="oval",     dy=0,  tilt=6, lid=(.46, -.25, .46, -.25), gaze=(1.6, -.6)),
    "surpreso":   dict(ea=2,   eb=12, olho="grande",   dy=-2),
    "desconfiado": dict(ea=-6, eb=58, olho="oval",     dy=0,  tilt=-5, lid=(.42, .3, .58, .3), gaze=(2.6, .3)),
    "tedio":      dict(ea=-20, eb=80, olho="oval",     dy=2,  lid=(.52, 0, .52, 0), gaze=(0, 1.4)),
    "bravo":      dict(ea=-18, eb=72, olho="oval",     dy=1,  treme=1, lid=(.24, 1, .24, 1)),
    "triste":     dict(ea=-30, eb=86, olho="oval",     dy=3,  lid=(.2, -1, .2, -1), olhoDy=1.6, gaze=(0, 1)),
    "chorando":   dict(ea=-32, eb=90, olho="oval",     dy=3,  lid=(.16, -1, .16, -1), chora=1, olhoGrande=1, brilho=1),
    "tonto":      dict(ea=-14, eb=64, olho="espiral",  dy=1,  balanca=1),
    "erro":       dict(ea=-26, eb=84, olho="x",        dy=2),
    "ouvindo":    dict(ea=-2,  eb=18, olho="grande",   dy=-1),
    "pensando":   dict(ea=-3,  eb=56, olho="oval",     dy=0,  gaze=(2.6, -2.4), tilt=-4),
    "segurado":   dict(ea=-22, eb=66, olho="apertado", dy=2),
    "sono":       dict(ea=-14, eb=62, olho="sono",     dy=2),
}

ROTULOS = {"resposta": ("Kadu", ROXO), "espontaneo": ("Comentário", QColor("#D96A00")),
           "lembrete": ("Lembrete", QColor("#0E9670")), "reacao": ("Kadu", QColor("#B23A9A")),
           "erro": ("Ops", QColor("#C0392B"))}


# ---------------------------------------------------------------- utilidades
def lim(x, m):
    return max(-m, min(m, x))


def ap(a, b, k):
    return a + (b - a) * min(1.0, k)


def seg(p, a, b):
    return max(0.0, min(1.0, (p - a) / (b - a)))


def mola(x, v, alvo, k, c, forca, dt):
    v += (k * (alvo - x) - c * v + forca) * dt
    return x + v * dt, v


class Ease:
    out = staticmethod(lambda p: 1 - (1 - p) ** 3)
    inn = staticmethod(lambda p: p ** 3)
    inout = staticmethod(lambda p: 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2)

    @staticmethod
    def back(p):
        c = 1.9
        return 1 + (c + 1) * (p - 1) ** 3 + c * (p - 1) ** 2

    @staticmethod
    def bounce(p):
        n, d = 7.5625, 2.75
        if p < 1 / d:
            return n * p * p
        if p < 2 / d:
            p -= 1.5 / d
            return n * p * p + .75
        if p < 2.5 / d:
            p -= 2.25 / d
            return n * p * p + .9375
        p -= 2.625 / d
        return n * p * p + .984375


def _caminho_estrela(cx, cy, R, r):
    p = QPainterPath()
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        q = r if i % 2 else R
        pt = QPointF(cx + math.cos(a) * q, cy + math.sin(a) * q)
        p.moveTo(pt) if i == 0 else p.lineTo(pt)
    p.closeSubpath()
    return p


def _caminho_espiral(cx, cy, lado):
    p = QPainterPath()
    for i in range(41):
        a, q = i * .3 * lado, .3 + i * .14
        pt = QPointF(cx + math.cos(a) * q, cy + math.sin(a) * q)
        p.moveTo(pt) if i == 0 else p.lineTo(pt)
    return p


def glifo(tipo: str, lado: int):
    """Olho desenhado em volta do centro. Retorna (caminho, preenchido, espessura) ou None = oval."""
    cx, cy, m = (41 if lado < 0 else 59), 64, lado
    p = QPainterPath()
    if tipo == "feliz":
        p.moveTo(cx - 4.5, cy + 2); p.quadTo(cx, cy - 4.5, cx + 4.5, cy + 2); return p, False, 3.2
    if tipo == "pisca":
        if lado > 0:
            return None
        p.moveTo(cx - 4.5, cy + 1); p.quadTo(cx, cy - 4, cx + 4.5, cy + 1); return p, False, 3.2
    if tipo == "apertado":
        p.moveTo(cx + 3.6 * m, cy - 4.5); p.lineTo(cx - 3.6 * m, cy); p.lineTo(cx + 3.6 * m, cy + 4.5); return p, False, 3.2
    if tipo == "sono":
        p.moveTo(cx - 4.5, cy + 1); p.quadTo(cx, cy + 4, cx + 4.5, cy + 1); return p, False, 3.2
    if tipo == "estrela":
        return _caminho_estrela(cx, cy, 6.4, 2.8), True, 0
    if tipo == "coracao":
        p.moveTo(cx, cy + 5)
        p.cubicTo(cx - 7.5, cy, cx - 5, cy - 6.5, cx, cy - 2.8)
        p.cubicTo(cx + 5, cy - 6.5, cx + 7.5, cy, cx, cy + 5)
        p.closeSubpath(); return p, True, 0
    if tipo == "x":
        p.moveTo(cx - 3.4, cy - 3.4); p.lineTo(cx + 3.4, cy + 3.4)
        p.moveTo(cx + 3.4, cy - 3.4); p.lineTo(cx - 3.4, cy + 3.4); return p, False, 3.2
    if tipo == "espiral":
        return _caminho_espiral(cx, cy, lado), False, 1.9
    return None


def _cfg_path() -> Path:
    try:
        from jarvis.config import get_config_path
        return Path(get_config_path()).parent / "kadu.json"
    except Exception:
        return Path.home() / ".config" / "jarvis" / "kadu.json"


# ================================================================ janela
class KaduWindow(QWidget):
    """Janela do Kadu. Mantém a mesma interface usada pelo app: show(), raise_(), set_tray_menu()."""

    estado_observado = pyqtSignal(str)
    FPS_MS = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kadu")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self._tray_menu: Optional[QMenu] = None

        # preferências
        self.prefs = {"modo": "equilibrado", "tamanho": "M", "animacao": "aleatoria", "saida": "voz_balao", "pos": None}
        self.enviar_falar = None   # o app liga aqui o canal que faz o assistente falar
        self._carrega_prefs()
        self.kw = float(TAMANHOS.get(self.prefs["tamanho"], 150))

        # estado do assistente / fala
        self._state_manager = get_jarvis_state()
        self.estado = "esperando"
        self._ultima_fala_id = None
        try:
            atual = kadu_ponte.ler()
            self._ultima_fala_id = atual.get("id") if atual else None
        except Exception:
            pass
        self._checa_fala_em = 0.0

        # balão
        self.balao_txt, self.balao_tipo, self.balao_vis = "", "resposta", 0.0
        self.balao_ini, self.balao_ate, self.balao_on = 0.0, 0.0, False
        self.balao_vel = 0.03
        self.falando = False
        self.emo_fala: Optional[str] = None
        self.emo_ate = 0.0

        # física
        self.F = dict(a=0.0, aV=0.0, b=38.0, bV=0.0, bal=0.0, balV=0.0, abre=0.0, abreV=0.0, pt=0.0, ptV=0.0,
                      tilt=0.0, tiltV=0.0, sy=1.0, syV=0.0, y=0.0, yV=0.0, gx=0.0, gy=0.0,
                      vx=0.0, vy=0.0, ax=0.0, ay=0.0)
        self.sm = dict(ovE=1.0, ovD=1.0, lag=0.0, br=0.0, lhE=0.0, liE=0.0, lhD=0.0, liD=0.0,
                       rx=4.0, ry=6.2, olhoDy=0.0, aura=0.0)
        self._ult_pos: Optional[QPointF] = None
        self._t0 = time.monotonic()
        self._ult_t = self._t0
        self.prox_pisca = self._t0 + 2.5
        self.piscou_em = -99.0
        self.pisca_dupla = False
        self.troca_olhar = 0.0
        self.alvo_olhar = (0.0, 0.0)
        self.prox_tremida = self._t0 + 4
        self.giro = {"E": 0.0, "D": 0.0}
        self.ult_interacao = self._t0
        self.sono = 0.0
        self.surpresa_ate = 0.0

        # mouse
        self.segurando = False
        self.arrastou = False
        self._press_global: Optional[QPoint] = None
        self._press_win: Optional[QPoint] = None
        self.tontura = 0.0
        self.sinal_vx = 0
        self.ult_virada = 0.0
        self.tonto_ate = 0.0
        self.reclamou_tonto = True

        # entrar / sair
        self.animando: Optional[dict] = None
        self.oculto = True
        self.fx = dict(anim_y=0.0, anim_sx=1.0, anim_sy=1.0, anim_rot=0.0, clip=None,
                       buraco=0.0, chapeu=0.0, chapeu_y=0.0, chapeu_rot=0.0, monte=0.0, monte_x=0.0,
                       visivel=1.0, sombra=1.0)
        self.ult_pulo = -1

        # tamanho animado
        self._tam_anim: Optional[tuple] = None

        # vida própria (comentários, lembretes, reações, tela cheia)
        self.vida = kadu_vida.Vida(self)

        self._timer = QTimer(self)
        self._timer.setInterval(self.FPS_MS)
        self._timer.timeout.connect(self._quadro)
        self._ajusta_geometria(inicial=True)

    # ------------------------------------------------------------ preferências
    def _carrega_prefs(self):
        try:
            dados = json.loads(_cfg_path().read_text(encoding="utf-8"))
            if isinstance(dados, dict):
                self.prefs.update({k: v for k, v in dados.items() if k in self.prefs})
        except Exception:
            pass
        if self.prefs["modo"] not in MODOS:
            self.prefs["modo"] = "equilibrado"
        if self.prefs["tamanho"] not in TAMANHOS:
            self.prefs["tamanho"] = "M"
        if self.prefs["saida"] not in SAIDAS:
            self.prefs["saida"] = "voz_balao"

    def _salva_prefs(self):
        try:
            caminho = _cfg_path()
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(json.dumps(self.prefs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            debug_log(f"kadu: não salvou preferências: {exc}", "face")

    @property
    def modo(self) -> str:
        return self.vida.modo_efetivo()

    # ------------------------------------------------------------ geometria
    # A janela tem espaço para o balão em cima e para pulos; o Kadu fica embaixo, no centro.
    def _dims(self, kw=None):
        kw = kw or self.kw
        kh = kw * 170 / 150
        larg = max(300.0, kw + 170)
        alt = kh + 170
        return kw, kh, larg, alt

    def _kadu_rect(self) -> QRectF:
        kw, kh, larg, alt = self._dims()
        return QRectF((larg - kw) / 2, alt - kh - 6, kw, kh)

    def _escala(self):
        return self.kw / 120.0

    def ancora_global(self) -> QPointF:
        """Ponto do 'chão' do Kadu na tela (centro da base)."""
        r = self._kadu_rect()
        return QPointF(self.x() + r.center().x(), self.y() + r.bottom())

    def _ajusta_geometria(self, inicial=False, ancora: Optional[QPointF] = None):
        kw, kh, larg, alt = self._dims()
        if inicial:
            tela = (QApplication.primaryScreen().availableGeometry() if QApplication.primaryScreen() else None)
            if self.prefs.get("pos") and isinstance(self.prefs["pos"], list):
                ax, ay = self.prefs["pos"]
            elif tela is not None:
                ax, ay = tela.right() - kw / 2 - 40, tela.bottom() - 30
            else:
                ax, ay = 800, 600
            ancora = QPointF(ax, ay)
        if ancora is None:
            ancora = self.ancora_global()
        self.resize(int(larg), int(alt))
        r = self._kadu_rect()
        self.move(int(ancora.x() - r.center().x()), int(ancora.y() - r.bottom()))
        self._limita_na_tela()

    def _limita_na_tela(self):
        tela = self.screen().availableGeometry() if self.screen() else None
        if tela is None:
            return
        r = self._kadu_rect()
        x = min(max(self.x(), tela.left() - int(r.left())), tela.right() - int(r.right()))
        y = min(max(self.y(), tela.top() - int(r.top()) + 40), tela.bottom() - int(r.bottom()))
        if (x, y) != (self.x(), self.y()):
            self.move(x, y)

    # ------------------------------------------------------------ interface usada pelo app
    def set_tray_menu(self, menu: QMenu) -> None:
        self._tray_menu = menu

    def set_expression(self, *_):  # compatibilidade com o rosto antigo
        pass

    def show(self):
        if self.isVisible() and not self.oculto:
            return
        super().show()
        self.oculto = False
        self._t0 = self._ult_t = time.monotonic()
        self._ult_pos = None
        self._timer.start()
        self.vida.iniciar()
        self._inicia_anim(self._escolhe_anim(), entrando=True)

    def esconder(self):
        if self.oculto or self.animando:
            return
        self.fecha_balao()
        self._inicia_anim(self._escolhe_anim(), entrando=False)

    def _escolhe_anim(self):
        a = self.prefs.get("animacao", "aleatoria")
        return a if a in ANIMACOES else random.choice(ANIMACOES)

    # ------------------------------------------------------------ fala / balão
    def fala(self, texto: str, tipo="resposta", emocao="neutro", dur=None, falar=False):
        """Mostra a fala do Kadu conforme a saída escolhida.

        falar=True: frase do próprio Kadu (comentário, lembrete, reação), que ele pede para a voz falar.
        Respostas do assistente chegam com falar=False, porque a voz delas já é tratada no assistente.
        """
        texto = (texto or "").strip()
        if not texto or self.oculto:
            return
        saida = self.prefs.get("saida", "voz_balao")
        com_voz, com_balao = saida in ("voz_balao", "voz"), saida in ("voz_balao", "balao")
        if falar and com_voz and self.enviar_falar is not None:
            try:
                self.enviar_falar(texto)
            except Exception as exc:
                debug_log(f"kadu: falha ao pedir fala: {exc}", "face")
        agora = time.monotonic()
        self.emo_fala = emocao if emocao in EXP else "neutro"
        if com_balao:
            if len(texto) > 240:
                texto = texto[:240].rsplit(" ", 1)[0] + "…"
            self.balao_txt, self.balao_tipo = texto, tipo
            self.balao_ini = agora
            self.balao_vel = min(.032, 2.4 / max(1, len(texto)))   # digita em no máximo ~2,4 s
            dur = dur if dur is not None else min(14.0, 3.0 + len(texto) * .055)
            self.balao_ate = agora + len(texto) * self.balao_vel + dur
            self.balao_on = True
            self.emo_ate = self.balao_ate
        else:
            # só voz: a expressão acompanha a fala (é estendida enquanto o assistente está falando)
            self.balao_on = False
            self.emo_ate = agora + (dur if dur is not None else min(12.0, 2.5 + len(texto) * .06))
        self.ult_interacao = agora
        if self.emo_fala == "surpreso":
            self.F["syV"] -= 3
        elif self.emo_fala == "animado":
            self.F["syV"] -= 2

    def fecha_balao(self):
        self.balao_on = False
        self.falando = False

    def _checa_fala_nova(self, agora):
        if agora < self._checa_fala_em:
            return
        self._checa_fala_em = agora + .15
        dados = kadu_ponte.ler()
        if not dados or dados.get("id") == self._ultima_fala_id:
            return
        self._ultima_fala_id = dados.get("id")
        origem = dados.get("origem", "resposta")
        if origem == "usuario":  # a pergunta só vai para o diário do Kadu novo
            return
        self.fala(dados.get("texto", ""), "erro" if dados.get("emocao") == "erro" else origem,
                  dados.get("emocao", "neutro"), falar=False)

    # ------------------------------------------------------------ expressão atual
    def _expressao(self, agora) -> str:
        if agora < self.tonto_ate:
            return "tonto"
        if self.segurando:
            return "segurado"
        if agora < self.surpresa_ate:
            return "surpreso"
        if self.estado == "ouvindo":
            return "ouvindo"
        if self.estado == "pensando":
            return "pensando"
        if self.emo_fala and agora < self.emo_ate:
            return self.emo_fala
        if self.sono > .5:
            return "sono"
        return "neutro"

    def acorda(self, suave=False):
        agora = time.monotonic()
        if self.sono > .5:
            self.surpresa_ate = agora + .7
            if not suave:
                self.F["syV"] -= 2
        self.ult_interacao = agora

    # ------------------------------------------------------------ mouse
    def _no_corpo(self, pos: QPointF) -> bool:
        r = self._kadu_rect()
        e = self._escala()
        ux = (pos.x() - r.x()) / e - 10
        uy = (pos.y() - r.y() - (r.height() - 126 * e) / 2) / e - 14
        return 16 <= ux <= 84 and -2 <= uy <= 92

    def mousePressEvent(self, ev):
        if self.animando or self.oculto:
            return ev.ignore()
        if ev.button() == Qt.MouseButton.LeftButton:
            if self._no_corpo(ev.position()):
                self.segurando, self.arrastou = True, False
                self._press_global = ev.globalPosition().toPoint()
                self._press_win = self.pos()
                self.F["syV"] -= 1.6
                self.acorda()
                ev.accept()
                return
            if self.balao_on:
                self.fecha_balao()
                ev.accept()
                return
        ev.ignore()

    def mouseMoveEvent(self, ev):
        if not self.segurando:
            return
        d = ev.globalPosition().toPoint() - self._press_global
        if not self.arrastou and (abs(d.x()) + abs(d.y())) > 5:
            self.arrastou = True
        if self.arrastou:
            self.move(self._press_win + d)

    def mouseReleaseEvent(self, ev):
        if not self.segurando:
            return
        self.segurando = False
        self.F["syV"] += 2.6
        self._limita_na_tela()
        if self.arrastou:
            a = self.ancora_global()
            self.prefs["pos"] = [a.x(), a.y()]
            self._salva_prefs()
        elif time.monotonic() > self.tonto_ate and not self.balao_on and random.random() < .5:
            self.fala(random.choice(["Hihi, faz cócegas!", "Ei, me solta! Brincadeira, pode segurar.", "Opa! Tô aqui."]),
                      "reacao", "piada", 2.6, falar=True)

    def contextMenuEvent(self, ev):
        menu = QMenu(self)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        try:
            apply_theme(menu)
        except Exception:
            pass
        menu.addAction("🙈 Esconder Kadu", self.esconder)

        m_modo = menu.addMenu("💬 Modo de conversa")
        g = QActionGroup(m_modo)
        for chave, nome in (("foco", "Foco (só quando eu chamar)"), ("equilibrado", "Equilibrado"), ("falante", "Falante")):
            act = QAction(nome, m_modo, checkable=True)
            act.setChecked(self.prefs["modo"] == chave)
            act.triggered.connect(lambda _=False, c=chave: self.troca_modo(c))
            g.addAction(act); m_modo.addAction(act)
        if self.vida.tela_cheia:
            m_modo.addSeparator()
            info = QAction("Tela cheia detectada: em Foco", m_modo); info.setEnabled(False); m_modo.addAction(info)

        m_sai = menu.addMenu("🔊 Saída")
        g4 = QActionGroup(m_sai)
        for chave, nome in (("voz_balao", "Voz + balão"), ("voz", "Só voz"), ("balao", "Só balão (mudo)")):
            act = QAction(nome, m_sai, checkable=True)
            act.setChecked(self.prefs["saida"] == chave)
            act.triggered.connect(lambda _=False, c=chave: self.troca_saida(c))
            g4.addAction(act); m_sai.addAction(act)

        m_tam = menu.addMenu("📏 Tamanho")
        g2 = QActionGroup(m_tam)
        for chave, nome in (("P", "Pequeno"), ("M", "Médio"), ("G", "Grande")):
            act = QAction(nome, m_tam, checkable=True)
            act.setChecked(self.prefs["tamanho"] == chave)
            act.triggered.connect(lambda _=False, c=chave: self.troca_tamanho(c))
            g2.addAction(act); m_tam.addAction(act)

        m_anim = menu.addMenu("🎩 Animação de entrada")
        g3 = QActionGroup(m_anim)
        for chave, nome in (("aleatoria", "Aleatória"), ("toca", "Toca de coelho"), ("cartola", "Cartola de mágico"),
                            ("pulinhos", "Pulinhos"), ("cavando", "Cavando")):
            act = QAction(nome, m_anim, checkable=True)
            act.setChecked(self.prefs["animacao"] == chave)
            act.triggered.connect(lambda _=False, c=chave: self._set_pref("animacao", c))
            g3.addAction(act); m_anim.addAction(act)

        if self._tray_menu is not None:
            menu.addSeparator()
            menu.addActions(self._tray_menu.actions())
        menu.popup(ev.globalPos())
        ev.accept()

    def _set_pref(self, k, v):
        self.prefs[k] = v
        self._salva_prefs()

    def troca_modo(self, modo):
        self._set_pref("modo", modo)
        self.vida.reagenda()
        frases = {"foco": ("Modo foco. Fico quietinho até você me chamar.", "neutro"),
                  "equilibrado": ("Beleza, falo só de vez em quando.", "feliz"),
                  "falante": ("Oba! Agora eu falo bastante.", "animado")}
        t, e = frases[modo]
        self.fala(t, "resposta", e, 3, falar=True)

    def troca_saida(self, saida):
        if saida not in SAIDAS:
            return
        self._set_pref("saida", saida)
        frases = {"voz_balao": ("Voz e balão ligados.", "feliz"),
                  "voz": ("Agora só falo, sem balão.", "neutro"),
                  "balao": ("Modo mudo. Agora eu só escrevo.", "zoando")}
        t, e = frases[saida]
        self.fala(t, "resposta", e, 3, falar=True)

    # ------------------------------------------------------------ tamanho animado
    def troca_tamanho(self, chave):
        if chave not in TAMANHOS:
            return
        self._set_pref("tamanho", chave)
        de, para = self.kw, float(TAMANHOS[chave])
        if abs(de - para) < .5:
            return
        self._tam_anim = (de, para, time.monotonic(), self.ancora_global())
        self.F["syV"] += 2.2 if para > de else -2.2

    def _passo_tamanho(self, agora):
        if not self._tam_anim:
            return
        de, para, t0, ancora = self._tam_anim
        p = min(1.0, (agora - t0) / .62)
        q = -.08 * math.sin(p / .18 * math.pi) if p < .18 else Ease.back(seg(p, .18, 1))
        self.kw = de + (para - de) * q
        self._ajusta_geometria(ancora=ancora)
        if p >= 1:
            self.kw = para
            self._ajusta_geometria(ancora=ancora)
            self._tam_anim = None
            cresce = para > de
            self.F["syV"] += -2.4 if cresce else 2
            self.F["balV"] += 90 if cresce else -60

    # ------------------------------------------------------------ entrar / sair
    def _inicia_anim(self, tipo, entrando):
        dur = {"toca": 1.25, "cartola": 1.7, "pulinhos": 1.8, "cavando": 2.3}[tipo]
        tela = self.screen().availableGeometry() if self.screen() else None
        casa = QPoint(self.pos())
        lado = 1
        if tela is not None:
            lado = 1 if self.ancora_global().x() > tela.center().x() else -1
        self.animando = dict(tipo=tipo, ent=entrando, t0=time.monotonic(), dur=dur, casa=casa, lado=lado, tela=tela)
        self.ult_pulo = -1
        self._passo_anim(time.monotonic())

    def _fim_anim(self):
        a = self.animando
        self.animando = None
        self.fx.update(anim_y=0.0, anim_sx=1.0, anim_sy=1.0, anim_rot=0.0, clip=None, buraco=0.0, chapeu=0.0,
                       monte=0.0, visivel=1.0, sombra=1.0)
        self.move(a["casa"])
        if a["ent"]:
            self.F["syV"] -= 1.5
            self.acorda()
            if random.random() < .7:
                self.fala(random.choice(["Voltei!", "Cheguei! Sentiu minha falta?", "Opa, tô de volta."]), "resposta", "feliz", 2.6, falar=True)
        else:
            self.oculto = True
            self._timer.stop()
            self.vida.parar()
            super().hide()

    def _distancia_borda(self, a) -> float:
        tela = a["tela"]
        if tela is None:
            return 400.0 * a["lado"]
        r = self._kadu_rect()
        if a["lado"] > 0:
            return tela.right() + 30 - (a["casa"].x() + r.left())
        return -((a["casa"].x() + r.right()) - tela.left() + 30)

    def _passo_anim(self, agora):
        a = self.animando
        if not a:
            return
        p = min(1.0, (agora - a["t0"]) / a["dur"])
        getattr(self, "_anim_" + a["tipo"])(p, a["ent"], a)
        if p >= 1:
            self._fim_anim()

    def _anim_toca(self, p, ent, a):
        if ent:
            abre = Ease.out(seg(p, 0, .2)) * (1 - Ease.inn(seg(p, .78, 1)))
            q, q2 = seg(p, .18, .62), seg(p, .62, .85)
            y = 110 - 130 * Ease.out(q) if q < 1 else -20 + 20 * Ease.bounce(q2)
            sx = sy = 1.0
            if q < 1:
                sy, sx = 1 + .22 * (1 - q), 1 - .12 * (1 - q)
            elif q2 < .35:
                sy, sx = .82 + .18 * (q2 / .35), 1.14 - .14 * (q2 / .35)
            rot = (1 - Ease.out(seg(p, .18, .7))) * -14
        else:
            abre = Ease.out(seg(p, .25, .45)) * (1 - Ease.inn(seg(p, .82, 1)))
            q, q2 = seg(p, 0, .3), seg(p, .3, .8)
            y = -16 * math.sin(q * math.pi) if q < 1 else 110 * Ease.inn(q2)
            rot = q2 * 30
            sy, sx = (.85, 1.12) if q < .25 else (1 + .2 * q2, 1 - .1 * q2)
        self.fx.update(buraco=abre, anim_y=y, anim_sx=sx, anim_sy=sy, anim_rot=rot, clip=101.0, sombra=0.0)

    def _anim_cartola(self, p, ent, a):
        hy = hr = 0.0
        hs = 1.0
        sx = sy = 1.0

        def espreme(yy):
            return 1 - .42 * max(0.0, min(1.0, (yy + 22) / 30))
        if ent:
            hy = -150 * (1 - Ease.bounce(seg(p, 0, .2)))
            q = seg(p, .2, .34)
            hr = math.sin(q * math.pi * 4) * 9 * (1 - q)
            sobe, cai = seg(p, .34, .6), seg(p, .6, .88)
            y = 82 - 128 * Ease.out(sobe) if sobe < 1 else -46 + 46 * Ease.bounce(cai)
            some = seg(p, .5, .7)
            hs = 1 - Ease.inn(some)
            hr += some * 120
            if .25 < cai < .4:
                sy, sx = .86, 1.12
            elif hs > .05:
                sx = espreme(y)
        else:
            pula, cai = seg(p, 0, .2), seg(p, .2, .52)
            y = -46 * Ease.out(pula) if cai == 0 else -46 + 128 * Ease.inn(cai)
            hs = Ease.back(seg(p, .08, .3))
            q = seg(p, .52, .68)
            hr = math.sin(q * math.pi * 4) * 9 * (1 - q)
            vai = seg(p, .7, 1)
            hy = -math.sin(vai * math.pi) * 14
            hs *= 1 - Ease.inn(vai)
            hr += vai * 140
            if pula < .3:
                sy, sx = .86, 1.1
            else:
                sx = espreme(y)
        self.fx.update(chapeu=max(0.0, hs), chapeu_y=hy, chapeu_rot=hr, anim_y=y, anim_sx=sx, anim_sy=sy, anim_rot=0.0,
                       clip=67.0 if (y > -22 and hs > .05) else None, sombra=0.0 if hs > .05 else 1.0)

    def _anim_pulinhos(self, p, ent, a):
        n = 4
        dist = self._distancia_borda(a)
        pe = seg(p, 0, .86) if ent else seg(p, .08, 1)
        x = dist * (1 - pe) if ent else dist * pe
        h = pe * n
        i = min(n - 1, int(h))
        loc = 1.0 if pe >= 1 else h - i
        e = self._escala() / 1.25
        altura = ((1 - i / (n + 1)) if ent else (.6 + i / (n + 1))) * 46 * e
        y = -math.sin(loc * math.pi) * altura
        if loc < .12 or loc > .9:
            sy, sx = .84, 1.12
        else:
            sy, sx = 1.08, .95
        if ent and pe >= 1:
            s2 = seg(p, .86, 1)
            sy, sx = 1 - .12 * math.sin(s2 * math.pi), 1 + .1 * math.sin(s2 * math.pi)
        if not ent and pe == 0:
            s2 = seg(p, 0, .08)
            sy, sx = 1 - .14 * math.sin(s2 * math.pi), 1 + .1 * math.sin(s2 * math.pi)
        if i != self.ult_pulo and 0 < pe < 1:
            self.ult_pulo = i
            self.F["abreV"] += 110
        rot = math.sin(loc * math.pi) * -9 * a["lado"] * (1 if ent else -1) if 0 < pe < 1 else 0
        self.move(int(a["casa"].x() + x), a["casa"].y())
        self.fx.update(anim_y=y / self._escala(), anim_sx=sx, anim_sy=sy, anim_rot=rot, clip=None,
                       sombra=max(0.0, 1 + y / (80 * e)))

    def _anim_cavando(self, p, ent, a):
        dist = self._distancia_borda(a)
        viagem = seg(p, 0, .42) if ent else seg(p, .55, 1)
        toca = seg(p, .38, 1) if ent else seg(p, 0, .55)
        mx = dist * (1 - Ease.out(viagem)) if ent else dist * Ease.inn(viagem)
        enc = 1 - seg(p, .38, .46) if ent else seg(p, .5, .58)
        visivel = (viagem > 0 and toca < .12) if ent else (toca >= .9 and viagem < 1)
        monte = 1.0 if visivel else max(0.0, min(1.0, enc)) if 0 < enc < 1 else 0.0
        self._anim_toca(toca, ent, a)
        if (ent and toca == 0) or (not ent and toca >= 1):
            self.fx["anim_y"] = 200.0
        self.move(int(a["casa"].x() + mx), a["casa"].y())
        self.fx.update(monte=monte if (visivel or 0 < enc < 1) else 0.0, monte_esc=max(.05, enc if 0 < enc < 1 else 1.0))

    # ------------------------------------------------------------ tontura
    def _mede_chacoalho(self, agora, dt):
        if not (self.segurando and self.arrastou):
            self.sinal_vx = 0
            self.tontura = max(0.0, self.tontura - dt * 2)
            return
        self.tontura = max(0.0, self.tontura - dt * 2)
        vx, vy = self.F["vx"], self.F["vy"]
        if abs(vx) > 650:
            sg = 1 if vx > 0 else -1
            if self.sinal_vx and sg != self.sinal_vx and agora - self.ult_virada > .09:
                self.tontura += 1
                self.ult_virada = agora
            self.sinal_vx = sg
        elif abs(vy) > 700:
            sg = 2 if vy > 0 else -2
            if abs(self.sinal_vx) == 2 and sg != self.sinal_vx and agora - self.ult_virada > .09:
                self.tontura += 1
                self.ult_virada = agora
            self.sinal_vx = sg
        if self.tontura >= 11:
            self.tontura = 6
            if agora > self.tonto_ate:
                self.reclamou_tonto = False
            self.tonto_ate = max(self.tonto_ate, agora + 3.8)

    # ------------------------------------------------------------ quadro (física)
    def _quadro(self):
        agora = time.monotonic()
        dt = min(1 / 30, max(1 / 240, agora - self._ult_t))
        self._ult_t = agora
        s = agora - self._t0

        self._passo_tamanho(agora)
        self._passo_anim(agora)
        if self.oculto:
            return

        # estado do assistente
        try:
            st = self._state_manager.state
        except Exception:
            st = JarvisState.IDLE
        novo = {JarvisState.LISTENING: "ouvindo", JarvisState.THINKING: "pensando",
                JarvisState.DICTATION_PROCESSING: "pensando", JarvisState.SPEAKING: "falando",
                JarvisState.DICTATING: "ouvindo"}.get(st, "esperando")
        if novo != self.estado:
            self.estado = novo
            self.estado_observado.emit(novo)
            if novo in ("ouvindo", "pensando"):
                self.acorda()
                if novo == "ouvindo":
                    self.F["syV"] -= 1.5
        self._checa_fala_nova(agora)
        if self.balao_on and agora > self.balao_ate and self.estado != "falando":
            self.fecha_balao()
        if self.estado == "falando" and self.emo_fala:
            self.emo_ate = max(self.emo_ate, agora + 1.2)   # a cara segue a voz até ela terminar
        self.falando = self.balao_on and (agora - self.balao_ini) < len(self.balao_txt) * self.balao_vel + .2 or self.estado == "falando"
        self.balao_vis = ap(self.balao_vis, 1.0 if self.balao_on else 0.0, dt * 10)

        # movimento real na tela -> velocidade -> aceleração
        g = QPointF(self.pos())
        if self._ult_pos is None:
            self._ult_pos = g
        vxn, vyn = (g.x() - self._ult_pos.x()) / dt, (g.y() - self._ult_pos.y()) / dt
        self._ult_pos = g
        F = self.F
        vxs, vys = ap(F["vx"], vxn, dt * 25), ap(F["vy"], vyn, dt * 25)
        F["ax"] = lim(ap(F["ax"], (vxs - F["vx"]) / dt, dt * 30), 9000)
        F["ay"] = lim(ap(F["ay"], (vys - F["vy"]) / dt, dt * 30), 9000)
        F["vx"], F["vy"] = vxs, vys
        self._mede_chacoalho(agora, dt)
        if not self.segurando and agora < self.tonto_ate and not self.reclamou_tonto:
            self.reclamou_tonto = True
            self.fala(random.choice(["Uoou... tô vendo tudo rodando!", "Para, para! Tem três de você agora.",
                                     "Isso foi pior que montanha-russa!", "Acho que vou vomitar arco-íris..."]),
                      "reacao", "tonto", 2.8, falar=True)
            self.emo_ate = self.tonto_ate

        parado = self.estado == "esperando" and not self.segurando and not self.balao_on and agora - self.ult_interacao > 25
        self.sono = ap(self.sono, 1.0 if parado else 0.0, dt * 1.5)
        nome = self._expressao(agora)
        X = EXP.get(nome) or EXP["neutro"]

        # olhar: mouse perto > expressão > passear
        gx = gy = incl = 0.0
        perto = False
        r = self._kadu_rect()
        e = self._escala()
        olho_g = QPointF(self.x() + r.x() + (50 + 10) * e, self.y() + r.y() + (r.height() - 126 * e) / 2 + (64 + 14) * e)
        if "gaze" in X:
            gx, gy = X["gaze"]
        elif self.segurando and math.hypot(F["vx"], F["vy"]) > 60:
            gx, gy = lim(-F["vx"] / 250, 3), lim(-F["vy"] / 300, 2.4)
        elif not self.segurando:
            c = QCursor.pos()
            dx, dy = c.x() - olho_g.x(), c.y() - olho_g.y()
            d = math.hypot(dx, dy) or 1
            if d < 320 * (e / 1.25) + 120:
                perto = True
                f = min(1.0, d / 120)
                gx, gy = dx / d * 3.4 * f, dy / d * 2.6 * f
                incl = lim(dx / 40, 5)
                if d < 200:
                    self.ult_interacao = max(self.ult_interacao, agora - 20)   # mouse por perto adia o sono
                if self.sono > .5 and d < 140:
                    self.acorda(True)
        if not perto and "gaze" not in X and not self.segurando:
            if agora > self.troca_olhar:
                self.troca_olhar = agora + 1.8 + random.random() * 2.6
                self.alvo_olhar = (0.0, 0.0) if random.random() < .4 else ((random.random() * 2 - 1) * 2.6, (random.random() * 2 - 1) * 1.4)
            gx, gy = self.alvo_olhar
        F["gx"], F["gy"] = ap(F["gx"], gx, dt * 10), ap(F["gy"], gy, dt * 10)

        # corpo
        F["tilt"], F["tiltV"] = mola(F["tilt"], F["tiltV"], X.get("tilt", 0) + incl, 55, 7, F["ax"] * .05, dt)
        F["tilt"] = lim(F["tilt"], 22)
        F["sy"], F["syV"] = mola(F["sy"], F["syV"], .9 if self.segurando else 1.0, 170, 9, F["ay"] * -.00012, dt)
        F["sy"] = max(.8, min(1.18, F["sy"]))
        alvo_y = X["dy"]
        if not self.segurando:
            alvo_y += math.sin(s * 1.6) * 2 * (1 - self.sono * .6)
            if X.get("pula"):
                alvo_y -= abs(math.sin(s * 7)) * 5
            if X.get("flutua"):
                alvo_y -= 2 + math.sin(s * 3) * 1.5
            if nome == "surpreso" and agora < self.surpresa_ate:
                alvo_y -= 3
        F["y"], F["yV"] = mola(F["y"], F["yV"], alvo_y, 120, 12, 0, dt)

        # orelhas: pose + balanço compartilhado pela inércia
        alvo_a, alvo_b = X["ea"], X["eb"]
        if perto and nome == "neutro":
            alvo_a -= 3; alvo_b -= 10
        if self.falando:
            alvo_a += math.sin(s * 9) * 5; alvo_b += math.sin(s * 9 + 1.2) * 7
        if X.get("ri"):
            alvo_b += math.sin(s * 14) * 9
        if nome == "neutro" and not perto:
            alvo_a += math.sin(s * 1.3) * 2; alvo_b += math.sin(s * 1.1 + 1) * 3
        if agora > self.prox_tremida and nome == "neutro" and not self.segurando:
            F["balV"] += 110 if random.random() < .5 else -110
            self.prox_tremida = agora + 4 + random.random() * 6
        emp_x, emp_y = -F["ax"] * .022, F["ay"] * .013
        F["a"], F["aV"] = mola(F["a"], F["aV"], alvo_a, 90, 13, 0, dt)
        F["b"], F["bV"] = mola(F["b"], F["bV"], alvo_b, 90, 13, 0, dt)
        F["bal"], F["balV"] = mola(F["bal"], F["balV"], 0, 60, 6, emp_x * 32 - F["tiltV"] * 1.5, dt)
        F["bal"] = lim(F["bal"], 42)
        F["abre"], F["abreV"] = mola(F["abre"], F["abreV"], 0, 60, 6.5, emp_y * 45, dt)
        F["abre"] = lim(F["abre"], 40)
        F["pt"], F["ptV"] = mola(F["pt"], F["ptV"], 0, 44, 4.2, emp_x * 28 - F["balV"] * 1.4, dt)
        F["pt"] = lim(F["pt"], 38)

        # olhos
        if agora > self.prox_pisca:
            self.piscou_em = agora
            self.pisca_dupla = random.random() < .25
            self.prox_pisca = agora + 2.3 + random.random() * 3.8
        if self.pisca_dupla and .26 < agora - self.piscou_em < .30:
            self.piscou_em = agora
            self.pisca_dupla = False
        sm = self.sm
        gE, gD = glifo(X["olho"], -1), glifo(X["olho"], 1)
        sm["ovE"] = ap(sm["ovE"], 0.0 if gE else 1.0, dt * 18)
        sm["ovD"] = ap(sm["ovD"], 0.0 if gD else 1.0, dt * 18)
        rx, ry = 4.0, 6.2
        if X["olho"] == "grande":
            rx, ry = 4.9, 7.6
        if X.get("olhoGrande"):
            rx, ry = 4.5, 7.0
        if perto and nome == "neutro":
            rx, ry = 4.3, 6.7
        sm["rx"], sm["ry"] = ap(sm["rx"], rx, dt * 12), ap(sm["ry"], ry, dt * 12)
        sm["olhoDy"] = ap(sm["olhoDy"], X.get("olhoDy", 0), dt * 12)
        lid = X.get("lid", (0, 0, 0, 0))
        for k, v in zip(("lhE", "liE", "lhD", "liD"), lid):
            sm[k] = ap(sm[k], v, dt * 10)
        sm["lag"] = ap(sm["lag"], 1.0 if X.get("chora") else 0.0, dt * 6)
        sm["br"] = ap(sm["br"], 1.0 if X.get("brilho") else 0.0, dt * 8)
        sm["aura"] = ap(sm["aura"], 1.0 if self.estado == "ouvindo" else 0.0, dt * 6)
        if X["olho"] == "espiral":
            self.giro["E"] -= dt * 260; self.giro["D"] += dt * 260

        self._nome_exp, self._X, self._gl, self._s = nome, X, (gE, gD), s
        self._clique_atraves()
        self.update()

    # ------------------------------------------------------------ cliques atravessam a área vazia (Windows)
    def _clique_atraves(self):
        """Só o corpo do Kadu recebe clique; o resto da janela (espaço do balão, pulos) deixa o clique passar."""
        if sys.platform != "win32":
            return
        c = self.mapFromGlobal(QCursor.pos())
        quer_mouse = self.segurando or (not self.animando and self._no_corpo(QPointF(c)))
        if quer_mouse == getattr(self, "_aceita_mouse", None):
            return
        self._aceita_mouse = quer_mouse
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE, WS_EX_TRANSPARENT, WS_EX_LAYERED = -20, 0x20, 0x80000
            u32 = ctypes.windll.user32
            estilo = u32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED
            estilo = (estilo & ~WS_EX_TRANSPARENT) if quer_mouse else (estilo | WS_EX_TRANSPARENT)
            u32.SetWindowLongW(hwnd, GWL_EXSTYLE, estilo)
        except Exception as exc:
            debug_log(f"kadu: clique-através falhou: {exc}", "face")

    # ------------------------------------------------------------ desenho
    def paintEvent(self, _ev):
        if not hasattr(self, "_X"):
            return
        pt = QPainter(self)
        pt.setRenderHint(QPainter.RenderHint.Antialiasing)
        try:
            self._desenha_kadu(pt)
            self._desenha_balao(pt)
        finally:
            pt.end()

    def _desenha_kadu(self, pt: QPainter):
        F, sm, X, s, fx = self.F, self.sm, self._X, self._s, self.fx
        r = self._kadu_rect()
        e = self._escala()
        pt.save()
        pt.translate(r.x(), r.y() + (r.height() - 126 * e) / 2)
        pt.scale(e, e)
        pt.translate(10, 14)   # agora valem as coordenadas do desenho original

        # aura (ouvindo)
        if sm["aura"] > .01:
            rr = 45 + math.sin(s * 5) * 2 * sm["aura"]
            grad = QRadialGradient(QPointF(50, 62), rr)
            c0, c1 = QColor(AURA), QColor(AURA)
            c0.setAlphaF(0); c1.setAlphaF(.4)
            grad.setColorAt(.6, c0); grad.setColorAt(.82, c1)
            c2 = QColor(AURA); c2.setAlphaF(0); grad.setColorAt(1, c2)
            pt.setOpacity(sm["aura"] * (.7 + .3 * math.sin(s * 5)))
            pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(QBrush(grad))
            pt.drawEllipse(QPointF(50, 62), rr, rr)
            pt.setOpacity(1)

        # buraco da toca
        if fx["buraco"] > .01:
            pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(BURACO)
            pt.drawEllipse(QPointF(50, 101), 24 * fx["buraco"], 5.5 * fx["buraco"])
            pt.setBrush(Qt.BrushStyle.NoBrush); pt.setPen(QPen(BURACO_BORDA, 1.6))
            pt.drawEllipse(QPointF(50, 99.6), 24 * fx["buraco"], 5.5 * fx["buraco"])

        # montinho de terra (cavando)
        if fx.get("monte", 0) > .01:
            pt.save()
            pt.translate(0, math.sin(s * 60) * .6)
            pt.translate(50, 101); pt.scale(1, fx.get("monte_esc", 1)); pt.translate(-50, -101)
            mt = QPainterPath(QPointF(33, 101.5))
            mt.quadTo(36, 92, 43, 89); mt.quadTo(50, 85, 57, 89); mt.quadTo(64, 92, 67, 101.5); mt.closeSubpath()
            pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(TERRA); pt.drawPath(mt)
            cr = QPainterPath(QPointF(39, 92.5)); cr.quadTo(50, 86.5, 61, 92.5)
            pt.setBrush(Qt.BrushStyle.NoBrush); pt.setPen(QPen(TERRA_LUZ, 1.6, cap=Qt.PenCapStyle.RoundCap)); pt.drawPath(cr)
            pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(TERRA_LUZ)
            for k, (x, y, rad) in enumerate(((40, 88, 1.6), (58, 86, 1.3), (50, 83, 1.1))):
                pt.drawEllipse(QPointF(x, y - abs(math.sin(s * 40 + k * 1.7)) * 5), rad, rad)
            pt.restore()

        # sombra
        alt = 6 if self.segurando else F["y"]
        op = max(.06, .25 + alt * .012 - (.1 if self.segurando else 0)) * fx["sombra"]
        if op > .01:
            sc = QColor(INK); sc.setAlphaF(min(1, op))
            pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(sc)
            pt.drawEllipse(QPointF(50, 101), 17 + alt * .5, 3.2)

        # chapéu: parte de trás
        if fx["chapeu"] > .01:
            self._transf_chapeu(pt, True)
            pt.setPen(Qt.PenStyle.NoPen)
            pt.setBrush(QColor("#2E2557")); pt.drawEllipse(QPointF(50, 66), 31, 6.5)
            pt.setBrush(BURACO); pt.drawEllipse(QPointF(50, 66), 24, 4.4)
            pt.restore()

        # corpo (com recorte da toca/cartola)
        pt.save()
        if fx["clip"] is not None:
            pt.setClipRect(QRectF(-60, -300, 220, 300 + fx["clip"]))
        if fx["anim_y"] < 150:
            pt.translate(0, fx["anim_y"])
            pt.translate(50, 62); pt.rotate(fx["anim_rot"]); pt.translate(-50, -62)
            pt.translate(50, 88); pt.scale(fx["anim_sx"], fx["anim_sy"]); pt.translate(-50, -88)
            self._desenha_corpo(pt)
        pt.restore()

        # chapéu: frente
        if fx["chapeu"] > .01:
            self._transf_chapeu(pt, False)
            pt.setPen(Qt.PenStyle.NoPen)
            copa = QPolygonF([QPointF(26.5, 66), QPointF(73.5, 66), QPointF(70.5, 99), QPointF(50, 102.5), QPointF(29.5, 99)])
            pt.setBrush(CARTOLA); pt.drawPolygon(copa)
            pt.setBrush(CARTOLA_FAIXA)
            pt.drawPolygon(QPolygonF([QPointF(27.2, 73.5), QPointF(72.8, 73.5), QPointF(72.3, 80), QPointF(27.7, 80)]))
            aba = QPainterPath(QPointF(19, 66))
            aba.arcTo(QRectF(19, 59.5, 62, 13), 180, 180)
            aba.lineTo(76, 66)
            aba.arcTo(QRectF(24, 61.6, 52, 8.8), 0, -180)
            aba.closeSubpath()
            pt.setBrush(CARTOLA_ABA); pt.drawPath(aba)
            pt.restore()
        pt.restore()

    def _transf_chapeu(self, pt, _tras):
        fx = self.fx
        pt.save()
        pt.translate(0, fx["chapeu_y"])
        pt.translate(50, 100); pt.rotate(fx["chapeu_rot"]); pt.scale(fx["chapeu"], fx["chapeu"]); pt.translate(-50, -100)

    def _pelo(self):
        g = QRadialGradient(QPointF(38, 40), 56)
        g.setColorAt(0, PELO_LUZ); g.setColorAt(.5, PELO_MEIO); g.setColorAt(1, PELO_SOMBRA)
        return QBrush(g)

    def _desenha_corpo(self, pt: QPainter):
        F, sm, X, s = self.F, self.sm, self._X, self._s
        tx = 0.0
        if X.get("treme"):
            tx = math.sin(s * 38) * .6
        if X.get("balanca"):
            tx = math.sin(s * 3.2) * 2.2
        if X.get("ri") and self.falando:
            tx = math.sin(s * 22) * .9
        resp = math.sin(s * (2.1 - self.sono * .9)) * (.012 + self.sono * .01)
        sy = F["sy"] * (1 + resp)
        sx = 1 + (1 - F["sy"]) * .9 - resp
        piv = 62 if self.segurando else 88
        pt.save()
        pt.translate(tx, F["y"])
        pt.translate(50, piv); pt.rotate(F["tilt"]); pt.translate(-50, -piv)
        pt.translate(50, 88); pt.scale(sx, sy); pt.translate(-50, -88)

        pelo = self._pelo()
        pt.setPen(Qt.PenStyle.NoPen)
        ang_a = F["a"] + F["bal"] + F["abre"] * .7
        ang_b = max(-10.0, min(115.0, F["b"] + F["bal"] - F["abre"] * .7))
        for (base, ponta, piv_o, piv_p, ang) in (
                (QRectF(33.5, 24, 15, 26), QRectF(33.5, 6, 15, 28), (41, 46), (41, 30), ang_a),
                (QRectF(40, 25, 15, 25), QRectF(40, 8, 15, 27), (47, 46), (47.5, 31), ang_b)):
            pt.save()
            pt.translate(*piv_o); pt.rotate(ang); pt.translate(-piv_o[0], -piv_o[1])
            pt.setBrush(pelo); pt.drawRoundedRect(base, 7.5, 7.5)
            pt.translate(*piv_p); pt.rotate(F["pt"]); pt.translate(-piv_p[0], -piv_p[1])
            pt.drawRoundedRect(ponta, 7.5, 7.5)
            pt.restore()

        cabeca = QPainterPath(QPointF(50, 36))
        cabeca.cubicTo(70, 36, 80, 48, 80, 64); cabeca.cubicTo(80, 80, 66, 88, 50, 88)
        cabeca.cubicTo(34, 88, 20, 80, 20, 64); cabeca.cubicTo(20, 48, 30, 36, 50, 36)
        pt.setBrush(pelo); pt.drawPath(cabeca)
        risco = QPainterPath(QPointF(43, 38.5)); risco.quadTo(49, 40.5, 54, 45.5)
        pt.setBrush(Qt.BrushStyle.NoBrush); pt.setPen(QPen(PELO_SOMBRA, 3, cap=Qt.PenCapStyle.RoundCap)); pt.drawPath(risco)

        # rosto
        pt.translate(F["gx"], F["gy"])
        self._desenha_olhos(pt)
        pt.restore()

    def _desenha_olhos(self, pt: QPainter):
        sm, X, s = self.sm, self._X, self._s
        agora = time.monotonic()
        f = (agora - self.piscou_em) / .15
        abre = abs(1 - f * 2) if f < 1 else 1.0
        cy = 64 + sm["olhoDy"]
        topo = cy - sm["ry"]

        def palp(h, i, interno):
            ativo = min(1.0, (h + abs(i)) * 6)
            y = topo + h * 2 * sm["ry"] - 7 * (1 - ativo)
            d = 4.8 * i
            return (y - d, y + d) if interno > 0 else (y + d, y - d)

        for L, cx, lado in (("E", 41, -1), ("D", 59, 1)):
            ov = sm["ov" + L]
            if ov > .01:
                y1, y2 = palp(sm["lh" + L], sm["li" + L], 1 if lado < 0 else -1)
                x0, x1 = (33, 49) if lado < 0 else (51, 67)
                pt.save()
                clip = QPainterPath(QPointF(x0, y1)); clip.lineTo(x1, y2); clip.lineTo(x1, 80); clip.lineTo(x0, 80); clip.closeSubpath()
                pt.setClipPath(clip)
                pt.setOpacity(ov)
                pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(INK)
                pt.drawEllipse(QPointF(cx, cy), sm["rx"], sm["ry"] * max(.07, abre))
                if sm["br"] > .01:
                    pt.setOpacity(ov * sm["br"] * abre)
                    pt.setBrush(QColor("#FFFFFF"))
                    pt.drawEllipse(QPointF(cx + 1.6 + math.sin(s * 9 + (lado > 0)) * .35, cy - 2.7 + math.cos(s * 7) * .3), 1.5, 1.9)
                pt.restore()
            g = self._gl[0 if lado < 0 else 1]
            if g and ov < .99:
                caminho, cheio, larg = g
                pt.save()
                pt.setOpacity(1 - ov)
                pt.translate(cx, 64)
                pt.scale(1.22, 1.22 * max(.08, abre))
                if X["olho"] == "espiral":
                    pt.rotate(self.giro[L])
                if X["olho"] == "coracao":
                    k = 1 + max(0.0, math.sin(s * 7)) * .16
                    pt.scale(k, k)
                if X["olho"] == "estrela":
                    pt.rotate(math.sin(s * 4) * 12)
                pt.translate(-cx, -64)
                if cheio:
                    pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(INK)
                else:
                    pt.setBrush(Qt.BrushStyle.NoBrush)
                    pt.setPen(QPen(INK, larg, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
                pt.drawPath(caminho)
                pt.restore()

        # lágrimas
        if sm["lag"] > .02:
            for x, fase in ((37.5, 0), (62.5, .5)):
                ciclo = (s * .85 + fase) % 1
                pt.save()
                pt.translate(x, 69 + ciclo * 13); pt.scale(.55 + ciclo * .5, .55 + ciclo * .5)
                pt.setOpacity(sm["lag"] * (1 if ciclo < .8 else (1 - ciclo) * 5))
                gota = QPainterPath(QPointF(0, -3.2))
                gota.cubicTo(1.8, -.6, 2.6, .8, 2.6, 2); gota.cubicTo(2.6, 3.6, 1.4, 4.6, 0, 4.6)
                gota.cubicTo(-1.4, 4.6, -2.6, 3.6, -2.6, 2); gota.cubicTo(-2.6, .8, -1.8, -.6, 0, -3.2)
                pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(LAGRIMA); pt.drawPath(gota)
                pt.restore()

    def _desenha_balao(self, pt: QPainter):
        if self.balao_vis < .02 or not self.balao_txt:
            return
        agora = time.monotonic()
        n = int((agora - self.balao_ini) / self.balao_vel) if self.balao_vel > 0 else len(self.balao_txt)
        texto = self.balao_txt[:max(0, min(len(self.balao_txt), n))]
        rotulo, cor = ROTULOS.get(self.balao_tipo, ROTULOS["resposta"])
        fonte = QFont("Segoe UI", 10)
        fonte_tag = QFont("Segoe UI", 7, QFont.Weight.DemiBold)
        fonte_tag.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 108)
        fm = QFontMetricsF(fonte)
        larg_max = min(270.0, self.width() - 16.0)
        # mede com o texto inteiro para o balão não ficar mudando de tamanho enquanto digita
        caixa = fm.boundingRect(QRectF(0, 0, larg_max - 26, 2000), int(Qt.TextFlag.TextWordWrap), self.balao_txt)
        w = max(110.0, caixa.width() + 26)
        h = caixa.height() + 34
        r = self._kadu_rect()
        x = min(max(8.0, r.center().x() + r.width() * .25 - w), self.width() - w - 8)
        y = max(4.0, r.top() + r.height() * .05 - h)
        sobe = (1 - self.balao_vis) * 8
        pt.save()
        pt.setOpacity(self.balao_vis)
        pt.translate(0, sobe)
        sombra = QColor(0, 0, 0, 70)
        pt.setPen(Qt.PenStyle.NoPen); pt.setBrush(sombra)
        pt.drawRoundedRect(QRectF(x + 1, y + 4, w, h), 16, 16)
        pt.setBrush(QColor("#FFFFFF"))
        pt.drawRoundedRect(QRectF(x, y, w, h), 16, 16)
        cauda_x = min(max(x + 18, r.center().x() + 8), x + w - 18)
        pt.drawPolygon(QPolygonF([QPointF(cauda_x - 9, y + h - 1), QPointF(cauda_x + 9, y + h - 1), QPointF(cauda_x, y + h + 9)]))
        pt.setFont(fonte_tag); pt.setPen(cor)
        pt.drawText(QRectF(x + 13, y + 7, w - 26, 14), int(Qt.AlignmentFlag.AlignLeft), rotulo.upper())
        pt.setFont(fonte); pt.setPen(INK)
        pt.drawText(QRectF(x + 13, y + 22, w - 26, h - 26), int(Qt.TextFlag.TextWordWrap), texto)
        pt.restore()

    # ------------------------------------------------------------ ciclo de vida
    def hideEvent(self, ev):
        if not self.oculto:     # escondido por fora (ex.: app fechando)
            self.oculto = True
            self._timer.stop()
            self.vida.parar()
        super().hideEvent(ev)
