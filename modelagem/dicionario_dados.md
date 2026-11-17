# Dicionário de dados — Caminho dos Direitos

Descreve todas as tabelas e colunas do **modelo dimensional** (Snowflake + Galaxy) que alimenta o *Painel do monitoramento* no Power BI. Tipos e chaves seguem o script [`3_dimensional/modelo_dimensional.sql`](3_dimensional/modelo_dimensional.sql); valores e exemplos foram tirados dos arquivos da pasta [`dados/`](../dados) (`saida`, `saida_app`, `saida_modelo`).

Documentos relacionados: [modelo conceitual](1_conceitual/modelo_conceitual.md) (entidades e regras de negócio) · [matriz de granularidade e barramento](3_dimensional/matriz_granularidade_barramento.md).

## Convenções

| Item | Significado |
|---|---|
| **Origem** | `REAL` = bases públicas · `ESTIMATIVA DO MODELO` = calculado pelo modelo de priorização · `SIMULADO` = dados que viriam do app, gerados a partir dos dados reais de cada distrito |
| **PK / FK** | Chave primária / chave estrangeira (com a tabela de destino) |
| **Dimensão degenerada** | Atributo com poucos valores guardado como texto dentro do fato (situação, documento, destino, resultado) |
| **Coluna `_ordem`** | Número usado só para ordenar categorias nos gráficos |
| **S / N** | Sim / Não. Nos CSVs essas colunas aparecem como `True` / `False` |
| **Proposta** | Prevista para quando o app estiver em uso; não existe nos dados atuais |
| **Arquivos CSV** | Separador `;` e vírgula decimal |

## Resumo das tabelas

| Tabela | Tipo | Grão (1 linha =) | Linhas | Origem |
|---|---|---|---|---|
| `dim_subprefeitura` | dimensão | uma subprefeitura | 32 | REAL |
| `dim_distrito` | dimensão (conformada) | um distrito | 96 | REAL |
| `dim_equipamento` | dimensão | um serviço público | 670 | REAL |
| `dim_programa` | dimensão | um programa | 7 | catálogo do projeto |
| `dim_caso` | dimensão | uma pessoa acompanhada | 5.000 | SIMULADO |
| `dim_tempo` | dimensão | um dia | — | proposta |
| `fato_item_plano` | fato sem medida | um direito sugerido por pessoa | 13.404 | SIMULADO |
| `fato_documento_pendente` | fato sem medida | um documento faltante por pessoa | 929 | SIMULADO |
| `fato_documento_historico` | fato de acompanhamento | um documento identificado por pessoa, pendente ou resolvido | 1.198 | SIMULADO |
| `fato_encaminhamento` | fato sem medida | um encaminhamento | 3.191 | SIMULADO |
| `fato_alertas` | fato derivado | um alerta por regra e distrito | 38 | SIMULADO + TERRITÓRIO |
| `fato_indicadores_distrito` | fato de foto (snapshot) | um distrito | 96 | REAL + ESTIMATIVA DO MODELO |
| `fato_recomendacoes` | fato derivado | uma campanha recomendada por distrito | 54 | ESTIMATIVA DO MODELO |
| `fato_risco_setor` | fato | um setor de risco por distrito | 1.480 | REAL |

## Tabelas e colunas

### `dim_subprefeitura`

Subprefeituras de São Paulo. Topo da hierarquia territorial e base da segurança por gestor.

- **Origem:** REAL (GeoSampa)
- **Arquivo:** [`dados/saida/dim_subprefeitura.csv`](../dados/saida/dim_subprefeitura.csv)
- **Linhas:** 32
- **Chave primária:** `subprefeitura`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `subprefeitura` | VARCHAR2(60) | PK | Nome da subprefeitura | 32 valores; ex.: Aricanduva/Formosa/Carrão |
| `qtd_distritos` | NUMBER(3) |  | Quantidade de distritos da subprefeitura | 1 · 2 · 3 · 4 · 5 · 6 · 8 |
| `email_gestor` | VARCHAR2(120) |  | E-mail do gestor que vê só os dados da sua subprefeitura (segurança por linha). Vazio nos dados atuais | (vazio) |

### `dim_distrito`

