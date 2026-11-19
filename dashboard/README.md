# Painel do monitoramento

O painel tem **duas abas**, uma para cada público. As duas usam os mesmos filtros (subprefeitura, distrito e unidade) e os mesmos dados. Não há filtro de programa: os indicadores por distrito não variam por programa, e a situação de cada direito aparece lado a lado no gráfico "Situação dos direitos por programa".

| Aba | Para quem | Pergunta que responde |
|---|---|---|
| **Gestão** | coordenação, subprefeituras e órgãos públicos | Estamos dentro das metas? As pendências são resolvidas a tempo? Onde fazer a próxima campanha? |
| **Operação** | UBS, CRAS e agentes de campo | Quem está esperando, há quanto tempo, e qual é o próximo passo de cada caso? |

Na URL, `?aba=gestao` ou `?aba=operacao` escolhem a aba. Sem esse parâmetro, o painel abre em Gestão; com `?uni=` (perfil de unidade), abre em Operação.

> Os dados do app (casos, documentos, encaminhamentos e **datas**) são **simulados** no notebook [`Simulacao_App_v2`](../notebooks/Simulacao_App_v2.ipynb), calibrados nos dados reais. O piloto simulado vai de **04/05/2026** a **13/11/2026** (data de referência do painel).

## Indicadores e metas

As metas foram **propostas pelo grupo para o piloto** e precisam ser validadas com a gestão. Cada indicador tem três faixas: **dentro da meta**, **atenção** e **fora da meta**. O painel mostra a faixa por cor e por texto (✓, !, ✕), para não depender só da cor.

| Indicador | Conta | Meta (dentro) | Atenção | Fora da meta | Aba |
|---|---|---|---|---|---|
| Encaminhamentos concluídos | concluídos ÷ encaminhados | ≥ 50% | 35% a 50% | < 35% | Gestão |
| Faltas nos encaminhamentos | faltou ÷ encaminhados | ≤ 15% | 15% a 25% | > 25% | Gestão |
| Pessoas sem documento já atendidas | pessoas que saíram com o documento ÷ pessoas que chegaram sem documento | ≥ 50% | 30% a 50% | < 30% | Gestão |
| Tempo até concluir | mediana de dias entre o encaminhamento e a conclusão | ≤ 30 dias | 30 a 45 dias | > 45 dias | Gestão |
| Pessoas que recebem lembrete | casos ativos que aceitaram lembrete pelo WhatsApp ÷ casos ativos | ≥ 70% | 55% a 70% | < 55% | Gestão |
| Esperando há mais de 30 dias | pessoas com pendência aberta há mais de 30 dias ÷ pessoas com pendência aberta | ≤ 20% | 20% a 40% | > 40% | Operação |

"Pendência aberta" = documento ainda pendente **ou** encaminhamento que não foi concluído (agendado, compareceu ou faltou). O tempo de espera conta a partir da pendência mais antiga da pessoa.

As metas estão no objeto `METAS` do [`index.html`](index.html). Para mudar uma meta, mude só o valor ali.

## Evolução no tempo

- **Gestão → Evolução no tempo:** para cada mês, quantas pessoas **chegaram sem documento** (mês em que o agente identificou), quantas **já foram atendidas** e quantas **ainda aguardam**. O botão "Encaminhamentos" mostra o mesmo para os encaminhamentos (feitos × concluídos × em aberto). Ao lado: o resumo dos **últimos 30 dias** e quem ainda aguarda, **por tempo de espera**.
  - Exemplo de leitura: *em outubro chegaram 211 pessoas sem documento; 20% já foram atendidas e 169 ainda aguardam.*
- **Operação → Ritmo da equipe:** casos novos × encaminhamentos concluídos por semana, nas últimas 12 semanas. Se os casos novos ficam acima dos concluídos por várias semanas, a fila cresce.

## Índice de prioridade (Onde agir primeiro)

O índice vai de **0 a 100** e **compara os 96 distritos entre si**. Em cada critério, o distrito com a situação mais difícil da cidade recebe a nota máxima e o de situação mais fácil recebe zero (normalização mín–máx). Depois, os critérios são somados com estes pesos (notebook [`Modelo_GS_v4`](../notebooks/Modelo_GS_v4.ipynb)):

| Critério | Peso | Fonte |
|---|---|---|
| Pessoas com direito provável a BPC idoso ou Bolsa Família que não recebem | 45% | estimativa do modelo |
| Distância ao CRAS mais próximo | 25% | GeoSampa |
| Setores de risco R3/R4 | 15% | GeoSampa |
| Famílias no CadÚnico por 1.000 habitantes | 15% | SMADS + Censo 2022 |

**Não é uma porcentagem.** Um índice 79 quer dizer que o distrito está perto do pior caso da cidade nos critérios que mais pesam. As classes são por posição: urgente = 10% maiores, alta = do 70º ao 90º percentil, média = do 40º ao 70º, baixa = o resto. Na tabela, uma barra mostra quanto cada critério soma na nota do distrito.

