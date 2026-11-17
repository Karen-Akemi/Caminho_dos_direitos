# Guia para a banca de Machine Learning

Cola de estudo para apresentar os códigos do **Caminho dos Direitos** ao professor de ML.
Todos os números abaixo saíram das saídas já salvas dos notebooks (`dados/saida_modelo/`) e foram conferidos rodando o código de novo.

---

## 1. A história em 30 segundos (decore isto)

> "Queremos saber **onde há mais gente que provavelmente tem direito a benefício e não recebe**.
> Não existe esse dado pronto, então estimamos: treinamos um modelo que prevê a **cobertura esperada** de BPC idoso e Bolsa Família de cada distrito usando **só variáveis de necessidade**.
> A diferença entre o **esperado** e o **observado** é a **lacuna de acesso**.
> Depois testamos se as **barreiras** (distância ao CRAS, área de risco) explicam essa lacuna e juntamos tudo num **índice de prioridade de 0 a 100** que diz onde agir primeiro."

Palavras-chave para repetir: **resíduo como sinal**, **validação cruzada fora da amostra**, **comparar com distritos de perfil parecido**.

---

## 2. Onde está o ML no projeto (mapa rápido)

| Notebook | Técnica de ML/estatística | Para quê |
|---|---|---|
| `Tratamento_GS_v6` (P4) | Índice IDA com min-max + sensibilidade por **Dirichlet** (1.000 sorteios) | Primeira versão do índice (hoje fica em `extras/`) |
| `Tratamento_GS_v6` (P5) | **K-means** com z-score, k escolhido pela **silhueta** | Perfis de território |
| `Tratamento_GS_v6` (P6) | **Moran global e LISA** (autocorrelação espacial) | Ver se os distritos críticos são vizinhos |
| **`Modelo_GS_v4`** ⭐ | **Ridge × Random Forest × Gradient Boosting**, CV 5-fold repetida 5×; Spearman; Mann-Whitney; análise de sensibilidade | **O coração: lacuna e índice de prioridade** |
| `Simulacao_App_v2` | Simulação Monte Carlo calibrada | Dados do app (marcados como SIMULADO) |
| `caminho_dos_direitos_colab_v4` | Motor de **regras** + RAG com LLM | Plano de Direitos (não é ML treinado) |
| `anotacao_por_voz` | Whisper (transcrição) + LLM | Anotação de visita |

**Se o professor quiser ver "o ML", abra o `Modelo_GS_v4`.** É o que mais vale a pena dominar.

---

## 3. `Modelo_GS_v4` célula por célula

| Célula | O que faz | O que falar |
|---|---|---|
| 1 | Imports, caminhos, `SEMENTE = 42`, `PESOS` do índice e `CORTES` das classes | "A semente fixa deixa tudo reprodutível." |
| 2 | Acha o `distritos_base.csv` no Drive | Só infraestrutura. |
| 3 | `carregar()` e `indicadores()`: cria as taxas | **Alvos:** `taxa_bpc_idoso = bpc_idoso / pop_65+` e `cobertura_pbf = famílias PBF / famílias CadÚnico`. **Features:** `cadunico_por_1000` e `pct_65`. |
| 5 | `comparar_modelos()` e `prever_esperado()` | Compara 3 modelos com CV 5-fold **repetida 5 vezes**, escolhe o de menor **MAE**. A previsão final usa `cross_val_predict`: **cada distrito é previsto por um modelo que não o viu.** |
| 6 | `lacunas()` | `lacuna = (esperado − observado)`, só a parte positiva, × população. Família vira pessoa × 2,5. |
| 8 | `testar_barreiras()`, `comparar_risco()`, `gerar_insights()` | Spearman (barreira × lacuna por 1.000 hab.) e Mann-Whitney (com R3/R4 × sem). As frases só dizem "agrava" se p < 0,05. |
| 10 | `normalizar()`, `indice_prioridade()`, `classificar()`, `sensibilidade()`, `recomendar()` | Min-max → soma ponderada × 100. Classes por **quantil** (top 10% = urgente). Sensibilidade: 200 sorteios de pesos ±50%. |
| 11 | `rodar()` | Orquestra tudo e salva os CSV para o Power BI. |
| 13 | Executa | Mostra os resultados abaixo. |

### Por que `cross_val_predict` é o ponto mais importante
Se treinássemos com os 96 distritos e previssemos os mesmos 96, o Random Forest **decoraria** os dados, o esperado ficaria igual ao observado e a lacuna seria quase zero.
Com a previsão fora da amostra, o "esperado" de cada distrito vem só dos **outros** distritos de perfil parecido. É isso que dá sentido ao resíduo.

---

## 4. Números que você precisa saber de cor

**Modelos (validação cruzada):**