Os 96 distritos de São Paulo. Dimensão conformada: liga os dados do território aos do app.

- **Origem:** REAL (GeoSampa, Censo 2022)
- **Arquivo:** [`dados/saida/dim_distrito.csv`](../dados/saida/dim_distrito.csv)
- **Linhas:** 96
- **Chave primária:** `cod_distrito`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `cod_distrito` | NUMBER(3) | PK | Código do distrito | 1 a 96 |
| `nome_distrito` | VARCHAR2(60) |  | Nome do distrito | 96 valores; ex.: Pirituba |
| `subprefeitura` | VARCHAR2(60) | FK → `dim_subprefeitura.subprefeitura` | Subprefeitura a que o distrito pertence | 32 valores; ex.: Pirituba/Jaraguá |
| `area_km2` | NUMBER(10,3) |  | Área em km² | 2,194 a 208,174 |
| `pop_2022` | NUMBER(10) |  | População no Censo 2022 | 11.443 a 384.873 |
| `densidade_hab_km2` | NUMBER(12,3) |  | Habitantes por km² | 54,968 a 25.334,438 |

### `dim_equipamento`

Serviços públicos com endereço: UBS, CRAS, cartórios e Poupatempo. UBS e CRAS também são a unidade onde o agente trabalha.

- **Origem:** REAL (CNES, GeoSampa, SMADS)
- **Arquivo:** [`dados/saida/dim_equipamento.csv`](../dados/saida/dim_equipamento.csv)
- **Linhas:** 670
- **Chave primária:** `id_equipamento`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_equipamento` | NUMBER(6) | PK | Identificador do equipamento | 1 a 704 |
| `tipo_equipamento` | VARCHAR2(20) |  | Tipo de serviço | CRAS · Cartório · Poupatempo · UBS |
| `nome_equipamento` | VARCHAR2(150) |  | Nome ou endereço do serviço | 670 valores; ex.: CRAS - Avenida Tiradentes, 749 |
| `eh_unidade_app` | CHAR(1) |  | S quando é UBS ou CRAS, onde há agentes usando o app (no CSV: True/False) | S (UBS/CRAS) · N |
| `cod_distrito` | NUMBER(3) | FK → `dim_distrito.cod_distrito` | Distrito onde o serviço fica | 1 a 96 |
| `lat` | NUMBER(10,6) |  | Latitude | -23,907 a -23,4 |
| `lon` | NUMBER(10,6) |  | Longitude | -46,805 a -46,367 |

### `dim_programa`

Os 7 programas (direitos) que o app sugere.

- **Origem:** Catálogo do projeto
- **Arquivo:** [`dados/saida_modelo/dim_programa.csv`](../dados/saida_modelo/dim_programa.csv)
- **Linhas:** 7
- **Chave primária:** `id_programa`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_programa` | NUMBER(2) | PK | Identificador do programa | 1 · 2 · 3 · 4 · 5 · 6 · 7 |
| `programa` | VARCHAR2(60) |  | Nome do programa | BPC · Bolsa Família · CadÚnico · Documentação básica · Farmácia Popular · Pé-de-Meia · Tarifa Social de Energia |
| `onde_pedir` | VARCHAR2(60) |  | Órgão ou serviço onde a pessoa pede | CRAS (SMADS) · Cartório / Poupatempo · Distribuidora (Enel SP) · INSS · MDS via CadÚnico · MEC · Ministério da Saúde |
| `tem_dado_publico_por_distrito` | CHAR(1) |  | S quando há base pública por distrito para comparar (no CSV: True/False) | S · N |

### `dim_caso`

Uma pessoa acompanhada pelo app. Sem nome, apelido, CPF ou telefone (LGPD).

