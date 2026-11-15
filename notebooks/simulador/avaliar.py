"""
Roda os 30 casos de teste e mede a taxa de acerto do simulador.

Os resultados esperados em casos_teste.json foram rotulados à mão a partir
das regras oficiais (fontes em regras.csv), sem olhar a saída do simulador.
Sugestão: peçam para um colega que não escreveu as regras revisar os rótulos.

Gera:
  resultado_testes.csv  -> uma linha por caso × programa (para o slide e o anexo)
"""
import csv
import json
import sys
from pathlib import Path

try:
    PASTA = Path(__file__).resolve().parent
except NameError:  # código colado numa célula do Colab/Jupyter
    PASTA = Path.cwd()
sys.path.insert(0, str(PASTA))
from simulador import PROGRAMAS, carregar_regras, simular  # noqa: E402


def main() -> None:
    casos = json.loads((PASTA / "casos_teste.json").read_text(encoding="utf-8"))
    regras = carregar_regras()
    linhas, acertos_caso = [], 0
    for caso in casos:
        sim = simular(caso["respostas"], regras)
        obtido = sim.status_por_programa()
        ok_caso = True
        for prog in PROGRAMAS:
            esp, obt = caso["esperado"][prog], obtido[prog]
            ok_caso &= esp == obt
            linhas.append({"caso": caso["id"], "persona": caso["persona"], "programa": prog,
                           "esperado": esp, "obtido": obt, "acertou": esp == obt,
                           "regra": next(r.regra_id for r in sim.resultados if r.programa == prog)})
        acertos_caso += ok_caso

    total = len(linhas)
    acertos = sum(l["acertou"] for l in linhas)
    with open(PASTA / "resultado_testes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(linhas)

    print(f"Casos testados: {len(casos)}  |  Decisões (caso × programa): {total}")
    print(f"Acerto por decisão: {acertos}/{total} = {acertos / total:.1%}")
    print(f"Casos 100% corretos: {acertos_caso}/{len(casos)} = {acertos_caso / len(casos):.1%}")
    erros = [l for l in linhas if not l["acertou"]]
    for e in erros:
        print(f"  ✗ {e['caso']} {e['programa']}: esperado {e['esperado']}, obtido {e['obtido']} ({e['regra']})")
    cobertas = {l["regra"] for l in linhas}
    todas = {r.id for lst in regras.values() for r in lst}
    print(f"Regras exercitadas pelos testes: {len(cobertas)}/{len(todas)}")
    print("Regras sem teste:", ", ".join(sorted(todas - cobertas)) or "nenhuma")


if __name__ == "__main__":
    main()