| Alvo | Escolhido | R² CV | MAE CV | Outros |
|---|---|---|---|---|
| BPC idoso | **Random Forest** | **0,81** (±0,02) | 0,020 (2 p.p.) | GB 0,67 · Ridge 0,67 |
| Bolsa Família | **Ridge** | **0,19** (±0,03) | 0,052 (5 p.p.) | RF 0,17 · GB −0,04 |

- No RF do BPC, `cadunico_por_1000` responde por ~95% da importância.
- GB com R² negativo no Bolsa Família = pior que prever a média; com 96 linhas, o boosting sobreajusta.

**Barreiras × lacuna (Spearman):**
- Setores de risco R3/R4: **ρ = 0,23, p = 0,024** → significativa.
- Distância ao CRAS: **ρ = 0,06, p = 0,55** → **não** significativa.

**Com R3/R4 (57 distritos) × sem (39), Mann-Whitney:**
- Bolsa Família: 38,2% × 40,1% (p = 0,03).
- BPC idoso: 14,6% × 6,3% (maior com risco porque esses distritos são mais pobres; por isso o modelo compara com distritos parecidos).

**Resultado:**
- Lacuna total ≈ **99.930 pessoas** (≈ 12.570 do BPC + ≈ 87.360 do Bolsa Família).
- **10 urgentes · 19 alta · 29 média · 38 baixa.**
- Os 10 urgentes concentram **55%** da lacuna (≈ 54.947 pessoas).
- Top 3: **Jardim Ângela (79,0), Tremembé (76,2), Grajaú (67,1).**
- **54** recomendações (só urgente e alta).

**Sensibilidade dos pesos (200 sorteios ±50%):** ranking com Spearman médio **0,975** (mínimo 0,87); em média **94%** dos urgentes se mantêm (mínimo 80%).

**Tratamento:** K-means com k = 3 (silhueta 0,28) · Moran I = 0,286, p = 0,001 · LISA: 7 Alto-Alto.

---

## 5. Perguntas prováveis e como responder

**"Por que regressão, se não existe rótulo de quem tem direito e não recebe?"**
Não prevemos a lacuna diretamente. Prevemos a **cobertura**, que é observada, e usamos o **resíduo** como sinal. É a mesma ideia de detecção de anomalia por resíduo e de *benchmarking* (comparar com pares).

**"Por que só 2 features?"**
Por desenho, só entram variáveis de **necessidade**. As de **barreira** ficam fora: se entrassem, o modelo "explicaria" a falta de acesso pela distância, e a lacuna sumiria justamente onde a barreira existe. Tínhamos previsto `% 0–6` e `% em pobreza no CadÚnico`, mas essas colunas **não estavam disponíveis por distrito** e o código as descarta sozinho (`features_necessidade`).

**"R² de 0,19 no Bolsa Família não é muito baixo?"**
É, e assumimos isso. Quer dizer que a necessidade explica pouco a cobertura do PBF, então a lacuna do PBF é **menos confiável** que a do BPC. Para defender: (1) o Ridge foi o que menos errou (MAE 5 p.p.); (2) o índice não usa só a lacuna; (3) a sensibilidade mostra que o ranking é estável; (4) com mais variáveis (renda do CadÚnico por faixa) daria para melhorar. **Não esconda: o próprio código foi feito para avisar se o R² ficasse abaixo de 0,1.**

**"96 linhas não é pouco para Random Forest?"**
É pouco, e por isso: `min_samples_leaf=3` para não decorar, GB raso (`max_depth=2`), comparação com um modelo linear regularizado (Ridge) e CV **repetida** 5× para medir a variação do R² (desvio de 0,02 no BPC).

**"Por que escolher pelo MAE e não pelo R²?"**
O MAE está na unidade da cobertura (pontos percentuais), é fácil de explicar e é menos sensível a distritos extremos. Nos dois alvos, o melhor pelo MAE também foi o melhor pelo R².

**"Escolher o modelo e prever na mesma validação não é otimista?"**
É levemente otimista (o certo seria *nested CV*). Com 3 modelos e uma diferença grande no BPC (0,81 × 0,67), o efeito é pequeno. Boa resposta honesta: "melhoria futura".

**"Por que `clip(lower=0)` na lacuna?"**
Só interessa a **sub**cobertura. Distrito que recebe mais que o esperado não tem "pessoas faltando", então fica com 0.

**"De onde vem o 2,5 pessoas por família?"**
É uma **premissa** para somar BPC (pessoa) com Bolsa Família (família). Está documentada no código e pode ser trocada pelo dado oficial.

**"A distância ao CRAS não foi significativa, mas pesa 25% no índice. Não é contraditório?"**
O índice é de **priorização de ação**, não um modelo preditivo. Longe do CRAS é motivo para mandar CRAS itinerante mesmo que não explique a lacuna. O teste está no painel justamente para ser transparente.