## Alertas cruzados

Cada alerta aparece quando o que os agentes registram no app **confirma, no mesmo distrito, um problema que os dados públicos já apontavam**. O painel mostra a ação indicada e o que foi cruzado:

| Ação | O que cruza |
|---|---|
| Busca ativa | distrito urgente ou alto no modelo + pessoas que ainda não pediram BPC ou Bolsa Família no app |
| Visita prioritária | setores de risco R3/R4 (GeoSampa) + pessoas sem documento no app |
| CRAS itinerante | CRAS distante (dado público) + muitas faltas nos encaminhamentos ao CRAS no app |
| Mutirão de atualização | muitos Bolsa Família bloqueados ou para atualizar no app |
| Revisar prioridade | prioridade média ou baixa no modelo, mas muitos direitos sem acesso no app |

## Percentuais

Todos os gráficos de composição mostram o **%** dentro da barra sempre que o texto cabe; nos segmentos estreitos, o % aparece ao passar o mouse. Barras simples mostram **número e %** (ex.: "259 · 44%"), e a tabela "Quem tem direito e ainda não recebe" mostra o número e o % do total em cada célula.

## Como atualizar os dados

```bash
python dashboard/gerar_dados_painel.py
```

O script lê `dados/saida/`, `dados/saida_modelo/` e `dados/saida_app/` e gera `dados_painel.js`.

## Arquivos do Power BI

| Arquivo | O que é |
|---|---|
| [`caminho-dos-direitos-dashboard-v2.pbix`](caminho-dos-direitos-dashboard-v2.pbix) | Versão atual, com as abas **Gestão** e **Operação** e a `dim_tempo` |
| [`Caminho-dos-direitos.pbix`](Caminho-dos-direitos.pbix) | Primeira versão, mantida como histórico |

## Como replicar no Power BI

1. Atualize as tabelas `dim_caso`, `fato_encaminhamento` e `fato_documento_pendente` (ganharam colunas de data) e importe `fato_documento_historico`.
2. Crie a tabela de calendário e ligue a `data_abertura`, `data_encaminhamento` e `data_identificacao` (relação ativa só com uma; as outras com `USERELATIONSHIP`):

```DAX
dim_tempo = ADDCOLUMNS ( CALENDAR ( DATE ( 2026, 5, 4 ), DATE ( 2026, 11, 13 ) ), "Mês", FORMAT ( [Date], "mmm/yy" ), "MêsOrdem", YEAR ( [Date] ) * 100 + MONTH ( [Date] ) )
```

3. Medidas principais:

```DAX
Encaminhados = COUNTROWS ( fato_encaminhamento )
% Concluídos = DIVIDE ( CALCULATE ( [Encaminhados], fato_encaminhamento[resultado] = "Concluído" ), [Encaminhados] )
% Faltas = DIVIDE ( CALCULATE ( [Encaminhados], fato_encaminhamento[resultado] = "Faltou" ), [Encaminhados] )
Tempo até concluir (mediana) = CALCULATE ( MEDIAN ( fato_encaminhamento[dias_ate_resultado] ), fato_encaminhamento[resultado] = "Concluído" )

Pessoas que chegaram sem documento = DISTINCTCOUNT ( fato_documento_historico[id_caso] )
Pessoas ainda aguardando documento = CALCULATE ( DISTINCTCOUNT ( fato_documento_historico[id_caso] ), fato_documento_historico[situacao_documento] = "Pendente" )
Pessoas atendidas = [Pessoas que chegaram sem documento] - [Pessoas ainda aguardando documento]
% Pessoas atendidas = DIVIDE ( [Pessoas atendidas], [Pessoas que chegaram sem documento] )

-- status da meta: use na formatação condicional (cor) e num cartão de texto
Status % Concluídos =
VAR v = [% Concluídos]
RETURN SWITCH ( TRUE (), ISBLANK ( v ), "sem dados", v >= 0.50, "✓ Dentro da meta", v >= 0.35, "! Atenção", "✕ Fora da meta" )
Cor % Concluídos =
VAR v = [% Concluídos]
RETURN SWITCH ( TRUE (), v >= 0.50, "#12B76A", v >= 0.35, "#F79009", "#F04438" )
```

4. Para a evolução no tempo, use um gráfico de colunas empilhadas com `dim_tempo[Mês]` no eixo e as medidas *Pessoas atendidas* e *Pessoas ainda aguardando documento* (relação pela `data_identificacao`). Ative os rótulos de dados em **% do total da coluna** para padronizar os percentuais.
5. Crie duas páginas, **Gestão** e **Operação**, com os mesmos segmentadores sincronizados (Exibir → Sincronizar segmentações).