- **Origem:** SIMULADO (gerado a partir dos dados reais por distrito)
- **Arquivo:** [`dados/saida_app/dim_caso.csv`](../dados/saida_app/dim_caso.csv)
- **Linhas:** 5.000
- **Chave primária:** `id_caso`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_caso` | NUMBER(8) | PK | Identificador do caso (pessoa) | 1 a 5000 |
| `id_unidade` | NUMBER(6) | FK → `dim_equipamento.id_equipamento` | UBS ou CRAS do agente responsável. Os filtros de subprefeitura, distrito e unidade chegam ao caso por aqui | 1 a 635 |
| `cod_distrito` | NUMBER(3) |  | Distrito onde a pessoa mora (atributo; não é usado no relacionamento) | 1 a 96 |
| `faixa_etaria` | VARCHAR2(10) |  | Faixa de idade | 0–5 · 6–17 · 18–29 · 30–64 · 65+ |
| `faixa_etaria_ordem` | NUMBER(1) |  | Ordem da faixa para os gráficos | 1 · 2 · 3 · 4 · 5 |
| `faixa_renda` | VARCHAR2(20) |  | Faixa de renda por pessoa (o app não guarda o valor) | até R$ 218 · até R$ 405 · até R$ 810 · até R$ 1.621 · acima · não informado |
| `faixa_renda_ordem` | NUMBER(1) |  | Ordem da faixa para os gráficos | 1 · 2 · 3 · 4 · 5 · 6 |
| `area_risco_r3r4` | VARCHAR2(3) |  | A casa fica em setor de risco alto ou muito alto (R3/R4) — agravante | Não · Sim |
| `situacao_caso` | VARCHAR2(10) |  | Situação do acompanhamento | Ativo · Encerrado |
| `whatsapp` | VARCHAR2(25) |  | Como a pessoa recebe lembretes | Sem WhatsApp · WhatsApp de familiar · WhatsApp próprio |
| `aceita_lembrete` | VARCHAR2(20) |  | Se aceitou receber lembretes | Não · Sem como receber · Sim |
| `formato_lembrete` | VARCHAR2(15) |  | Formato preferido do lembrete (vazio quando não recebe) | Texto · Texto e áudio · Áudio |
| `categoria_lembrete` | VARCHAR2(40) |  | Coluna calculada no Power BI para o quadro Cobertura dos lembretes | calculada no Power BI |
| `origem` | VARCHAR2(30) |  | Origem do dado | SIMULADO |
| `data_abertura` | DATE |  | Dia em que o agente cadastrou a pessoa no app (premissa da simulação: piloto de 04/05 a 13/11/2026) | 2026-05-04 a 2026-11-13 |
| `data_encerramento` | DATE |  | Dia em que o caso foi encerrado (vazio quando ativo) | até 2026-11-13 |

### `dim_tempo`

Calendário. Não existe como arquivo: os fatos já trazem datas (simuladas) e, no Power BI, a tabela é criada com `CALENDAR(DATE(2026;5;4); DATE(2026;11;13))` e ligada a `data_abertura`, `data_encaminhamento` e `data_identificacao`.

- **Origem:** proposta
- **Arquivo:** —
- **Linhas:** —
- **Chave primária:** `id_data`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_data` | NUMBER(8) | PK | Data no formato AAAAMMDD | proposta |
| `data_completa` | DATE |  | Data | proposta |
| `dia` | NUMBER(2) |  | Dia do mês | proposta |
| `mes` | NUMBER(2) |  | Número do mês | proposta |
| `nome_mes` | VARCHAR2(12) |  | Nome do mês | proposta |
| `trimestre` | NUMBER(1) |  | Trimestre (1 a 4) | proposta |
| `ano` | NUMBER(4) |  | Ano | proposta |
| `dia_semana` | VARCHAR2(15) |  | Dia da semana | proposta |

### `fato_item_plano`

Grão: um direito sugerido para uma pessoa, com a situação marcada pelo agente. Fato sem medida (contagens).

