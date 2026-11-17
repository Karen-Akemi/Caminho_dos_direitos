"""Gera site/dados_site.js a partir dos CSVs do repositório (dados reais + app simulado).

Uso, na raiz do repositório:  python site/gerar_dados_site.py .
"""
import csv, json, math, sys, collections
from pathlib import Path

ROOT = Path(sys.argv[1])
OUT = ROOT / "site" / "dados_site.js"


def ler(p):
    with open(ROOT / p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(v):
    if v in (None, ""):
        return None
    return float(v.replace(",", "."))


ind = ler("dados/saida_modelo/fato_indicadores_distrito.csv")
rec = ler("dados/saida_modelo/fato_recomendacoes.csv")
ins = ler("dados/saida_modelo/fato_insights.csv")
kpi = ler("dados/saida/kpi_cidade.csv")[0]
equip = ler("dados/saida/dim_equipamento.csv")
casos = ler("dados/saida_app/dim_caso.csv")
itens = ler("dados/saida_app/fato_item_plano.csv")
enc = ler("dados/saida_app/fato_encaminhamento.csv")
docs = ler("dados/saida_app/fato_documento_pendente.csv")
alertas = ler("dados/saida_app/fato_alertas.csv")

distritos = {}
for r in ind:
    c = int(r["cod_distrito"])
    distritos[c] = dict(
        n=r["distrito"], s=r["subprefeitura"], pop=int(num(r["pop_total"])),
        cad=int(num(r["familias_cadunico"])), pbf=int(num(r["familias_pbf"])),
        bpc=int(num(r["bpc_idoso"])), r34=int(num(r["setores_risco_r3r4"])),
        dcras=round(num(r["dist_cras_km"]), 2), lac=int(num(r["lacuna_pessoas"])),
        lacBpc=int(num(r["lacuna_bpc_idosos"])), lacPbf=int(num(r["lacuna_pbf_familias"])),
        idx=round(num(r["indice_prioridade"]), 1), cl=r["classe_prioridade"],
        cobPbf=round(num(r["cobertura_pbf"]), 4), cobPbfEsp=round(num(r["cobertura_pbf_esperada"]), 4),
        txBpc=round(num(r["taxa_bpc_idoso"]), 4), txBpcEsp=round(num(r["bpc_idoso_esperado_taxa"]), 4),
        cras=r["cras_referencia"],
    )

recs = [dict(d=int(r["cod_distrito"]), a=r["acao"], p=r["programa"], m=r["motivo"],
             pub=int(num(r["publico_estimado"])) if r["publico_estimado"] else None) for r in rec]

# unidades do app + indicadores simulados por unidade
uni = {int(e["id_equipamento"]): dict(n=e["nome_equipamento"], t=e["tipo_equipamento"], d=int(e["cod_distrito"]))
       for e in equip if e["eh_unidade_app"] == "True"}
sit_por_caso = collections.defaultdict(list)
for i in itens:
    sit_por_caso[int(i["id_caso"])].append(i["situacao"])
enc_por_caso = collections.defaultdict(list)
for e in enc:
    enc_por_caso[int(e["id_caso"])].append((e["tipo_destino"], e["resultado"], e["lembrete_enviado"]))
doc_por_caso = collections.defaultdict(list)
for d in docs:
    doc_por_caso[int(d["id_caso"])].append(d["documento"])

agg_uni = collections.defaultdict(lambda: dict(casos=0, ativos=0, sit=collections.Counter(), res=collections.Counter(),
                                                 docs=collections.Counter(), lem=0, risco=0))
for c in casos:
    u = int(c["id_unidade"])
    a = agg_uni[u]
    a["casos"] += 1
    a["ativos"] += c["situacao_caso"] == "Ativo"
    a["risco"] += c["area_risco_r3r4"] == "Sim"
    a["lem"] += c["aceita_lembrete"] == "Sim"
    cid = int(c["id_caso"])
    a["sit"].update(sit_por_caso[cid])
    a["res"].update(r for _, r, _ in enc_por_caso[cid])
    a["docs"].update(doc_por_caso[cid])
unidades = {}
for u, info in uni.items():
    a = agg_uni.get(u)
    if not a:
        continue
    unidades[u] = dict(info, casos=a["casos"], ativos=a["ativos"], risco=a["risco"], lem=a["lem"],
                       sit=dict(a["sit"]), res=dict(a["res"]), docs=dict(a["docs"].most_common(5)))

app_tot = dict(casos=len(casos), enc=len(enc),
               concl=sum(1 for e in enc if e["resultado"] == "Concluído"),
               comp=sum(1 for e in enc if e["resultado"] in ("Compareceu", "Concluído")),
               lem=sum(1 for e in enc if e["lembrete_enviado"] == "Sim"),
               lemComp=sum(1 for e in enc if e["lembrete_enviado"] == "Sim" and e["resultado"] in ("Compareceu", "Concluído")),
               semLem=sum(1 for e in enc if e["lembrete_enviado"] != "Sim"),
               semLemComp=sum(1 for e in enc if e["lembrete_enviado"] != "Sim" and e["resultado"] in ("Compareceu", "Concluído")),
               resultado_fora_agendado=sum(1 for e in enc if e["resultado"] != "Agendado"))

als = [dict(d=int(a["cod_distrito"]), r=a["regra"], t=a["alerta"], g=a["gravidade"]) for a in alertas]

# ---------- mapa: projeção equiretangular + simplificação Douglas-Peucker ----------
g = json.load(open(ROOT / "dados/saida/distritos_sp.geojson", encoding="utf-8"))
pts = [p for f in g["features"] for ring in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "Polygon"
       else [r for poly in f["geometry"]["coordinates"] for r in poly]) for p in ring]
minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
k = math.cos(math.radians((miny + maxy) / 2))
W = 400.0
H = W * (maxy - miny) / ((maxx - minx) * k)
proj = lambda p: ((p[0] - minx) * k / ((maxx - minx) * k) * W, (maxy - p[1]) / (maxy - miny) * H)


def dp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return dp(pts[:idx + 1], eps)[:-1] + dp(pts[idx:], eps)
    return [pts[0], pts[-1]]


mapa = {}
for f in g["features"]:
    c = int(f["properties"]["cod_distrito"])
    rings = f["geometry"]["coordinates"] if f["geometry"]["type"] == "Polygon" else \
        [r for poly in f["geometry"]["coordinates"] for r in poly]
    path = ""
    for ring in rings:
        pp = [proj(p) for p in ring]
        m = len(pp) // 2  # anel fechado: simplifica as duas metades separadamente
        rp = dp(pp[:m + 1], 0.6)[:-1] + dp(pp[m:], 0.6)
        if len(rp) < 3:
            continue
        path += "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in rp) + "Z"
    mapa[c] = path

dados = dict(
    kpi=dict(pop=int(num(kpi["populacao_2022"])), cad=int(kpi["cadunico_total"]), cras=int(kpi["qtd_cras"]),
             ubs=int(kpi["qtd_ubs"]), cart=int(kpi["qtd_cartorios"]), poup=int(kpi["qtd_poupatempo"])),
    distritos=distritos, recs=recs, insights=[r["insight"] for r in ins], unidades=unidades, app=app_tot,
    alertas=als, mapa=dict(w=W, h=round(H, 1), p=mapa),
)
OUT.parent.mkdir(exist_ok=True)
txt = "/* Gerado a partir dos CSVs de dados/ (território real + app SIMULADO). Não editar à mão. */\nwindow.CD = " + \
      json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";\n"
OUT.write_text(txt, encoding="utf-8")
print("ok:", OUT, len(txt) // 1024, "KB")
