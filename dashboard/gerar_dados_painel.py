"""Gera dashboard/dados_painel.js a partir dos CSVs do repositório.

Uso, na raiz do repositório:  python dashboard/gerar_dados_painel.py

Lê o território e o modelo (dados/saida, dados/saida_modelo) e o app simulado (dados/saida_app).
As datas viram "dia do piloto" (0 = DATA_INICIO) para o arquivo ficar pequeno.
"""
import csv
import json
import math
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard" / "dados_painel.js"

DATA_INICIO = date(2026, 5, 4)       # início do piloto (mesmo valor do notebook Simulacao_App_v2)
DATA_REFERENCIA = date(2026, 11, 13)  # "hoje" do painel

# Mesmos pesos do notebook Modelo_GS_v4 (PESOS): o painel mostra quanto cada parte soma no índice
PESOS = {"lacuna_pessoas": 0.45, "dist_cras_km": 0.25, "setores_risco_r3r4": 0.15, "cadunico_por_1000": 0.15}

SIT = ["Falta documento", "Ainda não pediu", "Bloqueado", "Precisa atualizar", "Já recebe"]
RES = ["Agendado", "Compareceu", "Concluído", "Faltou"]
LEM = ["Texto", "Áudio", "Texto e áudio", "Sem lembrete"]
COB = ["Recebe no próprio WhatsApp", "Recebe no WhatsApp de familiar", "Tem WhatsApp, não aceitou", "Sem WhatsApp"]
DEST = ["CRAS", "Poupatempo", "UBS", "Cartório", "INSS"]
DOCS = ["RG/CIN", "Certidão de nascimento", "Comprovante de residência", "CPF", "Título de eleitor", "Carteira de trabalho"]
ETA = ["0–5", "6–17", "18–29", "30–64", "65+"]
REN = ["até R$ 218", "até R$ 405", "até R$ 810", "até R$ 1.621", "acima", "não informado"]


