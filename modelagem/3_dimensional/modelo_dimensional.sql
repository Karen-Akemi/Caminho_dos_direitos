-- =====================================================================
-- Caminho dos Direitos - Global Solution FIAP 2026.2 (CitizenTech)
-- Modelo dimensional (Snowflake + Galaxy / constelacao de fatos)
-- Mesmo conteudo da v3, em formato facil de importar no Data Modeler:
-- chaves estrangeiras dentro de cada CREATE TABLE, tabelas em ordem de
-- dependencia e texto sem acentos.
--
-- Abrir: File > Import > DDL File > este arquivo > Oracle Database 19c
--        > marcar todas as tabelas > Merge.
--
-- 13 tabelas: 6 dimensoes (dim_tempo e proposta em escala) e 7 fatos.
-- Origens: territorio (REAL + ESTIMATIVA DO MODELO) e app (SIMULADO),
-- cruzadas pelas dimensoes conformadas dim_distrito e dim_programa.
-- =====================================================================


CREATE TABLE dim_subprefeitura (
    subprefeitura   VARCHAR2(60)  NOT NULL,
    qtd_distritos   NUMBER(3),
    email_gestor    VARCHAR2(120),
    CONSTRAINT pk_dim_subprefeitura PRIMARY KEY (subprefeitura)
);

CREATE TABLE dim_distrito (
    cod_distrito      NUMBER(3)     NOT NULL,
    nome_distrito     VARCHAR2(60)  NOT NULL,
    subprefeitura     VARCHAR2(60)  NOT NULL,
    area_km2          NUMBER(10,3),
    pop_2022          NUMBER(10),
    densidade_hab_km2 NUMBER(12,3),
    CONSTRAINT pk_dim_distrito PRIMARY KEY (cod_distrito),
    CONSTRAINT fk_distrito_subpref FOREIGN KEY (subprefeitura) REFERENCES dim_subprefeitura (subprefeitura)
);

CREATE TABLE dim_equipamento (
    id_equipamento    NUMBER(6)     NOT NULL,
    tipo_equipamento  VARCHAR2(20)  NOT NULL,
    nome_equipamento  VARCHAR2(150) NOT NULL,
    eh_unidade_app    CHAR(1)       NOT NULL,
    cod_distrito      NUMBER(3)     NOT NULL,
    lat               NUMBER(10,6),
    lon               NUMBER(10,6),
    CONSTRAINT pk_dim_equipamento PRIMARY KEY (id_equipamento),
    CONSTRAINT fk_equip_distrito FOREIGN KEY (cod_distrito) REFERENCES dim_distrito (cod_distrito)
);

CREATE TABLE dim_caso (
    id_caso             NUMBER(8)    NOT NULL,
    id_unidade          NUMBER(6)    NOT NULL,
    cod_distrito        NUMBER(3)    NOT NULL,
    faixa_etaria        VARCHAR2(10) NOT NULL,
    faixa_etaria_ordem  NUMBER(1)    NOT NULL,
    faixa_renda         VARCHAR2(20) NOT NULL,
    faixa_renda_ordem   NUMBER(1)    NOT NULL,
    area_risco_r3r4     VARCHAR2(3)  NOT NULL,
    situacao_caso       VARCHAR2(10) NOT NULL,
    whatsapp            VARCHAR2(25) NOT NULL,
    aceita_lembrete     VARCHAR2(20) NOT NULL,
    formato_lembrete    VARCHAR2(15),
    categoria_lembrete  VARCHAR2(40),
    origem              VARCHAR2(30) NOT NULL,
    CONSTRAINT pk_dim_caso PRIMARY KEY (id_caso),
    CONSTRAINT fk_caso_unidade FOREIGN KEY (id_unidade) REFERENCES dim_equipamento (id_equipamento)
);

CREATE TABLE dim_programa (
    id_programa                   NUMBER(2)    NOT NULL,
    programa                      VARCHAR2(60) NOT NULL,
    onde_pedir                    VARCHAR2(60),
    tem_dado_publico_por_distrito CHAR(1)      NOT NULL,
    CONSTRAINT pk_dim_programa PRIMARY KEY (id_programa)
);

CREATE TABLE dim_tempo (
    id_data         NUMBER(8)    NOT NULL,
    data_completa   DATE         NOT NULL,
    dia             NUMBER(2)    NOT NULL,
    mes             NUMBER(2)    NOT NULL,
    nome_mes        VARCHAR2(12) NOT NULL,
    trimestre       NUMBER(1)    NOT NULL,
    ano             NUMBER(4)    NOT NULL,
    dia_semana      VARCHAR2(15) NOT NULL,
    CONSTRAINT pk_dim_tempo PRIMARY KEY (id_data)
);

CREATE TABLE fato_item_plano (
    id_caso         NUMBER(8)    NOT NULL,
    id_programa     NUMBER(2)    NOT NULL,
    situacao        VARCHAR2(30) NOT NULL,
    situacao_ordem  NUMBER(1)    NOT NULL,
    origem          VARCHAR2(30) NOT NULL,
    CONSTRAINT pk_fato_item_plano PRIMARY KEY (id_caso, id_programa),
    CONSTRAINT fk_item_caso FOREIGN KEY (id_caso) REFERENCES dim_caso (id_caso),
    CONSTRAINT fk_item_programa FOREIGN KEY (id_programa) REFERENCES dim_programa (id_programa)
);

