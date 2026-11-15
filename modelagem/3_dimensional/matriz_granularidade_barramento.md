# Modelo dimensional — matriz de granularidade e matriz de barramento

Primeira parte da etapa 3 (modelo dimensional) do **Caminho dos Direitos**. Antes de desenhar o modelo dimensional, definimos **o que cada tabela fato registra (grão)** e **quais dimensões cada fato compartilha (barramento)**. As duas matrizes mostram como os dados públicos do território e os dados do app se cruzam no mesmo painel.

```
Modelo conceitual  →  Modelo lógico  →  Matrizes (esta etapa)  →  Modelo dimensional  →  Painel
```

Números conferidos nos arquivos da pasta [`dados/`](../../dados) (`saida`, `saida_app`, `saida_modelo`). Em todos os fatos, a chave do grão **não tem linhas repetidas**.

## 1. Processos de negócio

| # | Processo | Pergunta que responde | Origem |
|---|---|---|---|
| 1 | Plano de direitos | Quais direitos cada pessoa tem e em que situação estão? | App (SIMULADO) |
| 2 | Documentação | Quais documentos faltam para as pessoas acessarem os direitos? | App (SIMULADO) |
| 3 | Encaminhamento | As pessoas vão aos serviços? O lembrete por WhatsApp ajuda? | App (SIMULADO) |
| 4 | Priorização do território | Onde a cobertura dos benefícios está abaixo do esperado? Onde agir primeiro? | Bases públicas (REAL) + modelo (ESTIMATIVA DO MODELO) |
| 5 | Risco geológico | Onde estão os setores de risco R1 a R4? | Bases públicas (REAL) |
| 6 | Alertas cruzados | Onde o que os agentes encontram e o território apontam o mesmo problema? | App + território |

## 2. Matriz de granularidade

| Fato | Processo | Grão (1 linha =) | Chave do grão | Dimensões | Medidas (contagens no Power BI) | Linhas | Origem |
|---|---|---|---|---|---|---|---|
| `fato_item_plano` | Plano de direitos | um direito sugerido para uma pessoa, com a situação marcada pelo agente | `id_caso` + `id_programa` | caso, programa | Direitos sugeridos · Pessoas com direito sem acesso · Pessoas sem acesso | 13.404 | SIMULADO |
| `fato_documento_pendente` | Documentação | um documento que falta para uma pessoa | `id_caso` + `documento` | caso | Pessoas sem documento | 929 | SIMULADO |
| `fato_encaminhamento` | Encaminhamento | uma ida da pessoa a um serviço, com resultado e lembrete | `id_encaminhamento` | caso, programa, tempo (proposta) | Encaminhamentos · Encaminhamentos concluídos · % recebem lembrete · Faltas com lembrete · Faltas sem lembrete · Diferença | 3.191 | SIMULADO |
| `fato_alertas` | Alertas cruzados | um alerta de uma regra em um distrito | `cod_distrito` + `regra` (no script: chave substituta `id_alerta`) | distrito | (tabela de alertas) | 38 | SIMULADO + TERRITÓRIO |
| `fato_indicadores_distrito` | Priorização do território | um distrito | `cod_distrito` | distrito | Índice de prioridade · Classe de prioridade | 96 | REAL + ESTIMATIVA DO MODELO |
| `fato_recomendacoes` | Priorização do território | uma campanha recomendada para um distrito urgente ou de prioridade alta | `cod_distrito` + `acao` (no script: chave substituta `id_recomendacao`) | distrito | Campanha indicada | 54 | ESTIMATIVA DO MODELO |
| `fato_risco_setor` | Risco geológico | um setor de risco dentro de um distrito | `id_setor` + `cod_distrito` | distrito | (contagem de setores por grau) | 1.480 | REAL |

Tipos de fato:

- **Fato sem medida** (*factless*): `fato_item_plano`, `fato_documento_pendente` e `fato_encaminhamento` registram acontecimentos; as medidas são **contagens** (quantas pessoas, quantos direitos, quantos encaminhamentos).
- **Fato de foto periódica** (*snapshot*): `fato_indicadores_distrito` traz a situação de cada distrito na data das bases públicas, com medidas numéricas (população, famílias no CadÚnico, cobertura do Bolsa Família e do BPC, lacuna, índice de prioridade).
- **Fatos derivados**: `fato_alertas` e `fato_recomendacoes` são gerados por regras e pelo modelo de priorização a partir dos outros fatos.