- **Origem:** SIMULADO
- **Arquivo:** [`dados/saida_app/fato_item_plano.csv`](../dados/saida_app/fato_item_plano.csv)
- **Linhas:** 13.404
- **Chave primária:** `id_caso, id_programa`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_caso` | NUMBER(8) | PK FK → `dim_caso.id_caso` | Pessoa | 1 a 5000 |
| `id_programa` | NUMBER(2) | PK FK → `dim_programa.id_programa` | Programa sugerido | 1 · 2 · 3 · 4 · 5 · 6 · 7 |
| `situacao` | VARCHAR2(30) |  | Situação do direito marcada pelo agente (dimensão degenerada) | Já recebe · Precisa atualizar · Ainda não pediu · Falta documento · Bloqueado |
| `situacao_ordem` | NUMBER(1) |  | Ordem da situação para os gráficos | 1 · 2 · 3 · 4 · 5 |
| `origem` | VARCHAR2(30) |  | Origem do dado | SIMULADO |

### `fato_documento_pendente`

Grão: um documento que falta para uma pessoa. Fato sem medida.

- **Origem:** SIMULADO
- **Arquivo:** [`dados/saida_app/fato_documento_pendente.csv`](../dados/saida_app/fato_documento_pendente.csv)
- **Linhas:** 929
- **Chave primária:** `id_caso, documento`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_caso` | NUMBER(8) | PK FK → `dim_caso.id_caso` | Pessoa | 1 a 4995 |
| `documento` | VARCHAR2(40) | PK | Documento que falta (dimensão degenerada) | CPF · Carteira de trabalho · Certidão de nascimento · Comprovante de residência · RG/CIN · Título de eleitor |
| `origem` | VARCHAR2(30) |  | Origem do dado | SIMULADO |
| `data_identificacao` | DATE |  | Dia em que o agente identificou que o documento falta (= abertura do caso) | 2026-05-04 a 2026-11-13 |

### `fato_documento_historico`

Grão: um documento que faltava para uma pessoa, **pendente ou já resolvido**. É a base da evolução no tempo do painel ("chegaram 30 sem documento, 20 já foram atendidas, 10 aguardam"). Os pendentes são as mesmas linhas de `fato_documento_pendente`.

- **Origem:** SIMULADO
- **Arquivo:** [`dados/saida_app/fato_documento_historico.csv`](../dados/saida_app/fato_documento_historico.csv)
- **Linhas:** 1.198
- **Chave primária:** `id_caso, documento`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_caso` | NUMBER(8) | PK FK → `dim_caso.id_caso` | Pessoa | 1 a 4995 |
| `documento` | VARCHAR2(40) | PK | Documento que faltava | CPF · Carteira de trabalho · Certidão de nascimento · Comprovante de residência · RG/CIN · Título de eleitor |
| `data_identificacao` | DATE |  | Dia em que o agente identificou a falta | 2026-05-04 a 2026-11-13 |
| `data_resolucao` | DATE |  | Dia em que o encaminhamento de Documentação básica foi concluído (vazio = pendente) | 2026-05-24 a 2026-11-13 |
| `situacao_documento` | VARCHAR2(10) |  | Situação atual | Pendente · Resolvido |
| `dias_ate_resolver` | NUMBER(4) |  | Dias entre identificar e resolver (vazio = pendente) | 5 a 69 |
| `origem` | VARCHAR2(30) |  | Origem do dado | SIMULADO |

### `fato_encaminhamento`

Grão: uma ida da pessoa a um serviço, com resultado e lembrete por WhatsApp.

- **Origem:** SIMULADO
- **Arquivo:** [`dados/saida_app/fato_encaminhamento.csv`](../dados/saida_app/fato_encaminhamento.csv)
- **Linhas:** 3.191
- **Chave primária:** `id_encaminhamento`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_encaminhamento` | NUMBER(8) | PK | Identificador do encaminhamento | 1 a 3191 |
| `id_caso` | NUMBER(8) | FK → `dim_caso.id_caso` | Pessoa encaminhada | 1 a 5000 |
| `id_programa` | NUMBER(2) | FK → `dim_programa.id_programa` | Direito que motivou o encaminhamento | 1 · 2 · 3 · 4 · 5 · 6 · 7 |
| `tipo_destino` | VARCHAR2(20) |  | Tipo de serviço de destino (dimensão degenerada) | CRAS · Cartório · INSS · Poupatempo · UBS |
| `resultado` | VARCHAR2(20) |  | Resultado do encaminhamento (dimensão degenerada) | Agendado · Compareceu · Concluído · Faltou |
| `resultado_ordem` | NUMBER(1) |  | Ordem do resultado para os gráficos | 1 · 2 · 3 · 4 |
| `lembrete_enviado` | VARCHAR2(3) |  | Se algum lembrete foi enviado antes do atendimento | Não · Sim |
| `formato_lembrete` | VARCHAR2(15) |  | Formato do lembrete enviado (vazio quando não houve) | Texto · Texto e áudio · Áudio |
| `grupo_lembrete` | VARCHAR2(30) |  | Coluna calculada no Power BI a partir de lembrete_enviado (quadro Efetividade do atendimento) | calculada no Power BI |
| `origem` | VARCHAR2(30) |  | Origem do dado | SIMULADO |
| `data_encaminhamento` | DATE |  | Dia em que o agente encaminhou a pessoa | 2026-05-04 a 2026-11-13 |
| `data_resultado` | DATE |  | Dia do resultado (falta, comparecimento ou conclusão). Vazio quando ainda está agendado | 2026-05-11 a 2026-11-13 |
| `dias_ate_resultado` | NUMBER(4) |  | Dias entre o encaminhamento e o resultado (vazio quando agendado) | 1 a 108 |

