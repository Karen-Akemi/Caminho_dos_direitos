"""Voz do Caminho dos Direitos: texto -> áudio com voz neural (mais humana) em português do Brasil.

Motores, do mais natural para o mais simples:
  1. edge-tts  — vozes neurais da Microsoft (Francisca, Thalita, Antonio). Grátis, precisa de internet.
  2. gTTS      — voz do Google Tradutor (a "voz de robô"). Fica só como reserva, se o 1 falhar.

O arquivo final é OGG/Opus mono: é o formato que o WhatsApp mostra como *mensagem de voz*
(com a bolinha de play e a onda), e não como arquivo de música.

No Colab:  !pip install -q edge-tts gTTS      (o ffmpeg já vem instalado)
"""
from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

VOZES = {
    "feminina": "pt-BR-FranciscaNeural",   # calma e clara: a padrão, boa para idosos
    "feminina2": "pt-BR-ThalitaNeural",    # mais jovem
    "masculina": "pt-BR-AntonioNeural",
}
# Mais devagar que o normal: o público inclui idosos e pessoas com pouca leitura.
VELOCIDADE_PADRAO = "-10%"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
# Siglas que a voz lê errado ("CPF" vira "cpf" emendado). Escritas como se fala.
SIGLAS = {
    "CPF": "cê pê éfe", "RG": "érre gê", "UBS": "u bê ésse", "BPC": "bê pê cê",
    "CadÚnico": "Cadastro Único", "CADÚNICO": "Cadastro Único", "e-SUS": "é sus",
    "CRAS": "Crás", "CREAS": "Creás", "INSS": "i ene ésse ésse", "NIS": "nís", "SUS": "sus",
}


def preparar_texto(texto: str) -> str:
    """Deixa o texto do jeito que se fala: datas, horários, valores e siglas por extenso."""
    t = texto
    t = re.sub(r"\bR\$\s*(\d[\d.]*)(,(\d{2}))?",
               lambda m: f"{m.group(1).replace('.', '')} reais" + (f" e {int(m.group(3))} centavos"
                                                                    if m.group(3) and int(m.group(3)) else ""), t)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})(/\d{2,4})?\b",
               lambda m: f"{int(m.group(1))} de {MESES[int(m.group(2)) - 1]}"
               if 1 <= int(m.group(2)) <= 12 else m.group(0), t)
    t = re.sub(r"\b(\d{1,2})h(\d{2})\b", lambda m: f"{int(m.group(1))} e {m.group(2)}", t)
    t = re.sub(r"\b(\d{1,2})h\b", lambda m: f"{int(m.group(1))} hora" + ("s" if int(m.group(1)) != 1 else ""), t)
    for sigla, fala in sorted(SIGLAS.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(rf"(?<![\w-]){re.escape(sigla)}(?![\w-])", fala, t)
    t = t.replace("nº", "número").replace("Nº", "número")
    t = re.sub(r"[•▪●]\s*", ", ", t)          # tópicos viram pausas
    t = re.sub(r"\s*\n+\s*", ". ", t)          # quebra de linha vira ponto (pausa)
    t = re.sub(r"\.\s*\.", ".", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def _rodar(coro):
    """Roda uma corrotina mesmo dentro do Colab/Jupyter (que já tem um loop de eventos ligado)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    resultado: dict = {}

    def alvo():
        try:
            resultado["ok"] = asyncio.run(coro)
        except BaseException as e:   # repassa o erro para quem chamou
            resultado["erro"] = e

    th = threading.Thread(target=alvo)
    th.start()
    th.join()
    if "erro" in resultado:
        raise resultado["erro"]
    return resultado.get("ok")


def _edge(texto: str, destino_mp3: Path, voz: str, velocidade: str, tom: str) -> None:
    import edge_tts
    com = edge_tts.Communicate(texto, VOZES.get(voz, voz), rate=velocidade, pitch=tom)
    _rodar(com.save(str(destino_mp3)))


def _gtts(texto: str, destino_mp3: Path) -> None:
    from gtts import gTTS
    gTTS(texto, lang="pt", tld="com.br").save(str(destino_mp3))


def para_ogg_opus(origem: Path, destino: Path) -> Path:
    """Converte para OGG/Opus mono 48 kHz (formato de mensagem de voz do WhatsApp)."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg não encontrado (no Colab ele já vem; no PC, instale o ffmpeg).")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(origem), "-ac", "1", "-ar", "48000",
                    "-c:a", "libopus", "-b:a", "32k", "-application", "voip", str(destino)], check=True)
    return destino


def falar(texto: str, arquivo: str | Path = "audio.ogg", voz: str = "feminina",
          velocidade: str = VELOCIDADE_PADRAO, tom: str = "+0Hz", motor: str = "auto") -> Path:
    """Texto -> arquivo de áudio. Devolve o caminho.

    voz: "feminina", "feminina2", "masculina" ou o nome de uma voz do edge-tts.
    velocidade: "-10%" = 10% mais devagar. tom: "-2Hz" deixa a voz um pouco mais grave.
    motor: "auto" (neural, com reserva gTTS), "neural" (só edge-tts) ou "gtts".
    Extensão .ogg -> mensagem de voz do WhatsApp; .mp3 -> mp3 comum.
    """
    arquivo = Path(arquivo)
    falado = preparar_texto(texto)
    with tempfile.TemporaryDirectory() as tmp:
        mp3 = Path(tmp) / "voz.mp3"
        usado = None
        if motor in ("auto", "neural"):
            try:
                _edge(falado, mp3, voz, velocidade, tom)
                usado = "neural (edge-tts)"
            except Exception as e:
                if motor == "neural":
                    raise
                print(f"[voz] voz neural indisponível ({type(e).__name__}); usando gTTS")
        if usado is None:
            _gtts(falado, mp3)
            usado = "gTTS"
        if arquivo.suffix.lower() == ".ogg":
            para_ogg_opus(mp3, arquivo)
        else:
            shutil.copyfile(mp3, arquivo)
    falar.ultimo_motor = usado   # para mostrar na demonstração qual motor foi usado
    return arquivo


falar.ultimo_motor = None