**"O risco não é significativo só porque distrito grande tem mais setores?"**
Boa pergunta, e conferimos: usando **setores por habitante**, a correlação continua significativa (ρ = 0,22, p = 0,03).

**"Os 10 urgentes concentrarem 55% não é circular?"**
Em parte, sim: a lacuna pesa 45% do índice. A frase serve para dimensionar o esforço ("atacando 10% dos distritos, alcançamos mais da metade"), não como prova do modelo.

**"Por que min-max e não z-score no índice?"**
Para os componentes ficarem na mesma escala de 0 a 1 e o índice ficar entre 0 e 100, fácil de ler no painel. Ponto fraco: é sensível a extremos (por exemplo, a Sé tem 604 famílias no CadÚnico por 1.000 hab., pela população de rua cadastrada no centro).

**"O K-means ficou bom?"**
Silhueta de 0,28 é fraca, e um dos 3 grupos tem **um distrito só** (Marsilac, a 29 km do Poupatempo), que é um outlier. Na prática separa "bem atendido" (66) de "risco alto" (29). Melhoria: tirar o outlier ou usar um método robusto (por exemplo, K-medoids). Os perfis são descritivos e o índice principal não depende deles.

**"A acurácia de 100% do simulador do app não é suspeita?"**
Não é ML: é um **motor de regras** (a lei define quem tem direito; tem que ser explicável). Os 30 casos são **testes de unidade** rotulados à mão a partir das regras oficiais. 100% mostra que o código implementa as regras, não que acerta no mundo real. Cobrem 46 das 47 regras.

**"Os dados do app são reais?"**
Não. São **simulados** (`Simulacao_App_v2`), calibrados com as proporções reais por distrito e marcados com `origem = SIMULADO`. O próprio notebook avisa que a diferença de faltas com e sem lembrete é **efeito da simulação, não resultado**.

**"Fizeram validação externa?"**
Não há rótulo verdadeiro de "quem tem direito e não recebe". A validação possível foi: CV, coerência com o conhecimento do território (a maioria dos urgentes fica nas periferias, como Jardim Ângela, Grajaú e Capão Redondo) e sensibilidade. Com o app em uso, os registros dos agentes viram o rótulo para validar.

---

## 6. Problemas que achei nos notebooks (e o que dizer se perguntarem)

Nenhum deles muda os resultados.

**Já corrigidos** (só texto; código e saídas iguais): o título "v3" do `Modelo_GS_v4`, o texto que prometia 4 features (agora diz que entram 2 e por quê), a tabela de fontes que citava a população 0–6, o comentário informal *"digam isso na banca"* e a referência ao `Tratamento_GS_v5` no `Simulacao_App_v2`.
Mesmo assim, saiba explicar o das features: **só 2 entram** (`cadunico_por_1000` e `pct_65`), porque `pop_0_6` e `familias_cadunico_pobreza` não vieram por distrito e o código as descarta sozinho.

**Ainda vale saber explicar:**

5. **Dois índices diferentes:** o **IDA** (Tratamento, P4: CadÚnico 50% / CRAS 25% / risco 25%, top 1 = Sé) e o **índice de prioridade** (Modelo: lacuna 45% / CRAS 25% / risco 15% / CadÚnico 15%, top 1 = Jardim Ângela). Se ele perguntar por que o ranking muda: o IDA foi a primeira versão, só com dificuldade de acesso; o índice do modelo inclui a lacuna estimada e é o usado no painel. O IDA ficou em `extras/`.
6. **K-means com um grupo de 1 distrito** (ver pergunta acima).
7. O `anotacao_por_voz` tem **5 células de código sem execução** salva (as dos testes interativos de microfone). Normal, mas se for mostrar, rode antes.

---

## 7. Roteiro para a hora de abrir o código

1. Abrir o **`Modelo_GS_v4` já executado** (com as saídas aparecendo). Não rode ao vivo: o Colab precisa do Drive montado.
2. Ler a **célula 0** (a ideia do modelo) em voz alta, com as próprias palavras.
3. Mostrar a **célula 3**: alvos e features.
4. Mostrar a **célula 5**: os 3 modelos, a CV repetida e o `cross_val_predict`. **Falar do "modelo que não viu o distrito".**
5. Mostrar a **célula 6**: a fórmula da lacuna.
6. Ir para a **saída da célula 13**: tabela dos modelos → barreiras → insights → sensibilidade → top 10.
7. Mostrar a **última célula (Limitações e próximos passos)**: "conhecemos os limites e sabemos o que faríamos a seguir".
8. Fechar com o painel: "isso vira o mapa de prioridade e as campanhas recomendadas".

**Se travar:** volte para a frase da seção 1. Tudo no código serve a ela.
**Se não souber:** "Não testamos isso, mas daria para fazer assim: ..." é uma resposta muito melhor do que inventar.