### `fato_alertas`

Grão: um alerta de uma regra em um distrito. Cruza o que os agentes registram com os dados do território.

- **Origem:** SIMULADO + TERRITÓRIO
- **Arquivo:** [`dados/saida_app/fato_alertas.csv`](../dados/saida_app/fato_alertas.csv)
- **Linhas:** 38
- **Chave primária:** `id_alerta`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_alerta` | NUMBER(6) | PK | Chave substituta gerada na carga (no CSV a linha é identificada por cod_distrito + regra) | gerada na carga |
| `cod_distrito` | NUMBER(3) | FK → `dim_distrito.cod_distrito` | Distrito do alerta | 7 a 96 |
| `regra` | VARCHAR2(60) |  | Regra que gerou o alerta | Bloqueio no Bolsa Família · Distância + falta · Modelo subestimando · Prioridade alta + direito não pedido |
| `alerta` | VARCHAR2(400) |  | Texto do alerta mostrado no painel | 38 valores; ex.: Cidade Ademar: 13 pessoas com BPC ou Bolsa Família sugeri... |
| `gravidade` | VARCHAR2(10) |  | Gravidade | alta · média |
| `ordem` | NUMBER(4) |  | Ordem de exibição | 1 a 38 |
| `origem` | VARCHAR2(30) |  | Origem do dado | SIMULADO + TERRITÓRIO |

### `fato_indicadores_distrito`

Grão: um distrito. Indicadores públicos (REAL) e cobertura esperada, lacuna e prioridade calculadas pelo modelo (ESTIMATIVA DO MODELO).

- **Origem:** REAL + ESTIMATIVA DO MODELO
- **Arquivo:** [`dados/saida_modelo/fato_indicadores_distrito.csv`](../dados/saida_modelo/fato_indicadores_distrito.csv)
- **Linhas:** 96
- **Chave primária:** `cod_distrito`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `cod_distrito` | NUMBER(3) | PK FK → `dim_distrito.cod_distrito` | Distrito | 1 a 96 |
| `pop_total` | NUMBER(10) |  | População total | 11.443 a 384.873 |
| `familias_cadunico` | NUMBER(10) |  | Famílias no CadÚnico | 655 a 77270 |
| `dist_cras_km` | NUMBER(8,3) |  | Distância até o CRAS mais próximo (km) | 0,189 a 5,273 |
| `setores_risco_r3r4` | NUMBER(5) |  | Quantidade de setores de risco R3/R4 | 0 a 55 |
| `familias_pbf` | NUMBER(10) |  | Famílias no Bolsa Família | 72 a 29434 |
| `bpc_idoso` | NUMBER(10) |  | Idosos que recebem BPC | 155 a 6407 |
| `bpc_pcd` | NUMBER(10) |  | Pessoas com deficiência que recebem BPC | 29 a 5150 |
| `pop_65_mais` | NUMBER(10) |  | População com 65 anos ou mais | 974 a 30.789 |
| `cadunico_por_1000` | NUMBER(10,4) |  | Famílias no CadÚnico por 1.000 habitantes | 7,998 a 604,481 |
| `pct_65` | NUMBER(8,6) |  | Proporção da população com 65+ | 0,07 a 0,23 |
| `cobertura_pbf` | NUMBER(8,6) |  | Famílias no Bolsa Família ÷ famílias no CadÚnico | 0,11 a 0,72 |
| `taxa_bpc_idoso` | NUMBER(8,6) |  | Idosos com BPC ÷ população 65+ | 0,015 a 0,383 |
| `cras_referencia` | VARCHAR2(150) |  | CRAS de referência do distrito | 48 valores; ex.: CRAS - Rua Guerino Giovani Leardini, 290 |
| `bpc_idoso_esperado_taxa` | NUMBER(8,6) |  | Taxa de BPC idoso esperada pelo modelo | 0,023 a 0,274 |
| `cobertura_pbf_esperada` | NUMBER(8,6) |  | Cobertura do Bolsa Família esperada pelo modelo | 0,297 a 0,698 |
| `lacuna_bpc_idosos` | NUMBER(10,1) |  | Idosos com direito provável ao BPC que não recebem | 0 a 1.256 |
| `lacuna_pbf_familias` | NUMBER(10,1) |  | Famílias com direito provável ao Bolsa Família que não recebem | 0 a 3.301 |
| `lacuna_pessoas` | NUMBER(10,1) |  | Total estimado de pessoas com direito provável sem benefício | 0 a 8.252,5 |
| `lacuna_por_1000` | NUMBER(10,2) |  | Lacuna por 1.000 habitantes | 0 a 174,09 |
| `indice_prioridade` | NUMBER(6,2) |  | Índice de prioridade de ação (0 a 100) | 1,2 a 79 |
| `classe_prioridade` | VARCHAR2(10) |  | Classe de prioridade | alta · baixa · média · urgente |
| `tem_risco` | VARCHAR2(12) |  | Se o distrito tem setores R3/R4 | Com R3/R4 · Sem R3/R4 |
| `origem_indicadores` | VARCHAR2(30) |  | Origem dos indicadores | REAL |
| `origem_esperado_lacuna_indice` | VARCHAR2(30) |  | Origem do esperado, da lacuna e do índice | ESTIMATIVA DO MODELO |

### `fato_recomendacoes`

Grão: uma campanha recomendada para um distrito de prioridade urgente ou alta. Corresponde à tela Campanhas do app.

- **Origem:** ESTIMATIVA DO MODELO
- **Arquivo:** [`dados/saida_modelo/fato_recomendacoes.csv`](../dados/saida_modelo/fato_recomendacoes.csv)
- **Linhas:** 54
- **Chave primária:** `id_recomendacao`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_recomendacao` | NUMBER(6) | PK | Chave substituta gerada na carga (no CSV a linha é identificada por cod_distrito + acao) | gerada na carga |
| `cod_distrito` | NUMBER(3) | FK → `dim_distrito.cod_distrito` | Distrito da campanha | 11 a 96 |
| `classe_prioridade` | VARCHAR2(10) |  | Classe de prioridade do distrito | alta · urgente |
| `acao` | VARCHAR2(200) |  | Ação recomendada | Busca ativa Bolsa Família e atualização do CadÚnico · CRAS itinerante ou atendimento do CadÚnico dentro da UBS · Mutirão BPC: busca ativa de idosos 65+ com ACS e CRAS · Priorizar visitas dos ACS nos setores de risco R3/R4 |
| `programa` | VARCHAR2(40) |  | Programa foco (texto; "Todos" quando vale para todos) | BPC · Bolsa Família · CadÚnico · Todos |
| `cras_referencia` | VARCHAR2(150) |  | CRAS de referência | 24 valores; ex.: CRAS - Rua Ibiraiaras, 372 |
| `motivo` | VARCHAR2(300) |  | Por que a ação foi recomendada | 49 valores; ex.: Cobertura de BPC idoso 19,6% vs esperada 25,2% |
| `publico_estimado` | NUMBER(10) |  | Pessoas que a ação pode alcançar | 338 a 77.270 |
| `origem` | VARCHAR2(30) |  | Origem do dado | ESTIMATIVA DO MODELO |

