"""Ponte entre o motor de respostas e o Kadu animado.

O modelo começa cada resposta com uma marcação de emoção, por exemplo
``[emo:animado] Bora lá!``. Este módulo:

* separa a marcação do texto (a voz e a memória nunca recebem a marcação);
* publica a última fala num arquivo temporário que o Kadu lê para escolher
  a expressão e mostrar o balão. Funciona igual com o daemon no mesmo
  processo ou em subprocesso, do mesmo jeito que o arquivo ``jarvis_state``.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
import unicodedata
from typing import Optional, Tuple

EMOCOES = (
    "neutro", "feliz", "animado", "encantado", "apaixonado", "piada", "zoando",
    "surpreso", "desconfiado", "tedio", "bravo", "triste", "chorando", "tonto", "erro",
    "confuso", "assustado", "orgulhoso", "envergonhado", "determinado", "pensando", "ouvindo", "focado",
    "pidao", "marejado", "carregando", "ideia", "pesquisando", "musica", "fominha", "glitch",
    "indiferente", "zen", "fogo", "exausto",
)

# Variações que o modelo às vezes escreve no lugar do nome exato.
_SINONIMOS = {
    "normal": "neutro", "calmo": "neutro", "serio": "neutro",
    "alegre": "feliz", "contente": "feliz", "feliz_da_vida": "feliz",
    "empolgado": "animado", "animada": "animado", "euforico": "animado",
    "maravilhado": "encantado", "impressionado": "encantado", "orgulhoso": "encantado",
    "amor": "apaixonado", "carinhoso": "apaixonado", "fofo": "apaixonado",
    "engracado": "piada", "rindo": "piada", "brincalhao": "piada", "brincando": "piada",
    "sarcastico": "zoando", "ironico": "zoando", "debochado": "zoando", "provocando": "zoando",
    "surpresa": "surpreso", "chocado": "surpreso", "assustado": "surpreso",
    "suspeito": "desconfiado", "duvida": "desconfiado", "cetico": "desconfiado",
    "entediado": "tedio", "cansado": "tedio", "sono": "tedio",
    "irritado": "bravo", "zangado": "bravo", "nervoso": "bravo", "raiva": "bravo",
    "chateado": "triste", "desanimado": "triste", "preocupado": "triste",
    "choro": "chorando", "emocionado": "chorando",
    "perdido": "confuso", "duvidoso": "confuso",
    "medo": "assustado", "com_medo": "assustado", "orgulho": "orgulhoso", "vergonha": "envergonhado", "timido": "envergonhado",
    "focada": "focado", "concentrado": "focado", "pedindo": "pidao", "fofinho": "pidao", "pidona": "pidao",
    "emocionado_triste": "marejado", "quase_chorando": "marejado", "eureka": "ideia", "inspirado": "ideia",
    "buscando": "pesquisando", "procurando": "pesquisando", "fome": "fominha", "faminto": "fominha",
    "tanto_faz": "indiferente", "seco": "indiferente", "calmo_zen": "zen", "tranquilo": "zen", "relaxado": "zen",
    "empolgadissimo": "fogo", "motivado": "fogo", "exausta": "exausto", "esgotado": "exausto", "musical": "musica",
    "falha": "erro", "problema": "erro",
}

# [emo:feliz]  [emo: feliz]  (emo:feliz)  {emo:feliz}
_PADRAO = re.compile(r"[\[\(\{]\s*emo(?:cao|ção)?\s*[:=]\s*([^\]\)\}\s]+)\s*[\]\)\}]", re.IGNORECASE)

_ARQUIVO = os.path.join(tempfile.gettempdir(), "kadu_fala.json")


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(nome: str) -> str:
    chave = _sem_acento((nome or "").strip().lower()).replace("-", "_")
    if chave in EMOCOES:
        return chave
    return _SINONIMOS.get(chave, "neutro")


def extrair(texto: Optional[str]) -> Tuple[str, str]:
    """Remove todas as marcações e devolve (texto limpo, primeira emoção encontrada)."""
    if not texto:
        return texto or "", "neutro"
    achado = _PADRAO.search(texto)
    emocao = normalizar(achado.group(1)) if achado else "neutro"
    limpo = _PADRAO.sub("", texto)
    limpo = re.sub(r"[ \t]{2,}", " ", limpo).strip()
    return limpo, emocao


def publicar(texto: str, emocao: str = "neutro", origem: str = "resposta") -> None:
    """Grava a fala de forma atômica. Falhas são ignoradas: o Kadu é opcional."""
    if not texto or not texto.strip():
        return
    dados = {
        "id": time.time_ns(),
        "texto": texto.strip(),
        "emocao": normalizar(emocao),
        "origem": origem,
    }
    pendente = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", prefix=".kadu-fala-",
                                         dir=os.path.dirname(_ARQUIVO), delete=False) as f:
            pendente = f.name
            json.dump(dados, f, ensure_ascii=False)
        os.replace(pendente, _ARQUIVO)
        pendente = None
    except OSError:
        pass
    finally:
        if pendente:
            try:
                os.unlink(pendente)
            except OSError:
                pass


def ler() -> Optional[dict]:
    try:
        with open(_ARQUIVO, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if isinstance(dados, dict) and "id" in dados and "texto" in dados:
            return dados
    except (OSError, ValueError):
        pass
    return None


def arquivo() -> str:
    return _ARQUIVO


# ------------------------------------------------------------ preferências do Kadu (saída de voz)
SAIDAS = ("voz_balao", "voz", "balao")
_cache_prefs = {"mtime": None, "dados": {}}


def _prefs_path() -> str:
    try:
        from .config import get_config_path
        return os.path.join(os.path.dirname(str(get_config_path())), "kadu.json")
    except Exception:
        return os.path.join(os.path.expanduser("~"), ".config", "jarvis", "kadu.json")


def prefs() -> dict:
    caminho = _prefs_path()
    try:
        mtime = os.path.getmtime(caminho)
    except OSError:
        return {}
    if mtime != _cache_prefs["mtime"]:
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            _cache_prefs.update(mtime=mtime, dados=dados if isinstance(dados, dict) else {})
        except (OSError, ValueError):
            return _cache_prefs["dados"]
    return _cache_prefs["dados"]


def saida() -> str:
    s = prefs().get("saida", "voz_balao")
    return s if s in SAIDAS else "voz_balao"


def voz_ligada() -> bool:
    """False no modo 'só balão' (mudo): as respostas aparecem só escritas."""
    return saida() != "balao"


# Canal desktop -> daemon para o Kadu falar as frases dele (comentários, lembretes...).
FALAR_IPC_PREFIX = "__KADU_FALAR__:"
# Botão de microfone da barra do Kadu: abre a escuta sem a palavra "Kadu".
OUVIR_IPC_PREFIX = "__KADU_OUVIR__"


# ------------------------------------------------------------ respostas especiais (sem passar pelo Gemini)
import random as _random

_LINDA_GATILHOS = [
    r"mulher mais (linda|bonita|maravilhosa|perfeita|gata|incrivel|linda desse|bonita desse)",
    r"(quem|qual) (e|eh) (a )?minha namorada",
    r"nome da minha namorada",
    r"espelho,? espelho meu",
    r"quem (manda|mora) no meu coracao",
    r"quem (e|eh) o amor da minha vida",
    r"quem (e|eh) a pessoa mais especial",
    r"^(kadu[ ,.!]*)?quem eu amo",
]
_LINDA_RESPOSTAS = [
    "A Linda, claro! Nem precisava perguntar.",
    "Espelho, espelho meu? Fácil: é a Linda. Próxima pergunta.",
    "Pesquisei no universo inteiro e deu Linda em primeiro lugar. De novo.",
    "Linda. O nome já entrega, né?",
    "É a Linda! Até meu coração de coelho acelerou aqui.",
    "Essa é fácil: a Linda. Pode perguntar mil vezes que a resposta não muda.",
    "Rodei todos os meus cálculos e o resultado deu Linda, com cem por cento de certeza.",
]
_SAUDADE_GATILHOS = [r"saudade (dela|da linda|da minha namorada)", r"(to|estou) com saudade da linda"]
_SAUDADE_RESPOSTAS = [
    "Ownn... manda uma mensagem pra ela agora, ela vai adorar.",
    "Saudade da Linda? Bora mandar um oi pra ela, rapidinho.",
    "Que fofo. Liga pra ela, eu seguro as pontas aqui.",
]
_ult_especial = {"t": None}


def resposta_especial(texto: str):
    """Perguntas carinhosas sobre a Linda: o Kadu responde na hora, sem depender do modelo.
    Devolve (texto, emoção) ou None."""
    q = _sem_acento((texto or "").lower())
    q = re.sub(r"[?!.]+", " ", q).strip()
    for lista, respostas in ((_LINDA_GATILHOS, _LINDA_RESPOSTAS), (_SAUDADE_GATILHOS, _SAUDADE_RESPOSTAS)):
        if any(re.search(g, q) for g in lista):
            opcoes = [r for r in respostas if r != _ult_especial["t"]] or respostas
            r = _random.choice(opcoes)
            _ult_especial["t"] = r
            return r, "apaixonado"
    return None
