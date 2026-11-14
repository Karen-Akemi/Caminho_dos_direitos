"""Caminho dos Direitos — servidor do WhatsApp (Cloud API da Meta), seguindo o manual da aula.

O que ele faz:
  • POST /lembretes  (o app chama)  -> envia o lembrete do encaminhamento como MENSAGEM-MODELO aprovada,
                                       com o botão "Ouvir em áudio". Só envia se houver consentimento.
  • POST /webhook    (a Meta chama) -> valida a assinatura, guarda cada evento uma vez só (wamid único) e:
        - botão "Ouvir em áudio" ou palavra OUVIR -> gera o áudio com voz neural e manda como mensagem de voz;
        - PARAR / SAIR / STOP  -> nunca mais envia lembrete àquele número;  VOLTAR / START -> religa;
        - outro texto          -> explica o que o número faz;
        - áudio, foto, arquivo -> "ainda não recebo arquivos";
        - status de entrega    -> atualiza o envio (enviada, entregue, lida, falhou).
  • GET  /webhook    (a Meta chama uma vez) -> verificação do endereço.

Sem WA_ACCESS_TOKEN ou WA_PHONE_ID roda em MODO DEMONSTRAÇÃO: nada sai para a Meta,
mas tudo o mais acontece (o áudio é gerado e o que seria enviado fica em bot.saida_demo).

Variáveis de ambiente (manual, Passo 1). Nunca no código, nunca no Git:
  WA_VERIFY_TOKEN  texto longo inventado por vocês (o mesmo do painel da Meta)
  WA_APP_SECRET    App Secret (Configurações > Básico)        -> valida X-Hub-Signature-256
  WA_ACCESS_TOKEN  token de acesso                             -> envia mensagens
  WA_PHONE_ID      ID do número de telefone                    -> entra na URL de envio
  WA_CHAVE_APP     senha que o app usa para chamar /lembretes  (opcional)
  WA_CHAVE_HASH    chave do HMAC que guarda o telefone como hash (opcional; padrão = WA_APP_SECRET)
  WA_TEMPLATE      nome da mensagem-modelo aprovada (padrão: lembrete_encaminhamento)
  WA_GRAPH_VERSAO  versão do Graph API (padrão v21.0, a do manual: confira a atual na documentação)

Rodar no PC:   pip install fastapi uvicorn httpx edge-tts gTTS
               uvicorn servidor_whatsapp:app --port 8000      e, em outro terminal,  ngrok http 8000
No Colab: notebook servidor_whatsapp_colab.ipynb.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import sqlite3
import threading
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("whatsapp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Texto para cadastrar no painel da Meta (Gerenciador do WhatsApp > Modelos de mensagem).
# Categoria: Utilidade · Idioma: Português (BR) · Botão de resposta rápida: "Ouvir em áudio".
TEMPLATE_TEXTO = ("Olá, {{1}}! Lembrete do seu atendimento: {{2}}, dia {{3}}, às {{4}}. "
                  "Leve: {{5}}. Se não puder ir, avise o seu agente. Para não receber mais, responda PARAR.")
BOTAO_AUDIO = "Ouvir em áudio"
PALAVRAS_PARAR = {"parar", "sair", "stop", "cancelar"}
PALAVRAS_VOLTAR = {"voltar", "start", "iniciar"}
PALAVRAS_OUVIR = {"ouvir", "ouvir em audio", "audio", "áudio"}
LIMITE_PROATIVO_DIA = 3          # manual, seção 8.7: limite de mensagens proativas por pessoa
GUARDAR_CONVERSA_DIAS = 30       # manual, seção 8.4: por quanto tempo guarda e depois apaga
LIMITE_TEXTO = 4096              # tamanho máximo de uma mensagem de texto

MSG_PAROU = ("Pronto: você não vai mais receber lembretes por este número. "
             "Se quiser voltar a receber, é só mandar VOLTAR.")
MSG_VOLTOU = "Combinado: você voltou a receber os lembretes. Para parar, mande PARAR."
MSG_AJUDA = ("Oi! Este número manda lembretes dos seus atendimentos (Caminho dos Direitos). "
             "Para ouvir o último lembrete, mande OUVIR. Para não receber mais, mande PARAR. "
             "Para outras dúvidas, fale com o seu agente ou com o CRAS.")
MSG_ARQUIVO = ("Ainda não recebo áudios, fotos ou arquivos. Para ouvir o lembrete, mande OUVIR. "
               "Para outras dúvidas, fale com o seu agente ou com o CRAS.")
MSG_SEM_LEMBRETE = "Não achei nenhum lembrete para este número. Fale com o seu agente."


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _simples(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").strip().lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def mascarar(tel: str) -> str:
    """5511987650412 -> +55 11 ****-0412 (o número inteiro nunca vai para o log)."""
    d = re.sub(r"\D", "", tel or "")
    if len(d) in (10, 11):
        d = "55" + d
    return f"+{d[:2]} {d[2:4]} ****-{d[-4:]}" if len(d) >= 10 else "****"


def normalizar_telefone(tel: str) -> str:
    """'(11) 98765-4321' -> '5511987654321' (só dígitos, com 55, sem +), como a API pede."""
    d = re.sub(r"\D", "", tel or "")
    if len(d) in (10, 11):
        d = "55" + d
    if not 12 <= len(d) <= 13:
        raise ValueError("telefone inválido: use DDD + número")
    return d


@dataclass
class Lembrete:
    id_encaminhamento: str
    nome: str               # como a pessoa é chamada (apelido), nunca o nome completo
    local: str
    data: str               # "18/11"
    hora: str               # "9h"
    documentos: str
    formato: str = "texto_e_audio"   # "texto", "audio" ou "texto_e_audio" (dim_caso.formato_lembrete)

    def variaveis(self) -> list[str]:
        # Variável de modelo não pode ter quebra de linha nem espaços seguidos (regra da Meta)
        return [re.sub(r"\s+", " ", v).strip()[:200]
                for v in (self.nome, self.local, self.data, self.hora, self.documentos)]

    @property
    def texto(self) -> str:
        t = TEMPLATE_TEXTO
        for i, v in enumerate(self.variaveis(), 1):
            t = t.replace("{{%d}}" % i, v)
        return t

    @property
    def texto_falado(self) -> str:
        """Versão para ouvir: mais curta e com pausas."""
        return (f"Olá, {self.nome}! Aqui é o lembrete do seu atendimento. "
                f"Você vai no {self.local}, no dia {self.data}, às {self.hora}. "
                f"Não esqueça de levar: {self.documentos}. "
                f"Se não puder ir, avise o seu agente. Vou repetir o dia e a hora: "
                f"dia {self.data}, às {self.hora}.")


class Banco:
    """SQLite com as regras do manual: wamid único, status guardado mesmo fora de ordem, telefone em hash."""

    def __init__(self, caminho: str | Path = "whatsapp.db"):
        self.con = sqlite3.connect(str(caminho), check_same_thread=False)
        self.trava = threading.Lock()
        self.con.executescript("""
        CREATE TABLE IF NOT EXISTS mensagem_recebida (
            wamid TEXT PRIMARY KEY, tel_hash TEXT, tipo TEXT, conteudo TEXT, recebida_em TEXT);
        CREATE TABLE IF NOT EXISTS contato (
            tel_hash TEXT PRIMARY KEY, aceitou_em TEXT, origem_aceite TEXT,
            nao_enviar INTEGER DEFAULT 0, atualizado_em TEXT, ultimo_lembrete TEXT);
        CREATE TABLE IF NOT EXISTS lembrete (
            id_encaminhamento TEXT PRIMARY KEY, tel_hash TEXT, dados TEXT, criado_em TEXT);
        CREATE TABLE IF NOT EXISTS envio (
            id_meta TEXT UNIQUE, tel_hash TEXT, tipo TEXT, id_encaminhamento TEXT,
            status TEXT, erro TEXT, criado_em TEXT);
        CREATE TABLE IF NOT EXISTS status_pendente (id_meta TEXT, status TEXT, em TEXT);
        """)

    def x(self, sql: str, args=()):
        with self.trava, self.con:
            return self.con.execute(sql, args).fetchall()

    # --- recebidas: grava antes de responder; repetida = descarta
    def guardar_recebida(self, wamid, tel_hash, tipo, conteudo) -> bool:
        try:
            self.x("INSERT INTO mensagem_recebida VALUES (?,?,?,?,?)", (wamid, tel_hash, tipo, conteudo, _agora()))
            return True
        except sqlite3.IntegrityError:
            return False

    # --- consentimento (opt-in / opt-out)
    def registrar_aceite(self, tel_hash, aceitou_em, origem):
        self.x("""INSERT INTO contato (tel_hash, aceitou_em, origem_aceite, nao_enviar, atualizado_em)
                  VALUES (?,?,?,0,?) ON CONFLICT(tel_hash) DO UPDATE SET
                  aceitou_em=excluded.aceitou_em, origem_aceite=excluded.origem_aceite,
                  atualizado_em=excluded.atualizado_em""", (tel_hash, aceitou_em, origem, _agora()))

    def contato(self, tel_hash) -> dict | None:
        r = self.x("SELECT aceitou_em, nao_enviar, ultimo_lembrete FROM contato WHERE tel_hash=?", (tel_hash,))
        return dict(zip(("aceitou_em", "nao_enviar", "ultimo_lembrete"), r[0])) if r else None

    def marcar_nao_enviar(self, tel_hash, valor: bool):
        self.x("""INSERT INTO contato (tel_hash, nao_enviar, atualizado_em) VALUES (?,?,?)
                  ON CONFLICT(tel_hash) DO UPDATE SET nao_enviar=excluded.nao_enviar,
                  atualizado_em=excluded.atualizado_em""", (tel_hash, int(valor), _agora()))

    # --- lembretes
    def guardar_lembrete(self, tel_hash, lem: Lembrete):
        self.x("INSERT OR REPLACE INTO lembrete VALUES (?,?,?,?)",
               (lem.id_encaminhamento, tel_hash, json.dumps(asdict(lem), ensure_ascii=False), _agora()))
        self.x("UPDATE contato SET ultimo_lembrete=? WHERE tel_hash=?", (lem.id_encaminhamento, tel_hash))

    def lembrete(self, id_enc, tel_hash) -> Lembrete | None:
        r = self.x("SELECT dados FROM lembrete WHERE id_encaminhamento=? AND tel_hash=?", (id_enc, tel_hash))
        return Lembrete(**json.loads(r[0][0])) if r else None

    # --- envios e status de entrega (o status pode chegar antes de o envio ser gravado)
    def guardar_envio(self, id_meta, tel_hash, tipo, id_enc, status, erro=None):
        self.x("INSERT INTO envio VALUES (?,?,?,?,?,?,?)", (id_meta, tel_hash, tipo, id_enc, status, erro, _agora()))
        for (st,) in self.x("SELECT status FROM status_pendente WHERE id_meta=? ORDER BY em", (id_meta,)):
            self.x("UPDATE envio SET status=? WHERE id_meta=?", (st, id_meta))
        self.x("DELETE FROM status_pendente WHERE id_meta=?", (id_meta,))

    def atualizar_status(self, id_meta, status):
        if self.x("SELECT 1 FROM envio WHERE id_meta=?", (id_meta,)):
            self.x("UPDATE envio SET status=? WHERE id_meta=?", (status, id_meta))
        else:
            self.x("INSERT INTO status_pendente VALUES (?,?,?)", (id_meta, status, _agora()))

    def proativos_hoje(self, tel_hash) -> int:
        desde = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
        return self.x("SELECT COUNT(*) FROM envio WHERE tel_hash=? AND tipo='template' AND criado_em>=? "
                      "AND status!='falhou'", (tel_hash, desde))[0][0]

    def apagar_antigas(self, dias=GUARDAR_CONVERSA_DIAS):
        limite = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat(timespec="seconds")
        self.x("DELETE FROM mensagem_recebida WHERE recebida_em<?", (limite,))
        self.x("DELETE FROM lembrete WHERE criado_em<?", (limite,))


class ErroEnvio(Exception):
    pass


class Bot:
    def __init__(self, banco: Banco | None = None, pasta_audio: str | Path = "audios"):
        self.verify_token = os.getenv("WA_VERIFY_TOKEN", "")
        self.app_secret = os.getenv("WA_APP_SECRET", "")
        self.token = os.getenv("WA_ACCESS_TOKEN", "")
        self.phone_id = os.getenv("WA_PHONE_ID", "")
        self.template = os.getenv("WA_TEMPLATE", "lembrete_encaminhamento")
        self.graph = f"https://graph.facebook.com/{os.getenv('WA_GRAPH_VERSAO', 'v21.0')}"
        self.chave_hash = (os.getenv("WA_CHAVE_HASH") or self.app_secret or "troque-esta-chave").encode()
        self.demonstracao = not (self.token and self.phone_id)
        self.banco = banco or Banco()
        self.pasta_audio = Path(pasta_audio)
        self.pasta_audio.mkdir(exist_ok=True)
        self.saida_demo: list[dict] = []     # o que teria ido para a Meta (modo demonstração)
        self._contador_demo = 0

    def hash_tel(self, tel: str) -> str:
        return hmac.new(self.chave_hash, normalizar_telefone(tel).encode(), hashlib.sha256).hexdigest()

    # ================= Passo 2: receber =================
    def verificar(self, modo: str, token: str, desafio: str) -> tuple[int, str]:
        if modo == "subscribe" and self.verify_token and hmac.compare_digest(token or "", self.verify_token):
            return 200, desafio
        return 403, "proibido"

    def assinatura_ok(self, corpo: bytes, assinatura: str) -> bool:
        if not self.app_secret:
            return False
        esperado = "sha256=" + hmac.new(self.app_secret.encode(), corpo, hashlib.sha256).hexdigest()
        return hmac.compare_digest(esperado, assinatura or "")

    def receber(self, corpo: bytes, assinatura: str) -> tuple[int, list[tuple]]:
        """Valida, grava e devolve (status HTTP, tarefas para rodar em segundo plano).
        Se o banco falhar, devolve 500: a Meta tenta de novo e nada se perde."""
        if not self.assinatura_ok(corpo, assinatura):
            return 401, []
        try:
            dados = json.loads(corpo)
        except ValueError:
            return 400, []
        tarefas = []
        try:
            for entry in dados.get("entry", []):
                for change in entry.get("changes", []):
                    valor = change.get("value", {})
                    if valor.get("metadata", {}).get("phone_number_id") != self.phone_id:
                        continue                                   # evento de outro número: ignora
                    for st in valor.get("statuses", []):
                        self.banco.atualizar_status(st["id"], st["status"])
                        if st["status"] == "failed":
                            log.warning("envio %s falhou: %s", st["id"], st.get("errors"))
                    for m in valor.get("messages", []):
                        tipo, conteudo = self._ler(m)
                        tel_hash = self.hash_tel(m["from"])
                        if not self.banco.guardar_recebida(m["id"], tel_hash, tipo, conteudo):
                            continue                               # já recebida: descarta repetida
                        log.info("recebida de %s: %s", mascarar(m["from"]), tipo)
                        tarefas.append((m["from"], tipo, conteudo))
        except sqlite3.Error:
            log.exception("banco falhou")
            return 500, []
        return 200, tarefas

    @staticmethod
    def _ler(m: dict) -> tuple[str, str]:
        t = m.get("type")
        if t == "text":
            return "texto", m["text"]["body"][:1000]
        if t == "button":                                   # botão de resposta rápida de mensagem-modelo
            return "botao", m["button"].get("payload") or m["button"].get("text", "")
        if t == "interactive":                              # botão de mensagem interativa
            r = m["interactive"].get("button_reply") or m["interactive"].get("list_reply") or {}
            return "botao", r.get("id") or r.get("title", "")
        return "arquivo", t or "desconhecido"               # áudio, imagem, documento: não guarda o conteúdo

    def processar(self, tel: str, tipo: str, conteudo: str) -> None:
        """Roda fora da requisição do webhook (manual: responda rápido, trabalho pesado em segundo plano)."""
        try:
            tel_hash = self.hash_tel(tel)
            palavra = _simples(conteudo)
            if tipo == "arquivo":
                return self.enviar_texto(tel, MSG_ARQUIVO)
            if palavra in PALAVRAS_PARAR:
                self.banco.marcar_nao_enviar(tel_hash, True)
                return self.enviar_texto(tel, MSG_PAROU)
            if palavra in PALAVRAS_VOLTAR:
                self.banco.marcar_nao_enviar(tel_hash, False)
                return self.enviar_texto(tel, MSG_VOLTOU)
            if tipo == "botao" and conteudo.startswith("AUDIO:"):
                return self.responder_com_audio(tel, conteudo.split(":", 1)[1])
            if palavra in PALAVRAS_OUVIR or palavra == _simples(BOTAO_AUDIO):
                c = self.banco.contato(tel_hash)
                if c and c["ultimo_lembrete"]:
                    return self.responder_com_audio(tel, c["ultimo_lembrete"])
                return self.enviar_texto(tel, MSG_SEM_LEMBRETE)
            return self.enviar_texto(tel, MSG_AJUDA)
        except ErroEnvio as e:
            log.error("não enviado para %s: %s", mascarar(tel), e)   # falha é falha: fica registrada

    def responder_com_audio(self, tel: str, id_enc: str) -> None:
        lem = self.banco.lembrete(id_enc, self.hash_tel(tel))
        if lem is None:                       # o lembrete precisa ser deste número: ninguém ouve o de outro
            return self.enviar_texto(tel, MSG_SEM_LEMBRETE)
        from voz import falar
        nome = re.sub(r"\W", "_", id_enc)
        arquivo = falar(lem.texto_falado, self.pasta_audio / f"lembrete_{nome}.ogg")
        self.enviar_audio(tel, arquivo, id_enc)

    # ================= Passo 3 e 4: enviar =================
    def _post(self, caminho: str, tipo: str, tel: str, id_enc: str | None, **kw) -> str:
        tel_hash = self.hash_tel(tel)
        if self.demonstracao:
            self._contador_demo += 1
            id_meta = f"wamid.DEMO{self._contador_demo}"
            self.saida_demo.append({"para": mascarar(tel), "tipo": tipo, **{k: v for k, v in kw.items() if k != "files"}})
            self.banco.guardar_envio(id_meta, tel_hash, tipo, id_enc, "demonstracao")
            return id_meta
        import httpx
        try:
            r = httpx.post(f"{self.graph}/{self.phone_id}/{caminho}", timeout=20,
                           headers={"Authorization": f"Bearer {self.token}"}, **kw)
            corpo = r.json()
        except (httpx.HTTPError, ValueError) as e:
            self.banco.guardar_envio(None, tel_hash, tipo, id_enc, "falhou", f"rede: {type(e).__name__}")
            raise ErroEnvio(f"erro de rede: {type(e).__name__}") from e
        if r.status_code >= 400 or "error" in corpo:
            msg = corpo.get("error", {}).get("message", f"HTTP {r.status_code}")
            self.banco.guardar_envio(None, tel_hash, tipo, id_enc, "falhou", msg)
            raise ErroEnvio(msg)
        if caminho == "media":
            return corpo["id"]
        id_meta = corpo["messages"][0]["id"]
        self.banco.guardar_envio(id_meta, tel_hash, tipo, id_enc, "aceita")   # guarda o id: liga aos status
        return id_meta

    def _mensagem(self, tel: str, tipo: str, conteudo: dict, id_enc: str | None = None) -> str:
        corpo = {"messaging_product": "whatsapp", "to": normalizar_telefone(tel), "type": tipo, tipo: conteudo}
        return self._post("messages", "template" if tipo == "template" else tipo, tel, id_enc, json=corpo)

    def enviar_texto(self, tel: str, texto: str) -> list[str]:
        """Texto livre: só vale dentro da janela de 24 h (a pessoa escreveu primeiro). Divide se for longo."""
        partes = [texto[i:i + LIMITE_TEXTO] for i in range(0, len(texto), LIMITE_TEXTO)] or [""]
        return [self._mensagem(tel, "text", {"body": p}) for p in partes]

    def enviar_audio(self, tel: str, arquivo: Path, id_enc: str | None = None) -> str:
        """Sobe o .ogg (Opus) para a Meta e manda como mensagem de voz."""
        arquivo = Path(arquivo)
        if self.demonstracao:
            media_id = "MEDIA_DEMO"
        else:
            with open(arquivo, "rb") as f:
                media_id = self._post("media", "upload", tel, id_enc,
                                      data={"messaging_product": "whatsapp", "type": "audio/ogg"},
                                      files={"file": (arquivo.name, f, "audio/ogg")})
        id_meta = self._mensagem(tel, "audio", {"id": media_id}, id_enc)
        if self.saida_demo:
            self.saida_demo[-1]["arquivo"] = str(arquivo)
        return id_meta

    def enviar_lembrete(self, tel: str, lem: Lembrete, aceitou_em: str | None = None,
                        origem_aceite: str = "app: tela de contato do caso") -> str:
        """Mensagem proativa = mensagem-modelo aprovada (fora da janela de 24 h só ela sai).
        Exige o aceite da pessoa e respeita PARAR e o limite diário."""
        tel_hash = self.hash_tel(tel)
        if aceitou_em:
            self.banco.registrar_aceite(tel_hash, aceitou_em, origem_aceite)
        c = self.banco.contato(tel_hash)
        if not c or not c["aceitou_em"]:
            raise ErroEnvio("sem registro de que a pessoa aceitou receber lembretes")
        if c["nao_enviar"]:
            raise ErroEnvio("a pessoa pediu para parar (PARAR)")
        if self.banco.proativos_hoje(tel_hash) >= LIMITE_PROATIVO_DIA:
            raise ErroEnvio("limite de lembretes do dia atingido")
        self.banco.guardar_lembrete(tel_hash, lem)
        componentes = [{"type": "body", "parameters": [{"type": "text", "text": v} for v in lem.variaveis()]}]
        if lem.formato in ("audio", "texto_e_audio"):
            componentes.append({"type": "button", "sub_type": "quick_reply", "index": "0",
                                "parameters": [{"type": "payload", "payload": f"AUDIO:{lem.id_encaminhamento}"}]})
        return self._mensagem(tel, "template", {"name": self.template, "language": {"code": "pt_BR"},
                                                "components": componentes}, lem.id_encaminhamento)

    def enviar_lembrete_na_janela(self, tel: str, lem: Lembrete, aceitou_em: str | None = None) -> list[str]:
        """Para a demonstração enquanto o modelo não é aprovado: só funciona se a pessoa mandou mensagem
        ao número nas últimas 24 h. Manda o texto e, se o formato pedir, o áudio logo em seguida."""
        tel_hash = self.hash_tel(tel)
        if aceitou_em:
            self.banco.registrar_aceite(tel_hash, aceitou_em, "app: tela de contato do caso")
        c = self.banco.contato(tel_hash)
        if not c or not c["aceitou_em"] or c["nao_enviar"]:
            raise ErroEnvio("sem aceite registrado ou a pessoa pediu para parar")
        self.banco.guardar_lembrete(tel_hash, lem)
        ids = []
        if lem.formato in ("texto", "texto_e_audio"):
            ids += self.enviar_texto(tel, lem.texto + "\n\nPara ouvir este lembrete, mande OUVIR.")
        if lem.formato in ("audio", "texto_e_audio"):
            self.responder_com_audio(tel, lem.id_encaminhamento)
        return ids


# ================= Simulação (para testar sem a Meta) =================
def evento_simulado(bot: Bot, tel: str, *, texto: str | None = None, botao: str | None = None,
                    tipo: str | None = None, wamid: str | None = None) -> tuple[bytes, str]:
    """Monta um POST igual ao da Meta, já assinado com o App Secret. Devolve (corpo, assinatura)."""
    if botao is not None:
        m = {"type": "button", "button": {"payload": botao, "text": BOTAO_AUDIO}}
    elif texto is not None:
        m = {"type": "text", "text": {"body": texto}}
    else:
        m = {"type": tipo or "audio", (tipo or "audio"): {"id": "123"}}
    m.update({"from": normalizar_telefone(tel), "id": wamid or f"wamid.TESTE{datetime.now().timestamp()}",
              "timestamp": "0"})
    corpo = json.dumps({"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {
        "messaging_product": "whatsapp", "metadata": {"phone_number_id": bot.phone_id}, "messages": [m]}}]}]}).encode()
    return corpo, "sha256=" + hmac.new(bot.app_secret.encode(), corpo, hashlib.sha256).hexdigest()


# ================= FastAPI (camada fina por cima do Bot) =================
def criar_app(bot: Bot | None = None):
    from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query, Request
    from fastapi.responses import PlainTextResponse
    from pydantic import BaseModel

    bot = bot or Bot()
    app = FastAPI(title="Caminho dos Direitos — WhatsApp")
    app.state.bot = bot

    class PedidoLembrete(BaseModel):
        telefone: str
        aceitou_em: str | None = None       # data do consentimento registrada no app
        id_encaminhamento: str
        nome: str
        local: str
        data: str
        hora: str
        documentos: str
        formato: str = "texto_e_audio"

    @app.get("/webhook")
    def verificar(mode: str = Query("", alias="hub.mode"), token: str = Query("", alias="hub.verify_token"),
                  challenge: str = Query("", alias="hub.challenge")):
        status, corpo = bot.verificar(mode, token, challenge)
        if status != 200:
            raise HTTPException(status)
        return PlainTextResponse(corpo)

    @app.post("/webhook")
    async def receber(req: Request, bg: BackgroundTasks):
        corpo = await req.body()                     # bytes crus: a assinatura é calculada sobre eles
        status, tarefas = bot.receber(corpo, req.headers.get("X-Hub-Signature-256", ""))
        if status != 200:
            raise HTTPException(status)
        for t in tarefas:
            bg.add_task(bot.processar, *t)          # função comum: o FastAPI roda em outra thread
        return {"ok": True}

    @app.post("/lembretes")
    def lembrete(p: PedidoLembrete, x_chave_app: str = Header("")):
        chave = os.getenv("WA_CHAVE_APP")
        if chave and not hmac.compare_digest(x_chave_app, chave):
            raise HTTPException(401)
        lem = Lembrete(p.id_encaminhamento, p.nome, p.local, p.data, p.hora, p.documentos, p.formato)
        try:
            id_meta = bot.enviar_lembrete(p.telefone, lem, p.aceitou_em)
        except (ErroEnvio, ValueError) as e:
            raise HTTPException(422, str(e))
        return {"enviado": True, "id_mensagem": id_meta, "demonstracao": bot.demonstracao}

    @app.get("/saude")
    def saude():
        return {"ok": True, "demonstracao": bot.demonstracao}

    return app


try:            # "uvicorn servidor_whatsapp:app" funciona direto se o FastAPI estiver instalado
    app = criar_app()
except ImportError:
    app = None
