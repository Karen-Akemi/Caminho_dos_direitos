"""Caminho dos Direitos — anotação por voz com IA.

O agente fala (ou digita) a anotação da visita. Este módulo:
  1. grava pelo microfone (Colab) ou recebe um arquivo de áudio, transcreve com Whisper e apaga o áudio;
  2. remove os dados clínicos (pressão, peso, altura, glicemia, doença, remédio) e avisa: registre no e-SUS;
  3. organiza o texto filtrado em um resumo (situação, prioridade, próximos passos, pendências)
     e em 5 marcações de direitos (regras + Claude, se houver chave);
  4. guarda só as marcações que o agente confirmar: nem o texto, nem o áudio, nem o dado clínico.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# %% [markdown]
# ## 1. As 5 marcações (o que o app guarda) e o que cada uma muda no caso

# %%
CATEGORIAS = {
    "dificuldade_ir_ao_posto": {
        "rotulo": "Dificuldade de ir ao posto",
        "acao": "Encaminhamento por visita domiciliar ou atendimento acompanhado",
        "formulario": {},
    },
    "pessoa_com_deficiencia": {
        "rotulo": "Pessoa com deficiência",
        "acao": "Conferir BPC; incluir laudo na lista do que levar",
        "formulario": {"pcd": "sim"},
    },
    "precisa_atendimento_medico": {
        "rotulo": "Precisa de atendimento médico",
        "acao": "Encaminhar para a UBS (sem registrar o motivo aqui)",
        "formulario": {},
    },
    "uso_continuo_remedio_ou_fralda": {
        "rotulo": "Uso contínuo de remédio ou fralda",
        "acao": "Conferir Farmácia Popular",
        "formulario": {"precisa_remedio_ou_fralda": "sim"},
    },
    "urgencia_social": {
        "rotulo": "Situação de urgência (comida, moradia, luz)",
        "acao": "Prioridade no caso e aviso ao coordenador",
        "formulario": {},
    },
}

# Padrões em texto sem acento e minúsculo (ver _simples). Cada um indica a marcação.
PADROES = {
    "dificuldade_ir_ao_posto": [
        r"acamad", r"nao (consegue|pode) (andar|sair|ir)", r"nao sai de casa", r"cadeira de rodas",
        r"cadeirante", r"andador", r"muleta", r"mobilidade", r"mora (muito )?longe",
        r"longe (do|da) (posto|ubs|cras)", r"sem dinheiro (pra|para|da) (passagem|conducao|onibus)",
        r"nao tem como ir", r"nao tem quem leve",
    ],
    "pessoa_com_deficiencia": [
        r"deficien", r"\bpcd\b", r"cadeirante", r"\bcego\b", r"\bcega\b", r"cegueira", r"\bsurd[oa]",
        r"autis", r"sindrome de down", r"paralisia", r"amputad",
    ],
    "precisa_atendimento_medico": [
        r"precisa (de |ir ao |ir no |passar no )?(medico|consulta|atendimento)", r"esta doente", r"passando mal",
        r"sentindo dor", r"com dor", r"febre", r"ferida", r"machucad", r"nao vai ao medico",
        r"sem consulta", r"nao (passa|passou) (no|pelo) medico",
    ],
    "uso_continuo_remedio_ou_fralda": [
        r"remedio (de uso )?continuo", r"remedio todo dia", r"toma remedio", r"fralda", r"medicacao",
        r"remedios? controlad",
    ],
    "urgencia_social": [
        r"sem comida", r"passando fome", r"nao tem (o )?que comer", r"geladeira vazia", r"despej",
        r"casa (caindo|rachada|condenada)", r"desabamento", r"alagamento", r"luz (foi |esta |ta )?cortad", r"cortaram (a|minha|nossa) luz",
        r"cortaram a luz", r"sem luz",
    ],
}
NEGACAO = re.compile(r"\b(nao|nem|nunca|nenhum|nenhuma)\b[^.;!?]{0,15}$")
LAUDO_SIM = re.compile(r"(tem|possui|com) laudo")
LAUDO_NAO = re.compile(r"(nao tem|sem|falta) laudo")

# %% [markdown]
# ## 2. Dado clínico: detectado, removido e nunca guardado

# %%
CLINICO = {
    "pressão": r"press[aã]o( arterial)?( d[eao])?\s*(alta|baixa|\d{1,3}\s*(x|/|por)\s*\d{1,3})|\b\d{1,2}\s*(x|por)\s*\d{1,2}\b",
    "peso": r"\b(pes(a|o|ando)|com)?\s*\d{2,3}([.,]\d+)?\s*(kg|quilos?)\b|\bpes(a|o|ando)\s+\d{2,3}\b",
    "altura": r"\b(mede|altura( de)?)?\s*([12][.,]\d{2}\s*(m|metros?)\b|1 metro e \d{2}\b|\d{3}\s*cm\b)",
    "glicemia": r"\b(glicemia|glicose|a[cç][uú]car no sangue)\D{0,12}\d{2,3}",
    "temperatura": r"\b3\d([.,]\d)?\s*(graus|°)",
    "doença ou condição": (
        r"\b(diabet|hipertens|c[aâ]ncer|tumor|hiv\b|aids\b|tuberculose|hansen[ií]ase|hepatite|avc\b|derrame|"
        r"infarto|card[ií]ac|epileps|depress|esquizofren|bipolar|alzheimer|dem[eê]ncia|parkinson|asma\b|"
        r"dpoc\b|insufici[eê]ncia renal|hemodi[aá]lise|s[ií]filis|cid\b|gravidez de risco)\w*"
    ),
    "nome de remédio": (
        r"\b(insulina|losartan|metformin|captopril|enalapril|sinvastatin|rivotril|clonazepam|fluoxetin|omeprazol)\w*"
    ),
}
# Alguns dados clínicos, mesmo removidos, indicam uma marcação de direitos (sem guardar o detalhe)
CLINICO_SUGERE = {"nome de remédio": "uso_continuo_remedio_ou_fralda"}
MARCADOR = "[dado de saúde: registrar no e-SUS]"


def _simples(txt: str) -> str:
    """minúsculo, sem acento (para os padrões funcionarem com qualquer transcrição)."""
    t = unicodedata.normalize("NFKD", txt.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def filtrar_clinico(texto: str) -> tuple[str, list[str]]:
    """Troca cada dado clínico pelo MARCADOR. Devolve (texto filtrado, tipos encontrados — sem os valores)."""
    achados = []
    for tipo, padrao in CLINICO.items():
        novo = re.sub(padrao, MARCADOR, texto, flags=re.IGNORECASE)
        if novo != texto:
            achados.append(tipo)
            texto = novo
    texto = re.sub(rf"({re.escape(MARCADOR)}[\s,;e]*)+", MARCADOR + " ", texto).strip()
    return texto, achados

# %% [markdown]
# ## 3. Transcrição (Whisper local) e gravação pelo microfone

# %%
_MODELO_WHISPER = None
# Palavras do dia a dia do agente: ajudam o Whisper a acertar siglas e nomes de programas.
VOCABULARIO = ("Anotação de visita domiciliar. CRAS, UBS, CadÚnico, Bolsa Família, BPC, Farmácia Popular, "
               "Tarifa Social, Pé-de-Meia, Poupatempo, laudo, e-SUS, acamada, cadeirante.")


def transcrever(caminho_audio: str | Path, tamanho: str = "small", apagar_audio: bool = True) -> str:
    """Áudio (ogg, mp3, m4a, wav, webm...) -> texto em português, rodando no próprio servidor.

    No Colab: !pip install -q faster-whisper   (usa GPU se houver; 'small' roda bem em CPU).
    O áudio é apagado depois da transcrição (apagar_audio=True): o app não guarda a voz da pessoa.
    """
    global _MODELO_WHISPER
    from faster_whisper import WhisperModel  # import aqui: só quem transcreve precisa instalar

    if _MODELO_WHISPER is None:
        try:
            import torch
            dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            dispositivo = "cpu"
        _MODELO_WHISPER = WhisperModel(tamanho, device=dispositivo,
                                       compute_type="float16" if dispositivo == "cuda" else "int8")
    try:
        trechos, _ = _MODELO_WHISPER.transcribe(str(caminho_audio), language="pt", vad_filter=True,
                                                initial_prompt=VOCABULARIO)
        texto = " ".join(t.text.strip() for t in trechos).strip()
    finally:
        if apagar_audio:
            Path(caminho_audio).unlink(missing_ok=True)
    return texto


_JS_GRAVAR = """
async function gravarAnotacao(maxMs) {
  const stream = await navigator.mediaDevices.getUserMedia({audio: true});
  const rec = new MediaRecorder(stream);
  const partes = [];
  rec.ondataavailable = e => partes.push(e.data);
  const caixa = document.createElement('div');
  caixa.style = 'font-family:sans-serif;margin:8px 0;display:flex;gap:12px;align-items:center';
  const btn = document.createElement('button');
  btn.textContent = '⏹  Parar e organizar';
  btn.style = 'padding:10px 18px;font-size:15px;border-radius:8px;border:0;background:#c0392b;color:#fff;cursor:pointer';
  const info = document.createElement('span');
  const t0 = Date.now();
  const relogio = setInterval(() => {
    const s = Math.floor((Date.now() - t0) / 1000);
    info.textContent = '🔴 gravando… ' + Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  }, 250);
  caixa.appendChild(btn); caixa.appendChild(info);
  document.querySelector('#output-area').appendChild(caixa);
  return await new Promise(resolve => {
    rec.onstop = () => {
      clearInterval(relogio); stream.getTracks().forEach(t => t.stop()); caixa.remove();
      const leitor = new FileReader();
      leitor.onloadend = () => resolve(leitor.result.split(',')[1]);
      leitor.readAsDataURL(new Blob(partes, {type: rec.mimeType}));
    };
    btn.onclick = () => rec.stop();
    rec.start();
    setTimeout(() => { if (rec.state === 'recording') rec.stop(); }, maxMs);
  });
}
"""


def gravar_do_microfone(max_segundos: int = 180, arquivo: str | Path = "anotacao.webm") -> Path:
    """Grava pelo microfone do navegador (Colab) até o agente clicar em 'Parar' ou acabar o tempo.

    Na primeira vez o navegador pede permissão para usar o microfone: clique em Permitir.
    """
    import base64
    from google.colab.output import eval_js
    from IPython.display import Javascript, display

    display(Javascript(_JS_GRAVAR))
    dados = eval_js(f"gravarAnotacao({int(max_segundos * 1000)})", timeout_sec=max_segundos + 60)
    arquivo = Path(arquivo)
    arquivo.write_bytes(base64.b64decode(dados))
    return arquivo


# %% [markdown]
# ## 4. Organização: regras (sempre) + Claude (opcional, só recebe o texto já filtrado)
# Além das marcações, a anotação vira um **resumo organizado**: situação relatada, prioridade,
# próximos passos e pendências. O resumo aparece só na tela, para o agente revisar.
# O que fica salvo continua sendo só as marcações confirmadas.

# %%
@dataclass
class Marcacao:
    categoria: str
    origem: str                 # "regra", "ia" ou "regra+ia"
    evidencia: str = ""         # trecho do texto FILTRADO, só para o agente conferir na tela
    tem_laudo: str | None = None  # só para pessoa_com_deficiencia: "sim", "nao" ou None
    confirmada: bool = False    # o agente confirma no app

    @property
    def rotulo(self) -> str:
        return CATEGORIAS[self.categoria]["rotulo"]


@dataclass
class Resumo:
    situacao: list[str] = field(default_factory=list)        # o que foi relatado, em frases curtas
    prioridade: str = "normal"                                # "alta" quando há urgência social
    proximos_passos: list[str] = field(default_factory=list)
    pendencias: list[str] = field(default_factory=list)      # o que falta saber ou providenciar


@dataclass
class ResultadoAnotacao:
    texto_filtrado: str
    dados_clinicos: list[str]
    marcacoes: list[Marcacao] = field(default_factory=list)
    modo: str = "regras"
    resumo: Resumo = field(default_factory=Resumo)

    @property
    def aviso_esus(self) -> str | None:
        if not self.dados_clinicos:
            return None
        return ("A anotação tinha " + ", ".join(self.dados_clinicos) +
                ". Isso não fica no app: registre no e-SUS.")

    def para_formulario(self, so_confirmadas: bool = False) -> dict:
        """Respostas do formulário que as marcações preenchem (ex.: pcd='sim'), para o simulador."""
        resp = {}
        for m in self.marcacoes:
            if m.confirmada or not so_confirmadas:
                resp.update(CATEGORIAS[m.categoria]["formulario"])
        return resp

    def para_salvar(self, id_caso: str, data: str) -> list[dict]:
        """Linhas de fato_necessidade_caso: só categorias confirmadas. Nada de texto, nada de dado clínico."""
        return [{"id_caso": id_caso, "data": data, "categoria": m.categoria,
                 "tem_laudo": m.tem_laudo, "origem": m.origem}
                for m in self.marcacoes if m.confirmada]

    def mostrar(self) -> None:
        r = self.resumo
        print(f"[modo: {self.modo}]")
        print("Texto filtrado (só na tela, não é salvo):", self.texto_filtrado)
        if self.aviso_esus:
            print("⚠️ ", self.aviso_esus)
        print("\n📋 RESUMO DA VISITA" + ("   🔴 PRIORIDADE ALTA" if r.prioridade == "alta" else ""))
        if r.situacao:
            print("  Situação relatada:")
            for s in r.situacao:
                print(f"    • {s}")
        if r.proximos_passos:
            print("  Próximos passos:")
            for i, p in enumerate(r.proximos_passos, 1):
                print(f"    {i}. {p}")
        if r.pendencias:
            print("  Pendências (perguntar ou providenciar):")
            for p in r.pendencias:
                print(f"    • {p}")
        print("\n✅ MARCAÇÕES PARA CONFIRMAR (só elas ficam salvas)")
        if not self.marcacoes:
            print("  Nenhuma marcação sugerida.")
        for m in self.marcacoes:
            extra = f" · laudo: {m.tem_laudo}" if m.tem_laudo else ""
            print(f"  ☐ {m.rotulo}{extra}  [{m.origem}]  → {CATEGORIAS[m.categoria]['acao']}")
            if m.evidencia:
                print(f"      \"{m.evidencia}\"")


def _trecho(texto: str, ini: int, fim: int, folga: int = 30) -> str:
    a, b = max(0, ini - folga), min(len(texto), fim + folga)
    return ("…" if a else "") + texto[a:b].strip() + ("…" if b < len(texto) else "")


def por_regras(texto_filtrado: str) -> list[Marcacao]:
    s = _simples(texto_filtrado)   # mesmo comprimento do original na prática (NFKD sem acento)
    achadas: dict[str, Marcacao] = {}
    for cat, padroes in PADROES.items():
        for p in padroes:
            for m in re.finditer(p, s):
                if NEGACAO.search(s[max(0, m.start() - 25):m.start()]):
                    continue   # "não tem deficiência", "nem precisa de remédio"
                if cat not in achadas:
                    achadas[cat] = Marcacao(cat, "regra", _trecho(texto_filtrado, m.start(), m.end()))
                break
    if "pessoa_com_deficiencia" in achadas:
        achadas["pessoa_com_deficiencia"].tem_laudo = ("nao" if LAUDO_NAO.search(s)
                                                       else "sim" if LAUDO_SIM.search(s) else None)
    return list(achadas.values())


def _frases(texto_filtrado: str) -> list[str]:
    """Quebra o texto em frases e corta cada uma no primeiro dado de saúde removido."""
    saida = []
    for f in re.split(r"(?<=[.!?;])\s+", texto_filtrado):
        f = f.split(MARCADOR)[0]
        f = re.sub(r"[\s,;:.!?]+(e|toma|tem|com)?\s*$", "", f, flags=re.IGNORECASE).strip(" ,;:.!?")
        if len(f.split()) >= 3:
            saida.append(f[0].upper() + f[1:])
    return saida


def resumo_por_regras(texto_filtrado: str, marcacoes: list[Marcacao], clinicos: list[str]) -> Resumo:
    cats = {m.categoria for m in marcacoes}
    ordem = ["urgencia_social", "precisa_atendimento_medico", "dificuldade_ir_ao_posto",
             "pessoa_com_deficiencia", "uso_continuo_remedio_ou_fralda"]   # o mais urgente primeiro
    passos = [CATEGORIAS[c]["acao"] for c in ordem if c in cats]
    if clinicos:
        passos.append("Registrar no e-SUS: " + ", ".join(clinicos))
    pend = []
    for m in marcacoes:
        if m.categoria == "pessoa_com_deficiencia":
            if m.tem_laudo == "nao":
                pend.append("Providenciar laudo da deficiência (ainda não tem)")
            elif m.tem_laudo is None:
                pend.append("Perguntar se a pessoa com deficiência tem laudo")
    if "dificuldade_ir_ao_posto" in cats:
        pend.append("Combinar quem acompanha ou se o atendimento será em casa")
    return Resumo(_frases(texto_filtrado), "alta" if "urgencia_social" in cats else "normal", passos, pend)


FERRAMENTA = {
    "name": "registrar_anotacao",
    "description": "Registra as marcações de direitos e o resumo organizado da anotação do agente.",
    "input_schema": {
        "type": "object",
        "properties": {
            "marcacoes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "categoria": {"type": "string", "enum": list(CATEGORIAS)},
                        "evidencia": {"type": "string", "description": "trecho curto e literal da anotação"},
                        "tem_laudo": {"type": "string", "enum": ["sim", "nao", "nao_informado"]},
                    },
                    "required": ["categoria", "evidencia"],
                },
            },
            "situacao": {"type": "array", "items": {"type": "string"},
                         "description": "o que foi relatado, em 1 a 6 frases curtas e objetivas, na 3ª pessoa"},
            "pendencias": {"type": "array", "items": {"type": "string"},
                           "description": "o que o agente ainda precisa perguntar ou providenciar"},
            "proximos_passos": {"type": "array", "items": {"type": "string"},
                                "description": "passos práticos de orientação social, sem conduta médica"},
        },
        "required": ["marcacoes", "situacao", "pendencias", "proximos_passos"],
    },
}
INSTRUCAO = (
    "Você ajuda agentes de saúde e assistentes sociais de São Paulo a organizar anotações de visita. "
    "Marque SOMENTE as categorias que a anotação afirma de forma explícita; na dúvida, não marque. "
    "Não deduza diagnóstico, doença ou condição de saúde. Ignore os trechos '" + MARCADOR + "'. "
    "Categorias: " + "; ".join(f"{k} = {v['rotulo']}" for k, v in CATEGORIAS.items()) + ". "
    "A evidência deve ser um trecho literal e curto da anotação. "
    "No resumo: frases curtas, sem inventar nada que não foi dito, sem nome de doença, remédio ou "
    "medida de saúde, e sem orientação médica. A transcrição pode ter erros de fala: corrija só o óbvio."
)


def _limpo(frases) -> list[str]:
    """Segurança extra: tudo que vem da IA passa de novo pelo filtro clínico."""
    out = []
    for f in frases or []:
        f, _ = filtrar_clinico(str(f))
        f = re.sub(r"[\s,;:.!?]+(e|toma|tem|com)?\s*$", "", f.split(MARCADOR)[0], flags=re.IGNORECASE).strip(" ,;:.!?")
        if len(f.split()) >= 2:
            out.append(f[:200])
    return out


def por_ia(texto_filtrado: str, modelo: str | None = None) -> tuple[list[Marcacao], dict] | None:
    """Usa o Claude se houver ANTHROPIC_API_KEY. Recebe só o texto filtrado. None = sem IA disponível."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        resp = anthropic.Anthropic().messages.create(
            model=modelo or os.getenv("MODELO_ANOTACOES", "claude-haiku-5-5"),
            max_tokens=1200,
            system=INSTRUCAO,
            tools=[FERRAMENTA],
            tool_choice={"type": "tool", "name": FERRAMENTA["name"]},
            messages=[{"role": "user", "content": f"Anotação do agente:\n\"\"\"{texto_filtrado}\"\"\""}],
        )
    except Exception as e:     # sem internet, chave errada, limite: cai para o modo regras
        print(f"[IA indisponível: {type(e).__name__}; usando só as regras]")
        return None
    bloco = next(b for b in resp.content if b.type == "tool_use")
    out = []
    for m in bloco.input.get("marcacoes", []):
        if m.get("categoria") not in CATEGORIAS:
            continue
        evid, _ = filtrar_clinico(m.get("evidencia", ""))
        laudo = m.get("tem_laudo")
        out.append(Marcacao(m["categoria"], "ia", evid[:160],
                            laudo if laudo in ("sim", "nao") and m["categoria"] == "pessoa_com_deficiencia" else None))
    extras = {k: _limpo(bloco.input.get(k)) for k in ("situacao", "pendencias", "proximos_passos")}
    return out, extras