## 3. Dimensões

| Dimensão | Grão (1 linha =) | Chave | Linhas | Origem | Papel |
|---|---|---|---|---|---|
| `dim_subprefeitura` | uma subprefeitura | `subprefeitura` | 32 | REAL | topo da hierarquia; segurança por gestor (`email_gestor`) |
| `dim_distrito` | um distrito | `cod_distrito` | 96 | REAL | **dimensão conformada**: liga território e app |
| `dim_equipamento` | um serviço público (UBS, CRAS, cartório, Poupatempo) | `id_equipamento` | 670 | REAL | unidade do agente (UBS/CRAS) |
| `dim_caso` | uma pessoa acompanhada | `id_caso` | 5.000 | SIMULADO | perfil da pessoa (faixas, área de risco, lembrete) |
| `dim_programa` | um dos 7 programas | `id_programa` | 7 | REAL | filtro por direito |
| `dim_tempo` | um dia | `id_data` | — | proposta | evolução em escala (os dados atuais não têm data) |

Hierarquia usada pelos filtros do painel: **subprefeitura → distrito → unidade (equipamento) → caso**.

## 4. Matriz de barramento

Legenda: **●** ligação direta · **◐** chega pela hierarquia · **P** proposta em escala · **T** guardado como texto (sem ligação)

| Fato \ Dimensão | Subprefeitura | Distrito | Equipamento (unidade) | Caso | Programa | Tempo |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `fato_item_plano` | ◐ | ◐ | ◐ | ● | ● | |
| `fato_documento_pendente` | ◐ | ◐ | ◐ | ● | | |
| `fato_encaminhamento` | ◐ | ◐ | ◐ | ● | ● | P |
| `fato_alertas` | ◐ | ● | | | | |
| `fato_indicadores_distrito` | ◐ | ● | | | | |
| `fato_recomendacoes` | ◐ | ● | | | T | |
| `fato_risco_setor` | ◐ | ● | | | | |

**Leitura:** a coluna **Distrito** é preenchida em todas as linhas. É ela que permite colocar, no mesmo filtro, o que os agentes registram no app e o que as bases públicas mostram sobre o território. Os fatos do app chegam ao distrito pela unidade do agente (caso → unidade → distrito); os fatos do território ligam direto.

## 5. Decisões de modelagem

| Decisão | Motivo |
|---|---|
| **Constelação de fatos** (*Galaxy*) | Há processos com grãos diferentes (pessoa, encaminhamento, distrito, setor). Juntar tudo em um fato só misturaria grãos e duplicaria números. |
| **Dimensões em floco de neve** (*Snowflake*) na hierarquia territorial | O painel filtra por subprefeitura → distrito → unidade, e cada gestor vê só a sua subprefeitura. Com tabelas pequenas (o maior fato tem 13.404 linhas), a normalização não afeta o desempenho. |
| **Dimensões degeneradas** (situação, documento, destino, resultado) | Têm poucos valores e só um atributo; ficam como texto dentro do fato, como no Power BI. |
| **`dim_tempo` como proposta** | Os dados simulados não têm data. Com o app em uso, a data do encaminhamento alimenta a dimensão e permite ver a evolução. |
| **Coluna `origem` em todas as tabelas** | Separa o que é real (bases públicas), estimado (modelo de priorização) e simulado (app). Quando o app estiver em uso, o modelo continua igual: muda só a origem. |
| **Tabelas de apoio fora da estrela** | `distritos_base` e `fato_beneficios_distrito` são etapas do tratamento (os números já estão em `fato_indicadores_distrito`); `metricas_modelo`, `sensibilidade_pesos` e `teste_barreiras` validam o modelo de priorização. |
| **Dados pessoais fora do modelo analítico** | Nome, telefone, CPF, profissionais e anotações ficam só no banco do app (LGPD). O painel trabalha com o `id_caso` e com faixas. |
| **Caso ligado à unidade, não ao distrito** | Evita dois caminhos até o distrito. Em 5 dos 5.000 casos o distrito de moradia é diferente do distrito da unidade; o painel mostra o caso onde ele é atendido. |
