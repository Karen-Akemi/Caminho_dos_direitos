"""
Caminho dos Direitos — Motor de regras (camada 1 da IA)

Lê as regras oficiais de `regras.csv` e aplica às respostas do formulário
inteligente do agente. Devolve, para cada programa, um status:

    TRAVADO_DOC       -> lista vermelha (falta documento)
    PROVAVEL_DIREITO  -> lista amarela (provavelmente tem direito e não recebe)
    ATUALIZAR         -> lista amarela (precisa atualizar algo)
    VERIFICAR         -> lista amarela (falta informação)
    JA_RECEBE / ALERTA / OK -> lista verde (já recebe, com ou sem alerta)
    NAO_ELEGIVEL      -> não aparece para a família

Por que regras e não um modelo "caixa-preta"? Porque a decisão
"tem ou não tem direito" precisa ser auditável: cada resultado aponta a
linha de `regras.csv` e a fonte oficial que o gerou.

Uso:
    python simulador.py                 # roda a persona Dona Cida
    python simulador.py respostas.json  # roda um caso qualquer
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    PASTA = Path(__file__).resolve().parent
except NameError:  # código colado numa célula do Colab/Jupyter
    PASTA = Path.cwd()
SALARIO_MINIMO_2026 = 1621.00  # Decreto 12.797/2025

# Faixas de renda por pessoa usadas no formulário (valores de 2026)
FAIXAS_RENDA = {
    "ate_218": "Até R$ 218 (perfil Bolsa Família)",
    "ate_405": "De R$ 218,01 a R$ 405,25 (até 1/4 do salário mínimo, perfil BPC)",
    "ate_810": "De R$ 405,26 a R$ 810,50 (até 1/2 salário mínimo, perfil CadÚnico)",
    "ate_1621": "De R$ 810,51 a R$ 1.621 (até 1 salário mínimo)",
    "acima": "Acima de 1 salário mínimo",
    "nao_sei": "Não sabe",
}

LISTA_DO_STATUS = {
    "TRAVADO_DOC": "vermelha",
    "PROVAVEL_DIREITO": "amarela",
    "ATUALIZAR": "amarela",
    "VERIFICAR": "amarela",
    "ALERTA": "verde",
    "JA_RECEBE": "verde",
    "OK": "verde",
    "NAO_ELEGIVEL": None,
}

PROGRAMAS = [
    "Documentação básica",
    "CadÚnico",
    "Bolsa Família",
    "BPC",
    "Tarifa Social de Energia",
    "Pé-de-Meia",
    "Farmácia Popular",
]

# Respostas esperadas do formulário (sim / nao / nao_sei), com valor padrão
CAMPOS_PADRAO = {
    "distrito": "",
    "risco_geologico": "nenhum",          # preenchido pelo CEP via GeoSampa: R1..R4 ou nenhum
    "renda_faixa": "nao_sei",
    # Família
    "crianca_0_6": "nao",
    "crianca_7_17_escola": "nao",
    "gestante_ou_nutriz": "nao",
    "jovem_ensino_medio_publico": "nao",  # 14-24 no EM regular ou 19-24 na EJA, rede pública
    "idoso_60": "nao",
    "idoso_65": "nao",
    "pcd": "nao",
    "precisa_remedio_ou_fralda": "nao",
    # Documentos
    "todos_certidao": "sim",
    "todos_cpf": "sim",
    "todos_rg": "sim",
    "alguem_govbr": "nao",
    # Cadastros
    "no_cadunico": "nao",
    "cadunico_atualizado": "nao_sei",
    "conta_luz_nome_familia": "sim",
    "recebe": [],  # lista: bolsa_familia, bpc, tarifa_social, pe_de_meia
}


@dataclass
class Regra:
    id: str
    programa: str
    ordem: int
    condicao: str
    status: str
    mensagem: str
    proximo_passo: str
    onde: str
    levar: str
    fonte: str
    vigencia: str


@dataclass
class Resultado:
    programa: str
    status: str
    lista: str | None
    regra_id: str
    mensagem: str
    proximo_passo: str
    onde: str
    levar: str
    fonte: str


@dataclass
class Simulacao:
    respostas: dict
    resultados: list[Resultado] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)
    prioridade: str = "baixa"
    pontos_prioridade: int = 0

    def por_lista(self, lista: str) -> list[Resultado]:
        return [r for r in self.resultados if r.lista == lista]

    def status_por_programa(self) -> dict[str, str]:
        return {r.programa: r.status for r in self.resultados}


def carregar_regras(caminho: Path = PASTA / "regras.csv") -> dict[str, list[Regra]]:
    regras: dict[str, list[Regra]] = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            linha["ordem"] = int(linha["ordem"])
            r = Regra(**linha)
            if r.status not in LISTA_DO_STATUS:
                raise ValueError(f"Status inválido na regra {r.id}: {r.status}")
            regras.setdefault(r.programa, []).append(r)
    for lista in regras.values():
        lista.sort(key=lambda r: r.ordem)
    return regras


def variaveis(resp: dict) -> dict:
    """Transforma as respostas em variáveis usadas nas condições de regras.csv."""
    v = dict(resp)
    faixa = resp["renda_faixa"]
    recebe = set(resp.get("recebe") or [])
    v.update(
        renda_ate_218=faixa == "ate_218",
        renda_ate_quarto=faixa in ("ate_218", "ate_405"),
        renda_ate_meio=faixa in ("ate_218", "ate_405", "ate_810"),
        renda_ate_1sm=faixa in ("ate_218", "ate_405", "ate_810", "ate_1621"),
        renda_desconhecida=faixa == "nao_sei",
        sem_doc_base=resp["todos_certidao"] == "nao" or resp["todos_cpf"] == "nao",
        publico_bpc=resp["idoso_65"] == "sim" or resp["pcd"] == "sim",
        recebe_pbf="bolsa_familia" in recebe,
        recebe_bpc="bpc" in recebe,
        recebe_tarifa="tarifa_social" in recebe,
        recebe_pdm="pe_de_meia" in recebe,
    )
    return v


def avaliar_condicao(expr: str, ns: dict) -> bool:
    # Condições vêm só do regras.csv do projeto (não do usuário), sem builtins.
    return bool(eval(expr, {"__builtins__": {}}, ns))


def simular(respostas: dict, regras: dict[str, list[Regra]] | None = None) -> Simulacao:
    regras = regras or carregar_regras()
    resp = {**CAMPOS_PADRAO, **respostas}
    if resp["renda_faixa"] not in FAIXAS_RENDA:
        raise ValueError(f"renda_faixa inválida: {resp['renda_faixa']}")
    ns = variaveis(resp)
    sim = Simulacao(respostas=resp)

    for programa in PROGRAMAS:
        for regra in regras[programa]:
            if avaliar_condicao(regra.condicao, ns):
                sim.resultados.append(
                    Resultado(
                        programa=programa,
                        status=regra.status,
                        lista=LISTA_DO_STATUS[regra.status],
                        regra_id=regra.id,
                        mensagem=regra.mensagem,
                        proximo_passo=regra.proximo_passo,
                        onde=regra.onde,
                        levar=regra.levar,
                        fonte=regra.fonte,
                    )
                )
                break

    st = sim.status_por_programa()

    # Observações que cruzam programas (o agente precisa saber)
    if st.get("BPC") == "PROVAVEL_DIREITO" and st.get("Bolsa Família") in ("PROVAVEL_DIREITO", "JA_RECEBE", "ALERTA"):
        sim.observacoes.append(
            "Se o BPC for concedido, o valor entra na renda da família para o Bolsa Família. "
            "O Bolsa Família pode diminuir ou acabar; a Regra de Proteção pode manter parte dele por um tempo. "
            "Explique isso à família antes do pedido."
        )
    if resp["crianca_0_6"] == "sim" and st.get("Bolsa Família") in ("JA_RECEBE", "ALERTA"):
        sim.observacoes.append("Há criança de 0 a 6 anos: confira se o adicional de R$ 150 (Benefício Primeira Infância) está sendo pago.")
    if resp["alguem_govbr"] != "sim" and any(r.status == "PROVAVEL_DIREITO" for r in sim.resultados):
        sim.observacoes.append("Ninguém da família tem conta gov.br: os pedidos devem ser feitos presencialmente (CRAS, INSS 135) com apoio do agente.")

    # Prioridade de atendimento (usada na lista de famílias do agente)
    pts = 0
    pts += 3 * sum(r.status == "TRAVADO_DOC" for r in sim.resultados)
    pts += 2 * sum(r.status == "PROVAVEL_DIREITO" for r in sim.resultados)
    pts += 1 * sum(r.status in ("ALERTA", "ATUALIZAR") for r in sim.resultados)
    if resp["risco_geologico"] in ("R3", "R4"):
        pts += 4
    if resp["crianca_0_6"] == "sim" or resp["idoso_65"] == "sim" or resp["pcd"] == "sim":
        pts += 2
    sim.pontos_prioridade = pts
    sim.prioridade = "urgente" if pts >= 14 else "alta" if pts >= 9 else "média" if pts >= 4 else "baixa"
    return sim


def imprimir(sim: Simulacao) -> None:
    rotulos = {"vermelha": "🔴 Travado por documento", "amarela": "🟡 Provavelmente tem direito / fazer agora", "verde": "🟢 Já recebe ou está em dia"}
    print(f"Prioridade: {sim.prioridade.upper()} ({sim.pontos_prioridade} pontos)\n")
    for lista, titulo in rotulos.items():
        itens = sim.por_lista(lista)
        if not itens:
            continue
        print(titulo)
        for r in itens:
            print(f"  • {r.programa} [{r.status} · {r.regra_id}]: {r.mensagem}")
            if r.proximo_passo != "—":
                print(f"      → {r.proximo_passo} | Onde: {r.onde} | Levar: {r.levar}")
        print()
    for o in sim.observacoes:
        print(f"⚠️  {o}")


# Persona do pitch: mesmas respostas das telas 02 a 04 do protótipo no Figma (caso #3729)
# (65+, Jardim Ângela, 2 pessoas: ela e o filho que faz bico de ajudante de pedreiro;
#  renda R$ 600 / 2 = R$ 300 por pessoa; já recebe BPC e Tarifa Social; usa remédio contínuo;
#  tem certidão e RG, falta o CPF; está no CadÚnico, atualizado nos últimos 2 anos, antes de o CPF
#  passar a ser obrigatório para todos (Portaria MDS 1.133/2025)).
DONA_CIDA = {
    "distrito": "JARDIM ANGELA",
    "risco_geologico": "nenhum",
    "renda_faixa": "ate_405",
    "idoso_60": "sim",
    "idoso_65": "sim",
    "precisa_remedio_ou_fralda": "sim",
    "todos_certidao": "sim",
    "todos_cpf": "nao",
    "todos_rg": "sim",
    "alguem_govbr": "nao",
    "no_cadunico": "sim",
    "cadunico_atualizado": "sim",
    "conta_luz_nome_familia": "sim",
    "recebe": ["bpc", "tarifa_social"],
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        respostas = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        respostas = DONA_CIDA
    imprimir(simular(respostas))