### `fato_risco_setor`

Grão: um setor de risco geológico dentro de um distrito.

- **Origem:** REAL (GeoSampa)
- **Arquivo:** [`dados/saida/fato_risco_setor.csv`](../dados/saida/fato_risco_setor.csv)
- **Linhas:** 1.480
- **Chave primária:** `id_setor, cod_distrito`

| Coluna | Tipo | Chave | Descrição | Valores / exemplo |
|---|---|---|---|---|
| `id_setor` | NUMBER(6) | PK | Identificador do setor de risco | 1 a 1358 |
| `cod_distrito` | NUMBER(3) | PK FK → `dim_distrito.cod_distrito` | Distrito onde o setor fica | 3 a 96 |
| `grau` | VARCHAR2(2) |  | Grau de risco | R1 · R2 · R3 · R4 |
| `area_m2` | NUMBER(14,1) |  | Área do setor dentro do distrito (m²) | 0 a 222.505,7 |

## Colunas dos arquivos de dados que ficam fora do modelo

| Arquivo | Coluna | Motivo |
|---|---|---|
| `dim_equipamento.csv` | `subprefeitura` | Repetida: vem de `dim_distrito` pela hierarquia |
| `fato_indicadores_distrito.csv` | `distrito`, `subprefeitura` | Repetidas: vêm de `dim_distrito` |
| `fato_indicadores_distrito.csv` | `pop_0_6`, `pct_0_6`, `familias_cadunico_pobreza`, `pct_pobreza_cadunico` | Vazias nas bases tratadas |
| `fato_recomendacoes.csv` | `distrito`, `subprefeitura` | Repetidas: vêm de `dim_distrito` |