def _sem_repetir(*listas) -> list[str]:
    vistos, out = set(), []
    for lista in listas:
        for x in lista:
            k = _simples(x).strip(" .")
            if k not in vistos:
                vistos.add(k)
                out.append(x)
    return out


def organizar(texto: str, usar_ia: bool = True) -> ResultadoAnotacao:
    """Texto da anotação (digitado ou transcrito) -> resumo + marcações para o agente confirmar."""
    filtrado, clinicos = filtrar_clinico(texto)
    regras = por_regras(filtrado)
    for tipo, cat in CLINICO_SUGERE.items():
        if tipo in clinicos and all(m.categoria != cat for m in regras):
            regras.append(Marcacao(cat, "regra (remédio citado, nome não guardado)"))
    ordem = list(CATEGORIAS)
    ia = por_ia(filtrado) if usar_ia else None
    if ia is None:
        regras.sort(key=lambda m: ordem.index(m.categoria))
        return ResultadoAnotacao(filtrado, clinicos, regras, "regras (offline)",
                                 resumo_por_regras(filtrado, regras, clinicos))
    marc_ia, extras = ia
    final = {m.categoria: m for m in regras}
    for m in marc_ia:                 # união: a regra garante o básico, a IA pega o que foi dito de outro jeito
        if m.categoria in final:
            final[m.categoria].origem = "regra+ia"
            final[m.categoria].tem_laudo = final[m.categoria].tem_laudo or m.tem_laudo
        else:
            final[m.categoria] = m
    marcacoes = sorted(final.values(), key=lambda m: ordem.index(m.categoria))
    base = resumo_por_regras(filtrado, marcacoes, clinicos)   # passos fixos de cada marcação vêm sempre
    resumo = Resumo(extras["situacao"] or base.situacao, base.prioridade,
                    _sem_repetir(base.proximos_passos, extras["proximos_passos"]),
                    _sem_repetir(base.pendencias, extras["pendencias"]))
    return ResultadoAnotacao(filtrado, clinicos, marcacoes, "regras + IA (Claude)", resumo)


def anotar_por_voz(caminho_audio: str | Path, usar_ia: bool = True) -> ResultadoAnotacao:
    """Atalho para um arquivo de áudio: transcreve, apaga o áudio e organiza."""
    return organizar(transcrever(caminho_audio), usar_ia=usar_ia)


def anotar_pelo_microfone(max_segundos: int = 180, usar_ia: bool = True,
                          mostrar_transcricao: bool = False) -> ResultadoAnotacao:
    """Botão de microfone: grava, transcreve, apaga o áudio, filtra e organiza."""
    arquivo = gravar_do_microfone(max_segundos)
    print("Transcrevendo… (na primeira vez o modelo é baixado, alguns minutos)")
    texto = transcrever(arquivo)
    if mostrar_transcricao:
        print("Transcrição (só na tela):", texto, "\n")
    return organizar(texto, usar_ia=usar_ia)