def ler(p):
    with open(ROOT / p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(v):
    return None if v in (None, "") else float(v.replace(",", "."))


def dia(v):
    """'2026-05-10' -> dias desde o início do piloto; vazio -> -1."""
    return -1 if not v else (date.fromisoformat(v) - DATA_INICIO).days


# ---------- território e modelo ----------
ind = ler("dados/saida_modelo/fato_indicadores_distrito.csv")
vals = {c: [num(r[c]) for r in ind] for c in PESOS}
med = {c: sorted(v for v in vs if v is not None)[len([v for v in vs if v is not None]) // 2] for c, vs in vals.items()}
lim = {c: (min(v if v is not None else med[c] for v in vs), max(v if v is not None else med[c] for v in vs)) for c, vs in vals.items()}

distritos = {}
for r in ind:
    comp = []
    for c, w in PESOS.items():
        v = num(r[c])
        v = med[c] if v is None else v
        lo, hi = lim[c]
        comp.append(round((v - lo) / (hi - lo) * w * 100, 2) if hi > lo else 0)
    idx = num(r["indice_prioridade"])
    assert abs(sum(comp) - idx) < 0.1, (r["distrito"], sum(comp), idx)
    distritos[int(r["cod_distrito"])] = dict(
        n=r["distrito"], s=r["subprefeitura"], idx=idx, c=r["classe_prioridade"],
        pop=int(num(r["pop_total"])), cras=round(num(r["dist_cras_km"]), 3), risco=int(num(r["setores_risco_r3r4"])),
        lac=round(num(r["lacuna_pessoas"]), 1), cad=int(num(r["familias_cadunico"])),
        cad1000=round(num(r["cadunico_por_1000"]), 1), comp=comp,
    )

# faixas do índice que separam as classes (classes por quantil, no notebook do modelo)
faixas = {}
for d in distritos.values():
    lo, hi = faixas.get(d["c"], (999, -1))
    faixas[d["c"]] = (min(lo, d["idx"]), max(hi, d["idx"]))

equip = ler("dados/saida/dim_equipamento.csv")
unidades = {int(e["id_equipamento"]): [e["nome_equipamento"], int(e["cod_distrito"]), e["tipo_equipamento"]]
            for e in equip if e["eh_unidade_app"] == "True"}

# ---------- app (simulado) ----------
prog = {int(p["id_programa"]): p["programa"] for p in ler("dados/saida_modelo/dim_programa.csv")}

casos = {}
for c in ler("dados/saida_app/dim_caso.csv"):
    if c["aceita_lembrete"] == "Sim":
        cob = 0 if c["whatsapp"] == "WhatsApp próprio" else 1
    else:
        cob = 3 if c["whatsapp"] == "Sem WhatsApp" else 2
    casos[int(c["id_caso"])] = [
        int(c["cod_distrito"]), int(c["id_unidade"]), ETA.index(c["faixa_etaria"]), REN.index(c["faixa_renda"]),
        1 if c["area_risco_r3r4"] == "Sim" else 0, 1 if c["situacao_caso"] == "Ativo" else 0, cob,
        dia(c["data_abertura"]), dia(c["data_encerramento"]),
    ]

itens = [[int(i["id_caso"]), int(i["id_programa"]), SIT.index(i["situacao"])] for i in ler("dados/saida_app/fato_item_plano.csv")]

enc = []
for e in ler("dados/saida_app/fato_encaminhamento.csv"):
    lem = LEM.index(e["formato_lembrete"]) if e["lembrete_enviado"] == "Sim" else 3
    enc.append([int(e["id_caso"]), int(e["id_programa"]), DEST.index(e["tipo_destino"]), RES.index(e["resultado"]), lem,
                dia(e["data_encaminhamento"]), dia(e["data_resultado"])])

# histórico de documentos: [caso, documento, dia identificado, dia resolvido (-1 = pendente)]
docs = [[int(d["id_caso"]), DOCS.index(d["documento"]), dia(d["data_identificacao"]), dia(d["data_resolucao"])]
        for d in ler("dados/saida_app/fato_documento_historico.csv")]
pend = {(int(d["id_caso"]), d["documento"]) for d in ler("dados/saida_app/fato_documento_pendente.csv")}
assert pend == {(c, DOCS[d]) for c, d, _, r in docs if r < 0}, "histórico e pendentes não batem"

alertas = [[int(a["cod_distrito"]), a["regra"], a["alerta"], a["gravidade"], int(a["ordem"])]
           for a in ler("dados/saida_app/fato_alertas.csv")]

# ---------- mapa: projeção simples (longitude × cos da latitude média), encaixada na caixa ----------
geo = json.load(open(ROOT / "dados/saida/distritos_sp.geojson", encoding="utf-8"))
W, H, PAD = 340, 415, 2


def aneis(g):
    return g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]


pts = [p for f in geo["features"] for a in aneis(f["geometry"]) for p in a]
x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
k = math.cos(math.radians((y0 + y1) / 2))
esc = min((W - 2 * PAD) / ((x1 - x0) * k), (H - 2 * PAD) / (y1 - y0))
dx = (W - (x1 - x0) * k * esc) / 2
dy = (H - (y1 - y0) * esc) / 2
paths = {}
for f in geo["features"]:
    partes = []
    for a in aneis(f["geometry"]):
        xy, ult = [], None
        for lon, lat in a:
            p = (round(dx + (lon - x0) * k * esc, 1), round(dy + (y1 - lat) * esc, 1))
            if p != ult:
                xy.append(p); ult = p
        partes.append("M" + "L".join(f"{x},{y}" for x, y in xy) + "Z")
    paths[int(f["properties"]["cod_distrito"])] = "".join(partes)
assert set(paths) == set(distritos)

D = dict(
    inicio=DATA_INICIO.isoformat(), ref=(DATA_REFERENCIA - DATA_INICIO).days,
    SIT=SIT, RES=RES, LEM=LEM, COB=COB, DEST=DEST, DOCS=DOCS, ETA=ETA, REN=REN, prog=prog,
    pesos=list(PESOS.values()), faixas=faixas,
    distritos=distritos, unidades=unidades, casos=casos, itens=itens, enc=enc, docs=docs, alertas=alertas,
    paths=paths, mapW=W, mapH=H,
)
txt = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
OUT.write_text("/* Gerado por dashboard/gerar_dados_painel.py. Não edite à mão. */\nconst D = " + txt + ";\n", encoding="utf-8")
print(f"{OUT.relative_to(ROOT)}: {len(txt) / 1024:.0f} KB | {len(casos)} casos, {len(enc)} encaminhamentos, {len(docs)} documentos")
