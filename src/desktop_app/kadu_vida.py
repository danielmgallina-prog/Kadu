"""Vida própria do Kadu: comentários, lembretes, reações aos apps e Foco em tela cheia.

Tudo aqui é local e não gasta cota do Gemini: as falas espontâneas vêm de listas,
e o app em primeiro plano é lido pela API do Windows (ctypes). Em outros sistemas
as partes específicas do Windows simplesmente ficam desligadas.
"""

from __future__ import annotations

import random
import sys
import time

from PyQt6.QtCore import QTimer

from jarvis.debug import debug_log

# (frase, emoção)
ESPONTANEOS = [
    ("Por que o programador foi ao médico? Tava com um bug no peito.", "piada"),
    ("Sabe por que o C foi à terapia? Tinha muitos problemas de ponteiro.", "piada"),
    ("O que o array disse pro índice? Para de me apontar!", "piada"),
    ("Sabia que o primeiro bug de computador foi uma mariposa de verdade, em 1947?", "surpreso"),
    ("Curiosidade: coelho consegue girar a orelha quase 270 graus. Eu só consigo fazer um K.", "encantado"),
    ("Tô aqui se precisar, é só me chamar.", "feliz"),
    ("Esse silêncio tá suspeito. Tá estudando ou jogando?", "desconfiado"),
    ("Se travar em algum código, me chama que a gente resolve junto.", "animado"),
    ("Dica: no for, o i++ roda depois de cada volta, não antes.", "neutro"),
    ("Já salvou o arquivo hoje? Pergunto por um amigo.", "zoando"),
    ("Coelho dorme de olho meio aberto. Eu durmo de orelha em pé.", "piada"),
    ("Hoje é um bom dia pra fechar uma tarefa pendente. Só uma já vale.", "feliz"),
]

LEMBRETE_PAUSA = [
    ("Faz quase uma hora direto no PC. Bora levantar e alongar um pouco?", "neutro"),
    ("Pausa rapidinha? Seus olhos agradecem. Olha pra longe uns 20 segundos.", "feliz"),
]
LEMBRETE_PAUSA_FORTE = [
    ("Ei! Mais de duas horas sem pausa. Levanta dessa cadeira agora!", "bravo"),
]
LEMBRETE_AGUA = [
    ("Hora de beber água!", "animado"),
    ("Um copo d'água agora cai bem. Eu espero aqui.", "feliz"),
]

# processo (minúsculo) -> (frases, emoção)
REACOES = {
    "code.exe": (["Abriu o VS Code! Bora programar.", "Modo dev ativado. Quer que eu fique no Foco?"], "animado"),
    "devenv.exe": (["Visual Studio aberto. Café do lado?"], "animado"),
    "chrome.exe": (["Navegando, é? Não vai se perder em vídeo de gatinho."], "zoando"),
    "msedge.exe": (["Edge aberto. Pesquisa séria ou distração?"], "desconfiado"),
    "firefox.exe": (["Firefox! Raiz."], "feliz"),
    "spotify.exe": (["Opa, música! Que que vai tocar?"], "animado"),
    "discord.exe": (["Discord aberto. Manda um oi pra galera por mim."], "feliz"),
    "whatsapp.exe": (["WhatsApp aberto. Responde aquele áudio que você tá enrolando."], "zoando"),
    "steam.exe": (["Steam aberta... vai jogar? Eu fico quietinho no Foco."], "encantado"),
    "winword.exe": (["Word aberto. Trabalho da faculdade?"], "neutro"),
    "excel.exe": (["Planilha! Se precisar de fórmula, me pergunta."], "neutro"),
    "powerpnt.exe": (["Apresentação? Capricha nos slides."], "feliz"),
    "obs64.exe": (["Vai gravar? Deixa eu arrumar a orelha."], "surpreso"),
    "taskmgr.exe": (["Gerenciador de tarefas... tem coisa pesando aí?"], "desconfiado"),
}

# Intervalos dos comentários espontâneos em segundos, por modo.
INTERVALOS = {"equilibrado": (20 * 60, 30 * 60), "falante": (5 * 60, 10 * 60)}
PAUSA_APOS = 55 * 60        # tempo de uso contínuo até o lembrete de pausa
PAUSA_FORTE_APOS = 125 * 60
AGUA_A_CADA = 95 * 60
OCIOSO_ZERA = 5 * 60        # 5 min sem mexer = conta como pausa
REACAO_RECARGA = 15 * 60    # não reage ao mesmo app de novo antes disso