## Outros arquivos de saída

Ficam em [`dados/`](../dados), fora do modelo dimensional. São resumos e conferências gerados pelos notebooks.

| Arquivo | Linhas | O que traz |
|---|---|---|
| `saida/fato_acesso_distrito_servico.csv` | 384 | Distrito × serviço (CRAS, UBS, cartório, Poupatempo): o serviço mais próximo, a distância em km e quantos há num raio de 2 km e no distrito |
| `saida/kpi_cidade.csv` | 1 | Totais da cidade: população 2022, famílias no CadÚnico e número de CRAS, UBS, cartórios e postos do Poupatempo |
| `saida_modelo/fato_lacuna_programa.csv` | 192 | Distrito × programa (BPC e Bolsa Família): público, beneficiários, cobertura real e esperada e lacuna |
| `saida_modelo/fato_comparacao_risco.csv` | 4 | Distritos com e sem setores R3/R4: diferença em cada indicador e p-valor |
| `saida_modelo/fato_insights.csv` | 5 | Frases de resultado do modelo, em ordem |

Tabelas de apoio carregadas no Power BI, fora do modelo dimensional: `distritos_base` e `fato_beneficios_distrito` (etapas do tratamento; os números já estão em `fato_indicadores_distrito`) e `metricas_modelo`, `sensibilidade_pesos`, `teste_barreiras` (validação do modelo de priorização).

## Rastreabilidade: tela do app → tabela → quadro do painel

| Tela do app | Tabela | Quadro do painel |
|---|---|---|
| 02–04 Novo atendimento | `dim_caso` | Pessoas acompanhadas · Casos em área de risco · Cobertura dos lembretes |
| 05 Plano de Direitos · 06 Detalhe do direito | `fato_item_plano` | Situação dos direitos por programa · Direitos sem acesso · Quem tem direito e ainda não recebe |
| 04 Novo atendimento · Etapa 3 (documentos) · 06 Documentação básica | `fato_documento_pendente` | Documentos que faltam · Pessoas sem documento |
| 07 Registrar encaminhamento · 08 Acompanhamento do caso | `fato_encaminhamento` | Encaminhamentos · Encaminhamentos concluídos · Efetividade do atendimento |
| 09 Campanhas | `fato_recomendacoes` + `fato_indicadores_distrito` | Prioridade de ação por distrito · Onde agir primeiro |
| (regras que cruzam app e território) | `fato_alertas` | Alertas cruzados |
| L1–L5 Login · C1–C3 Coordenação | — | Ficam só no banco do app (dados pessoais e operacionais, LGPD) |
| 10 Anotação por voz | `marcacao` (banco do app; o notebook exporta como `fato_necessidade_caso.csv`) | Fica só no banco do app: só as categorias confirmadas, sem texto nem dado clínico (LGPD) |