CREATE TABLE fato_documento_pendente (
    id_caso         NUMBER(8)    NOT NULL,
    documento       VARCHAR2(40) NOT NULL,
    origem          VARCHAR2(30) NOT NULL,
    CONSTRAINT pk_fato_documento_pendente PRIMARY KEY (id_caso, documento),
    CONSTRAINT fk_doc_caso FOREIGN KEY (id_caso) REFERENCES dim_caso (id_caso)
);

CREATE TABLE fato_encaminhamento (
    id_encaminhamento NUMBER(8)    NOT NULL,
    id_caso           NUMBER(8)    NOT NULL,
    id_programa       NUMBER(2)    NOT NULL,
    id_data           NUMBER(8),
    tipo_destino      VARCHAR2(20) NOT NULL,
    resultado         VARCHAR2(20) NOT NULL,
    resultado_ordem   NUMBER(1)    NOT NULL,
    lembrete_enviado  VARCHAR2(3)  NOT NULL,
    formato_lembrete  VARCHAR2(15),
    grupo_lembrete    VARCHAR2(30),
    origem            VARCHAR2(30) NOT NULL,
    CONSTRAINT pk_fato_encaminhamento PRIMARY KEY (id_encaminhamento),
    CONSTRAINT fk_enc_caso FOREIGN KEY (id_caso) REFERENCES dim_caso (id_caso),
    CONSTRAINT fk_enc_programa FOREIGN KEY (id_programa) REFERENCES dim_programa (id_programa),
    CONSTRAINT fk_enc_tempo FOREIGN KEY (id_data) REFERENCES dim_tempo (id_data)
);

CREATE TABLE fato_alertas (
    id_alerta       NUMBER(6)     NOT NULL,
    cod_distrito    NUMBER(3)     NOT NULL,
    regra           VARCHAR2(60)  NOT NULL,
    alerta          VARCHAR2(400) NOT NULL,
    gravidade       VARCHAR2(10)  NOT NULL,
    ordem           NUMBER(4),
    origem          VARCHAR2(30)  NOT NULL,
    CONSTRAINT pk_fato_alertas PRIMARY KEY (id_alerta),
    CONSTRAINT fk_alerta_distrito FOREIGN KEY (cod_distrito) REFERENCES dim_distrito (cod_distrito)
);

CREATE TABLE fato_indicadores_distrito (
    cod_distrito                  NUMBER(3)    NOT NULL,
    pop_total                     NUMBER(10),
    familias_cadunico             NUMBER(10),
    dist_cras_km                  NUMBER(8,3),
    setores_risco_r3r4            NUMBER(5),
    familias_pbf                  NUMBER(10),
    bpc_idoso                     NUMBER(10),
    bpc_pcd                       NUMBER(10),
    pop_65_mais                   NUMBER(10),
    cadunico_por_1000             NUMBER(10,4),
    pct_65                        NUMBER(8,6),
    cobertura_pbf                 NUMBER(8,6),
    taxa_bpc_idoso                NUMBER(8,6),
    cras_referencia               VARCHAR2(150),
    bpc_idoso_esperado_taxa       NUMBER(8,6),
    cobertura_pbf_esperada        NUMBER(8,6),
    lacuna_bpc_idosos             NUMBER(10,1),
    lacuna_pbf_familias           NUMBER(10,1),
    lacuna_pessoas                NUMBER(10,1),
    lacuna_por_1000               NUMBER(10,2),
    indice_prioridade             NUMBER(6,2),
    classe_prioridade             VARCHAR2(10),
    tem_risco                     VARCHAR2(12),
    origem_indicadores            VARCHAR2(30),
    origem_esperado_lacuna_indice VARCHAR2(30),
    CONSTRAINT pk_fato_indicadores_distrito PRIMARY KEY (cod_distrito),
    CONSTRAINT fk_ind_distrito FOREIGN KEY (cod_distrito) REFERENCES dim_distrito (cod_distrito)
);

CREATE TABLE fato_recomendacoes (
    id_recomendacao   NUMBER(6)     NOT NULL,
    cod_distrito      NUMBER(3)     NOT NULL,
    classe_prioridade VARCHAR2(10)  NOT NULL,
    acao              VARCHAR2(200) NOT NULL,
    programa          VARCHAR2(40)  NOT NULL,
    cras_referencia   VARCHAR2(150),
    motivo            VARCHAR2(300),
    publico_estimado  NUMBER(10),
    origem            VARCHAR2(30)  NOT NULL,
    CONSTRAINT pk_fato_recomendacoes PRIMARY KEY (id_recomendacao),
    CONSTRAINT fk_rec_distrito FOREIGN KEY (cod_distrito) REFERENCES dim_distrito (cod_distrito)
);

