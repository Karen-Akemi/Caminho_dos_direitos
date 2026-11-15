"""
Caminho dos Direitos — IA generativa com base nos normativos (camada 2: RAG)

O motor de regras (simulador/) decide. Esta camada só EXPLICA o resultado
em linguagem simples e responde dúvidas do agente, sempre citando a fonte.

Como funciona:
  1. Recuperação: busca por similaridade (TF-IDF) nos trechos de
     base_conhecimento.csv os mais parecidos com o programa/pergunta.
  2. Geração: monta um prompt com o resultado do simulador + os trechos
     recuperados e pede a um LLM a explicação, proibindo-o de mudar a
     decisão ou inventar regra que não esteja nos trechos.
  3. Sem chave de API (ou sem internet), usa uma explicação por modelo de
     texto, para a demonstração funcionar offline.

Para usar um LLM de verdade no Colab:
    !pip install -q anthropic
    e salve a chave em "Secrets" (ícone de chave na barra lateral) com o nome
    ANTHROPIC_API_KEY, liberando o acesso para o notebook.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    PASTA = Path(__file__).resolve().parent
except NameError:  # código colado numa célula do Colab/Jupyter
    PASTA = Path.cwd()
# Aceita as duas organizações: ia/ + simulador/ lado a lado, ou tudo na mesma pasta
for _p in (PASTA, PASTA.parent / "simulador"):
    if (_p / "simulador.py").exists():
        sys.path.insert(0, str(_p))
        break
from simulador import DONA_CIDA, Resultado, Simulacao, simular  # noqa: E402

MODELO_LLM = "claude-haiku-5-5"

INSTRUCOES_SISTEMA = """Você é o assistente do Caminho dos Direitos, usado por agentes comunitários de saúde e técnicos do CRAS em São Paulo.
Regras obrigatórias:
- A decisão (tem direito / travado / verificar) já foi tomada pelo motor de regras. Nunca mude essa decisão.
- Explique em linguagem simples, frases curtas, sem siglas sem explicação, para ser lida em voz alta para a família.
- Use SOMENTE as informações dos TRECHOS fornecidos. Se algo não estiver nos trechos, diga "confirme no CRAS".
- Sempre trate o resultado como possibilidade ("pode ter direito"), nunca como garantia.
- Termine cada programa com a fonte entre colchetes, ex.: [Lei 8.742/1993].
- Não peça nem repita nome completo, CPF ou qualquer dado pessoal."""


class BaseConhecimento:
    def __init__(self, caminho: Path = PASTA / "base_conhecimento.csv"):
        with open(caminho, encoding="utf-8") as f:
            self.trechos = list(csv.DictReader(f, delimiter=";"))
        textos = [f"{t['programa']} {t['texto']}" for t in self.trechos]
        self.vetorizador = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2))
        self.matriz = self.vetorizador.fit_transform(textos)

    def buscar(self, consulta: str, programa: str | None = None, k: int = 3) -> list[dict]:
        sims = cosine_similarity(self.vetorizador.transform([consulta]), self.matriz).ravel()
        if programa:  # reforça trechos do mesmo programa
            sims = sims + [0.5 if t["programa"] == programa else 0 for t in self.trechos]
        ordem = sims.argsort()[::-1][:k]
        return [{**self.trechos[i], "score": round(float(sims[i]), 3)} for i in ordem if sims[i] > 0]


def montar_prompt(sim: Simulacao, base: BaseConhecimento, pergunta: str | None = None) -> tuple[str, list[dict]]:
    relevantes = [r for r in sim.resultados if r.lista is not None and r.status != "OK"]
    blocos, usados = [], {}
    for r in relevantes:
        for t in base.buscar(f"{r.programa} {r.mensagem}", programa=r.programa, k=2):
            usados[t["id"]] = t
        blocos.append(f"- {r.programa}: {r.status} (regra {r.regra_id}). {r.mensagem} Próximo passo: {r.proximo_passo}")
    if pergunta:
        for t in base.buscar(pergunta, k=3):
            usados[t["id"]] = t
    trechos = "\n".join(f"[{t['id']}] ({t['fonte']}) {t['texto']}" for t in usados.values())
    tarefa = f"Responda à dúvida do agente: {pergunta}" if pergunta else (
        "Escreva o Plano de Direitos da família: primeiro o que está travado por documento, "
        "depois o que ela provavelmente tem direito, depois os alertas. No máximo 3 frases por programa.")
    prompt = f"RESULTADO DO MOTOR DE REGRAS:\n" + "\n".join(blocos) + \
             ("\n\nOBSERVAÇÕES:\n" + "\n".join(sim.observacoes) if sim.observacoes else "") + \
             f"\n\nTRECHOS DOS NORMATIVOS:\n{trechos}\n\nTAREFA: {tarefa}"
    return prompt, list(usados.values())


def explicacao_offline(sim: Simulacao) -> str:
    """Plano de Direitos por modelo de texto (sem LLM)."""
    titulos = {"vermelha": "🔴 Primeiro, os documentos", "amarela": "🟡 Você pode ter direito (ou precisa resolver)", "verde": "🟢 Já recebe ou está em dia"}
    partes = ["*Seu Plano de Direitos*", "Este plano mostra possibilidades. Quem confirma é o órgão responsável.\n"]
    for lista, titulo in titulos.items():
        itens: list[Resultado] = [r for r in sim.por_lista(lista) if r.status != "OK"]
        if not itens:
            continue
        partes.append(titulo)
        for i, r in enumerate(itens, 1):
            linha = f"{i}. *{r.programa}*: {r.mensagem}"
            if r.proximo_passo != "—":
                linha += f"\n   O que fazer: {r.proximo_passo}\n   Onde: {r.onde}\n   Levar: {r.levar}"
            partes.append(linha)
        partes.append("")
    for o in sim.observacoes:
        partes.append(f"⚠️ {o}")
    return "\n".join(partes)


def chave_api() -> str | None:
    """Pega a chave do ambiente ou dos Secrets do Colab."""
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        try:
            from google.colab import userdata  # só existe no Colab
            chave = userdata.get("ANTHROPIC_API_KEY")
        except Exception:
            chave = None
    return chave


def explicar(sim: Simulacao, pergunta: str | None = None, base: BaseConhecimento | None = None) -> dict:
    base = base or BaseConhecimento()
    prompt, trechos = montar_prompt(sim, base, pergunta)
    texto, modo = None, "offline (modelo de texto)"
    chave = chave_api()
    if chave:
        try:
            import anthropic
            cliente = anthropic.Anthropic(api_key=chave)
            msg = cliente.messages.create(model=MODELO_LLM, max_tokens=1200, system=INSTRUCOES_SISTEMA,
                                          messages=[{"role": "user", "content": prompt}])
            texto, modo = msg.content[0].text, f"LLM ({MODELO_LLM})"
        except Exception as e:  # sem internet, sem pacote etc.
            modo = f"offline (falha no LLM: {type(e).__name__})"
    if texto is None:
        texto = explicacao_offline(sim) if not pergunta else \
            "Trechos mais próximos da pergunta:\n" + "\n".join(f"- {t['texto']} [{t['fonte']}]" for t in base.buscar(pergunta, k=3))
    return {"modo": modo, "texto": texto, "fontes": [(t["id"], t["fonte"], t["url"]) for t in trechos], "prompt": prompt}


if __name__ == "__main__":
    base = BaseConhecimento()
    sim = simular(DONA_CIDA)
    r = explicar(sim, base=base)
    print(f"[modo: {r['modo']}]\n")
    print(r["texto"])
    print("\nFontes recuperadas:", ", ".join(f"{i}" for i, _, _ in r["fontes"]))
    print("\n--- Dúvida do agente ---")
    r2 = explicar(sim, pergunta="Se a Dona Cida conseguir o BPC ela perde o Bolsa Família?", base=base)
    print(r2["texto"])
