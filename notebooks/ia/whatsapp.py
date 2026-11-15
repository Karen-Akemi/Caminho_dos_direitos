"""
Caminho dos Direitos — Lembretes por WhatsApp em texto e em áudio (acessibilidade)

Fluxo (segue a regra do WhatsApp Business: fora da janela de 24 h só vale mensagem-modelo aprovada):

    1. Agente salva o encaminhamento (tela 07)  ->  enviar_lembrete()
       manda a mensagem-modelo "lembrete_atendimento" (texto) com o botão "Ouvir em áudio".
    2. A pessoa toca no botão  ->  o WhatsApp chama o webhook  ->  tratar_webhook()
       a resposta abre a janela de 24 h e o sistema manda o MESMO lembrete como mensagem de voz.
    3. Se a pessoa já estiver com a janela aberta (respondeu há menos de 24 h),
       enviar_lembrete(..., audio_direto=True) manda texto e áudio de uma vez.

Modo demonstração (padrão quando não há token): nada sai para a internet. As mensagens que
seriam enviadas ficam em wa.enviados e o áudio é gerado no Colab para tocar na apresentação.

Para enviar de verdade (número de teste gratuito da Meta, até 5 destinatários cadastrados):
    WHATSAPP_TOKEN=...           token do app em developers.facebook.com
    WHATSAPP_PHONE_ID=...        Phone number ID do número de teste
e cadastrar a mensagem-modelo TEMPLATE_LEMBRETE no Gerenciador do WhatsApp (categoria Utilidade).

No Colab: !pip install -q gTTS requests     (o ffmpeg já vem instalado)
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

API = "https://graph.facebook.com/v25.0"

# Mensagem-modelo para cadastrar na Meta (o texto exato precisa ser aprovado antes do uso)
TEMPLATE_LEMBRETE = {
    "name": "lembrete_atendimento",
    "category": "UTILITY",
    "language": "pt_BR",
    "components": [
        {"type": "BODY",
         "text": ("Olá, {{1}}! Seu atendimento no {{2}} é dia {{3}} às {{4}}. "
                  "Leve: {{5}}. Se preferir, toque no botão para ouvir esta mensagem."),
         "example": {"body_text": [["Dona Cida", "CRAS Jardim Ângela", "18/11", "9h",
                                     "RG ou certidão, CPF e comprovante de endereço"]]}},
        {"type": "BUTTONS", "buttons": [{"type": "QUICK_REPLY", "text": "Ouvir em áudio"}]},
    ],
}
BOTAO_AUDIO = "OUVIR_AUDIO"


# --------------------------------------------------------------------------------------
# Texto do lembrete
# --------------------------------------------------------------------------------------
@dataclass
class Lembrete:
    id_encaminhamento: str
    apelido: str          # como a pessoa quer ser chamada (o app não guarda nome completo)
    local: str
    data: str             # "18/11"
    hora: str             # "9h"
    levar: str

    @property
    def parametros(self) -> list[str]:
        return [self.apelido, self.local, self.data, self.hora, self.levar]

    @property
    def texto(self) -> str:
        return (f"Olá, {self.apelido}! Seu atendimento no {self.local} é dia {self.data} às {self.hora}. "
                f"Leve: {self.levar}.")


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
SIGLAS = {  # como a voz deve ler (siglas soletradas ou por extenso)
    r"\bCadÚnico\b": "Cadastro Único", r"\bCADÚNICO\b": "Cadastro Único",
    r"\bBPC\b": "B P C", r"\bRG\b": "R G", r"\bCPF\b": "C P F", r"\bCIN\b": "carteira de identidade",
    r"\bINSS\b": "I N S S", r"\bUBS\b": "U B S", r"\bCRAS\b": "Cras", r"\bSUS\b": "SUS",
}


def texto_para_fala(texto: str) -> str:
    """Prepara o texto para a voz: tira formatação e emoji, lê datas, horas, dinheiro e siglas por extenso."""
    t = re.sub(r"[*_~`#>]", "", texto)
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿️]", "", t)
    t = re.sub(r"\bR\$\s*([\d.]+),(\d{2})", lambda m: f"{m.group(1)} reais e {int(m.group(2))} centavos", t)
    t = re.sub(r"\bR\$\s*([\d.]+)", r"\1 reais", t)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})(/\d{2,4})?\b",
               lambda m: f"{int(m.group(1))} de {MESES[int(m.group(2)) - 1]}" if 1 <= int(m.group(2)) <= 12 else m.group(0), t)
    t = re.sub(r"\b(\d{1,2})h(\d{2})\b", r"\1 horas e \2", t)
    t = re.sub(r"\b(\d{1,2})h\b", lambda m: f"{m.group(1)} hora" + ("" if m.group(1) == "1" else "s"), t)
    for padrao, fala in SIGLAS.items():
        t = re.sub(padrao, fala, t)
    t = re.sub(r"\s*→\s*", ". ", t)
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------------------------
# Texto -> áudio (mensagem de voz do WhatsApp: .ogg, codec Opus, mono)
# --------------------------------------------------------------------------------------
def falar(texto: str, saida: str | Path = "lembrete.ogg", lento: bool = False) -> Path:
    """Gera o áudio em português do Brasil. Devolve .ogg/Opus (aparece como mensagem de voz);
    se não houver ffmpeg, devolve .mp3 (chega como áudio comum)."""
    from gtts import gTTS   # voz do Google, pt-BR; precisa de internet (no Colab funciona)

    saida = Path(saida)
    mp3 = saida.with_suffix(".mp3")
    gTTS(texto_para_fala(texto), lang="pt", tld="com.br", slow=lento).save(str(mp3))
    if not shutil.which("ffmpeg"):
        return mp3
    ogg = saida.with_suffix(".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1",
                    "-c:a", "libopus", "-b:a", "32k", str(ogg)], check=True)
    mp3.unlink(missing_ok=True)
    return ogg


# --------------------------------------------------------------------------------------
# Cliente da WhatsApp Cloud API
# --------------------------------------------------------------------------------------
def normalizar_telefone(tel: str) -> str:
    """'(11) 98765-4321' -> '5511987654321' (formato que a API usa, sem '+')."""
    d = re.sub(r"\D", "", tel)
    if len(d) in (10, 11):
        d = "55" + d
    if not (12 <= len(d) <= 13 and d.startswith("55")):
        raise ValueError(f"Telefone inválido: {tel}")
    return d


@dataclass
class WhatsApp:
    token: str | None = None
    phone_id: str | None = None
    demonstracao: bool | None = None
    enviados: list = field(default_factory=list)   # registro do que foi (ou seria) enviado

    def __post_init__(self):
        self.token = self.token or os.getenv("WHATSAPP_TOKEN")
        self.phone_id = self.phone_id or os.getenv("WHATSAPP_PHONE_ID")
        if self.demonstracao is None:
            self.demonstracao = not (self.token and self.phone_id)

    # --- chamadas HTTP ---
    def _post(self, caminho: str, json: dict | None = None, files=None, data=None) -> dict:
        self.enviados.append({"caminho": caminho, "json": json, "arquivo": files and str(files["file"][0])})
        if self.demonstracao:
            return {"demonstracao": True, "id": f"demo-{len(self.enviados)}"}
        import requests
        r = requests.post(f"{API}/{self.phone_id}/{caminho}", json=json, files=files, data=data,
                          headers={"Authorization": f"Bearer {self.token}"}, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"WhatsApp respondeu {r.status_code}: {r.text}")
        return r.json()

    def _mensagem(self, para: str, tipo: str, conteudo: dict) -> dict:
        return self._post("messages", json={"messaging_product": "whatsapp", "recipient_type": "individual",
                                            "to": normalizar_telefone(para), "type": tipo, tipo: conteudo})

    # --- tipos de mensagem ---
    def enviar_texto(self, para: str, texto: str) -> dict:
        """Texto livre: só funciona com a janela de 24 h aberta (a pessoa respondeu há menos de 24 h)."""
        return self._mensagem(para, "text", {"preview_url": False, "body": texto[:4096]})

    def enviar_template(self, para: str, parametros: list[str], id_encaminhamento: str,
                        nome: str = TEMPLATE_LEMBRETE["name"], idioma: str = "pt_BR") -> dict:
        """Mensagem-modelo aprovada (funciona fora da janela). O botão leva o id do encaminhamento."""
        return self._mensagem(para, "template", {
            "name": nome, "language": {"code": idioma},
            "components": [
                {"type": "body", "parameters": [{"type": "text", "text": p} for p in parametros]},
                {"type": "button", "sub_type": "quick_reply", "index": "0",
                 "parameters": [{"type": "payload", "payload": f"{BOTAO_AUDIO}|{id_encaminhamento}"}]},
            ]})

    def subir_audio(self, caminho: str | Path) -> str:
        caminho = Path(caminho)
        mime = "audio/ogg" if caminho.suffix == ".ogg" else "audio/mpeg"
        with open(caminho, "rb") as f:
            r = self._post("media", files={"file": (caminho.name, f, mime)},
                           data={"messaging_product": "whatsapp", "type": mime})
        return r["id"]

    def enviar_audio(self, para: str, caminho: str | Path) -> dict:
        """Mensagem de voz (.ogg/Opus) ou áudio comum (.mp3)."""
        media_id = self.subir_audio(caminho)
        conteudo = {"id": media_id}
        if Path(caminho).suffix == ".ogg":
            conteudo["voice"] = True
        return self._mensagem(para, "audio", conteudo)

    # --- fluxo do app ---
    def enviar_lembrete(self, para: str, lembrete: Lembrete, audio_direto: bool = False,
                        pasta_audio: str | Path = ".") -> list[dict]:
        """Passo 1: lembrete em texto com botão 'Ouvir em áudio'.
        audio_direto=True só quando a janela de 24 h já está aberta: manda texto e áudio juntos."""
        if audio_direto:
            ogg = falar(lembrete.texto, Path(pasta_audio) / f"lembrete_{lembrete.id_encaminhamento}.ogg")
            return [self.enviar_texto(para, lembrete.texto), self.enviar_audio(para, ogg)]
        return [self.enviar_template(para, lembrete.parametros, lembrete.id_encaminhamento)]


def tratar_webhook(corpo: dict, wa: WhatsApp, buscar_lembrete, pasta_audio: str | Path = ".") -> list[dict]:
    """Passo 2: recebe o aviso do WhatsApp. Se for o toque em 'Ouvir em áudio', manda o áudio.

    buscar_lembrete(id_encaminhamento) -> Lembrete   (no app real, vem do banco de dados)
    """
    respostas = []
    for entrada in corpo.get("entry", []):
        for mudanca in entrada.get("changes", []):
            for msg in mudanca.get("value", {}).get("messages", []):
                payload = (msg.get("button", {}).get("payload")                                # botão de mensagem-modelo
                           or msg.get("interactive", {}).get("button_reply", {}).get("id", ""))  # botão interativo
                if not payload or not payload.startswith(BOTAO_AUDIO + "|"):
                    continue
                lembrete = buscar_lembrete(payload.split("|", 1)[1])
                if lembrete is None:
                    continue
                ogg = falar(lembrete.texto, Path(pasta_audio) / f"lembrete_{lembrete.id_encaminhamento}.ogg")
                respostas.append(wa.enviar_audio(msg["from"], ogg))
    return respostas


def toque_simulado(telefone: str, id_encaminhamento: str) -> dict:
    """Corpo de webhook igual ao que o WhatsApp manda quando a pessoa toca no botão (para testar sem servidor)."""
    return {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {
        "messaging_product": "whatsapp",
        "messages": [{"from": normalizar_telefone(telefone), "type": "button",
                      "button": {"text": "Ouvir em áudio", "payload": f"{BOTAO_AUDIO}|{id_encaminhamento}"}}]}}]}]}


# Servidor do webhook (para rodar fora do Colab; o WhatsApp exige uma URL https pública):
#
#   from flask import Flask, request
#   app = Flask(__name__); wa = WhatsApp()
#   @app.get("/webhook")                       # verificação feita uma vez pela Meta
#   def verificar():
#       ok = request.args.get("hub.verify_token") == os.getenv("WEBHOOK_VERIFY_TOKEN")
#       return (request.args.get("hub.challenge"), 200) if ok else ("", 403)
#   @app.post("/webhook")
#   def receber():
#       tratar_webhook(request.get_json(), wa, buscar_lembrete_no_banco)
#       return "", 200