CREATE TABLE fato_risco_setor (
    id_setor        NUMBER(6)    NOT NULL,
    cod_distrito    NUMBER(3)    NOT NULL,
    grau            VARCHAR2(2)  NOT NULL,
    area_m2         NUMBER(14,1),
    CONSTRAINT pk_fato_risco_setor PRIMARY KEY (id_setor, cod_distrito),
    CONSTRAINT fk_risco_distrito FOREIGN KEY (cod_distrito) REFERENCES dim_distrito (cod_distrito)
);


-- Comentarios

COMMENT ON TABLE dim_subprefeitura IS 'Subprefeituras de SP. email_gestor permite seguranca por linha: cada gestor ve so a sua.';

COMMENT ON TABLE dim_distrito IS '96 distritos de SP (GeoSampa / Censo 2022). Dimensao conformada entre app e territorio.';

COMMENT ON TABLE dim_equipamento IS 'CRAS, UBS, cartorios e Poupatempo. eh_unidade_app = S: CRAS/UBS onde o agente esta lotado (unidade do app).';

COMMENT ON TABLE dim_caso IS 'Uma pessoa acompanhada pelo app. Sem nome, apelido, CPF ou telefone (LGPD); renda so por faixa.';

COMMENT ON TABLE dim_programa IS '7 programas: Documentacao basica, CadUnico, Bolsa Familia, BPC, Tarifa Social, Pe-de-Meia, Farmacia Popular.';

COMMENT ON TABLE dim_tempo IS 'PROPOSTA EM ESCALA. Nao carregada: os dados simulados nao tem data.';

COMMENT ON TABLE fato_item_plano IS 'Grao: um direito sugerido por caso, com situacao. Fato sem medida. SIMULADO.';

COMMENT ON TABLE fato_documento_pendente IS 'Grao: um documento faltante por caso. Fato sem medida. SIMULADO.';

COMMENT ON TABLE fato_encaminhamento IS 'Grao: um encaminhamento, com destino, resultado e lembrete por WhatsApp. SIMULADO.';

COMMENT ON TABLE fato_alertas IS 'Grao: alerta por distrito, cruzando app e territorio. SIMULADO + TERRITORIO.';

COMMENT ON TABLE fato_indicadores_distrito IS 'Grao: distrito. Indicadores publicos (REAL) + esperado, lacuna e prioridade (ESTIMATIVA DO MODELO).';

COMMENT ON TABLE fato_recomendacoes IS 'Grao: campanha recomendada por distrito (so prioridade urgente ou alta). ESTIMATIVA DO MODELO.';

COMMENT ON TABLE fato_risco_setor IS 'Grao: setor de risco R1-R4 por distrito (GeoSampa). REAL.';

COMMENT ON COLUMN dim_caso.id_unidade IS 'UBS/CRAS do agente responsavel. Os filtros de subprefeitura, distrito e unidade chegam ao caso por aqui.';

COMMENT ON COLUMN dim_caso.cod_distrito IS 'Distrito de moradia (atributo). O relacionamento usa o distrito da unidade.';

COMMENT ON COLUMN dim_caso.categoria_lembrete IS 'Coluna calculada no Power BI (quadro Cobertura dos lembretes).';

COMMENT ON COLUMN fato_item_plano.situacao IS 'Dimensao degenerada: Ja recebe, Precisa atualizar, Ainda nao pediu, Falta documento, Bloqueado.';

COMMENT ON COLUMN fato_documento_pendente.documento IS 'Dimensao degenerada: tipo de documento que falta.';

COMMENT ON COLUMN fato_encaminhamento.tipo_destino IS 'Dimensao degenerada: CRAS, UBS, Poupatempo, Cartorio, INSS.';

COMMENT ON COLUMN fato_encaminhamento.resultado IS 'Dimensao degenerada: Agendado, Compareceu, Concluido, Faltou.';

COMMENT ON COLUMN fato_encaminhamento.grupo_lembrete IS 'Coluna calculada no Power BI a partir de lembrete_enviado (quadro Efetividade do atendimento).';

COMMENT ON COLUMN fato_encaminhamento.id_data IS 'PROPOSTA EM ESCALA: data do atendimento. Vazio nos dados atuais.';

COMMENT ON COLUMN fato_recomendacoes.programa IS 'Texto do programa da campanha (BPC, Bolsa Familia, CadUnico ou Todos).';



-- =====================================================================
-- TABELAS DE APOIO (estao no Power BI, ficam fora da estrela)
-- Nao sao fatos de negocio: nao tem grao proprio para analise no painel.
-- =====================================================================
-- Dados reais intermediarios (usados para montar fato_indicadores_distrito):
--   distritos_base            1 linha por distrito: populacao, CadUnico, CRAS, risco, PBF, BPC
--   fato_beneficios_distrito  1 linha por distrito: familias PBF, BPC idoso e PcD, pop 65+
-- Validacao do modelo de priorizacao (ESTIMATIVA DO MODELO):
--   metricas_modelo           erro e R2 dos modelos testados (Random Forest x Gradient Boosting)
--   sensibilidade_pesos       estabilidade do ranking quando os pesos do indice mudam
--   teste_barreiras           correlacao das barreiras (distancia do CRAS, setores R3/R4) com a lacuna