class _Win:
    """Acesso mínimo à API do Windows. Tudo devolve None fora do Windows ou em caso de erro."""

    def __init__(self):
        self.ok = sys.platform == "win32"
        if not self.ok:
            return
        try:
            import ctypes
            from ctypes import wintypes
            self.ctypes, self.wt = ctypes, wintypes
            self.u32, self.k32 = ctypes.windll.user32, ctypes.windll.kernel32

            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                            ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]
            self.LASTINPUTINFO, self.MONITORINFO = LASTINPUTINFO, MONITORINFO
        except Exception as exc:
            debug_log(f"kadu: API do Windows indisponível: {exc}", "face")
            self.ok = False

    def ocioso_seg(self):
        if not self.ok:
            return None
        try:
            li = self.LASTINPUTINFO()
            li.cbSize = self.ctypes.sizeof(li)
            if not self.u32.GetLastInputInfo(self.ctypes.byref(li)):
                return None
            return max(0, (self.k32.GetTickCount() - li.dwTime) & 0xFFFFFFFF) / 1000.0
        except Exception:
            return None

    def janela_frente(self):
        """(nome do processo em minúsculas, está em tela cheia) do app em primeiro plano."""
        if not self.ok:
            return None, False
        try:
            hwnd = self.u32.GetForegroundWindow()
            if not hwnd:
                return None, False
            classe = self.ctypes.create_unicode_buffer(256)
            self.u32.GetClassNameW(hwnd, classe, 256)
            if classe.value in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
                return "explorer.exe", False
            pid = self.wt.DWORD()
            self.u32.GetWindowThreadProcessId(hwnd, self.ctypes.byref(pid))
            nome = None
            try:
                import psutil
                nome = psutil.Process(pid.value).name().lower()
            except Exception:
                pass
            rect = self.wt.RECT()
            self.u32.GetWindowRect(hwnd, self.ctypes.byref(rect))
            mon = self.u32.MonitorFromWindow(hwnd, 2)
            mi = self.MONITORINFO()
            mi.cbSize = self.ctypes.sizeof(mi)
            cheia = False
            if self.u32.GetMonitorInfoW(mon, self.ctypes.byref(mi)):
                m = mi.rcMonitor
                cheia = (rect.left <= m.left and rect.top <= m.top and rect.right >= m.right and rect.bottom >= m.bottom)
            return nome, cheia
        except Exception:
            return None, False


class Vida:
    def __init__(self, kadu):
        self.kadu = kadu
        self.win = _Win()
        self.tela_cheia = False
        self.app_atual = None
        self._reagiu_em = {}
        self._inicio_uso = time.monotonic()
        self._ult_agua = time.monotonic()
        self._avisou_pausa = False
        self._avisou_pausa_forte = False
        self._prox_espontaneo = None
        self._timer = QTimer(kadu)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._tique)

    # ------------------------------------------------------------ modos
    def modo_efetivo(self) -> str:
        if self.tela_cheia:
            return "foco"
        return self.kadu.prefs.get("modo", "equilibrado")

    def reagenda(self):
        faixa = INTERVALOS.get(self.modo_efetivo())
        self._prox_espontaneo = time.monotonic() + random.uniform(*faixa) if faixa else None

    def iniciar(self):
        self.reagenda()
        self._timer.start()

    def parar(self):
        self._timer.stop()

    # ------------------------------------------------------------ laço (a cada 2 s)
    def _pode_falar(self) -> bool:
        k = self.kadu
        return (not k.oculto and not k.animando and not k.segurando and not k.balao_on
                and k.estado == "esperando" and time.monotonic() > k.emo_ate)

    def _tique(self):
        agora = time.monotonic()
        nome, cheia = self.win.janela_frente()
        if cheia != self.tela_cheia:
            self.tela_cheia = cheia
            self.reagenda()
            debug_log(f"kadu: tela cheia={cheia}", "face")

        # uso contínuo: 5 min parado conta como pausa
        ocioso = self.win.ocioso_seg()
        if ocioso is not None and ocioso >= OCIOSO_ZERA:
            self._inicio_uso = agora
            self._avisou_pausa = self._avisou_pausa_forte = False

        modo = self.modo_efetivo()
        if modo == "foco":
            return

        # reação a app aberto (só quando muda de app)
        if nome and nome != self.app_atual:
            anterior, self.app_atual = self.app_atual, nome
            if anterior is not None and nome in REACOES and self._pode_falar():
                ult = self._reagiu_em.get(nome, -1e9)
                chance = 1.0 if modo == "falante" else .5
                if agora - ult > REACAO_RECARGA and random.random() < chance:
                    frases, emo = REACOES[nome]
                    self._reagiu_em[nome] = agora
                    self.kadu.fala(random.choice(frases), "reacao", emo, falar=True)
                    return

        if not self._pode_falar():
            return
        uso = agora - self._inicio_uso
        if uso > PAUSA_FORTE_APOS and not self._avisou_pausa_forte:
            self._avisou_pausa_forte = True
            t, e = random.choice(LEMBRETE_PAUSA_FORTE)
            self.kadu.fala(t, "lembrete", e, falar=True)
            return
        if uso > PAUSA_APOS and not self._avisou_pausa:
            self._avisou_pausa = True
            t, e = random.choice(LEMBRETE_PAUSA)
            self.kadu.fala(t, "lembrete", e, falar=True)
            return
        if agora - self._ult_agua > AGUA_A_CADA:
            self._ult_agua = agora
            t, e = random.choice(LEMBRETE_AGUA)
            self.kadu.fala(t, "lembrete", e, falar=True)
            return
        if self._prox_espontaneo is not None and agora > self._prox_espontaneo:
            t, e = random.choice(ESPONTANEOS)
            self.kadu.fala(t, "espontaneo", e, falar=True)
            self.reagenda()
