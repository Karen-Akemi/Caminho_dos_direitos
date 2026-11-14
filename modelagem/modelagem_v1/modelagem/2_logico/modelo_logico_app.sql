-- =====================================================================
-- Caminho dos Direitos - Global Solution FIAP 2026.2 (CitizenTech)
-- Modelo do app (base do modelo conceitual) - 16 entidades
--
-- Como gerar o diagrama conceitual no Oracle SQL Developer Data Modeler:
--   1. File > Import > DDL File > este arquivo > Oracle Database 19c > Merge
--      (cria o modelo relacional com as 16 tabelas e as ligacoes)
--   2. Com o modelo relacional aberto, clique em "Engineer to Logical Model"
--      (botao com seta dupla para a esquerda) > Engineer
--   3. O modelo logico mostra as entidades e os relacionamentos com
--      cardinalidade. Em View > Logical Diagram Notation escolha
--      "Bachman" ou "Information Engineering" (pes de galinha).
--
-- Camadas:
--   referencia (territorio e catalogos): subprefeitura, distrito,
--     equipamento, programa, documento
--   operacao do app: profissional, caso, responsabilidade, contato,
--     documento_caso, item_plano, encaminhamento, lembrete, marcacao,
--     campanha, indicacao
-- =====================================================================


-- ===================== REFERENCIA =====================

CREATE TABLE subprefeitura (
    nome_subprefeitura  VARCHAR2(60)  NOT NULL,
    email_gestor        VARCHAR2(120),
    CONSTRAINT pk_subprefeitura PRIMARY KEY (nome_subprefeitura)
);

CREATE TABLE distrito (
    cod_distrito        NUMBER(3)     NOT NULL,
    nome_distrito       VARCHAR2(60)  NOT NULL,
    populacao           NUMBER(10),
    nome_subprefeitura  VARCHAR2(60)  NOT NULL,
    CONSTRAINT pk_distrito PRIMARY KEY (cod_distrito),
    CONSTRAINT fk_distrito_subprefeitura FOREIGN KEY (nome_subprefeitura)
        REFERENCES subprefeitura (nome_subprefeitura)
);

CREATE TABLE equipamento (
    id_equipamento      NUMBER(6)     NOT NULL,
    tipo_equipamento    VARCHAR2(20)  NOT NULL,
    nome_equipamento    VARCHAR2(150) NOT NULL,
    endereco            VARCHAR2(200),
    lat                 NUMBER(10,6),
    lon                 NUMBER(10,6),
    cod_distrito        NUMBER(3)     NOT NULL,
    CONSTRAINT pk_equipamento PRIMARY KEY (id_equipamento),
    CONSTRAINT fk_equipamento_distrito FOREIGN KEY (cod_distrito)
        REFERENCES distrito (cod_distrito)
);

CREATE TABLE programa (
    id_programa         NUMBER(2)     NOT NULL,
    nome_programa       VARCHAR2(60)  NOT NULL,
    onde_pedir          VARCHAR2(60),
    CONSTRAINT pk_programa PRIMARY KEY (id_programa)
);

CREATE TABLE documento (
    tipo_documento      VARCHAR2(40)  NOT NULL,
    CONSTRAINT pk_documento PRIMARY KEY (tipo_documento)
);


-- ===================== OPERACAO DO APP =====================

CREATE TABLE profissional (
    id_profissional     NUMBER(8)     NOT NULL,
    nome_profissional   VARCHAR2(100) NOT NULL,
    cpf                 VARCHAR2(11)  NOT NULL,
    papel               VARCHAR2(30)  NOT NULL,
    situacao            VARCHAR2(15)  NOT NULL,
    id_equipamento      NUMBER(6)     NOT NULL,
    id_aprovador        NUMBER(8),
    CONSTRAINT pk_profissional PRIMARY KEY (id_profissional),
    CONSTRAINT fk_profissional_unidade FOREIGN KEY (id_equipamento)
        REFERENCES equipamento (id_equipamento),
    CONSTRAINT fk_profissional_aprovador FOREIGN KEY (id_aprovador)
        REFERENCES profissional (id_profissional)
);

CREATE TABLE caso (
    id_caso                  NUMBER(8)    NOT NULL,
    apelido                  VARCHAR2(40) NOT NULL,
    faixa_etaria             VARCHAR2(10) NOT NULL,
    faixa_renda              VARCHAR2(20) NOT NULL,
    pessoas_na_casa          NUMBER(2),
    tem_pessoa_65_mais       CHAR(1),
    tem_pessoa_deficiencia   CHAR(1),
    tem_crianca_ate_6        CHAR(1),
    tem_ensino_medio_publico CHAR(1),
    tem_gestante             CHAR(1),
    area_risco_r3r4          CHAR(1)      NOT NULL,
    autorizou_uso_dados      CHAR(1)      NOT NULL,
    situacao_caso            VARCHAR2(10) NOT NULL,
    data_abertura            DATE         NOT NULL,
    cod_distrito             NUMBER(3)    NOT NULL,
    CONSTRAINT pk_caso PRIMARY KEY (id_caso),
    CONSTRAINT fk_caso_distrito FOREIGN KEY (cod_distrito)
        REFERENCES distrito (cod_distrito)
);

-- Periodo em que um profissional acompanha o caso (historico de transferencias).
CREATE TABLE responsabilidade (
    id_caso             NUMBER(8)     NOT NULL,
    id_profissional     NUMBER(8)     NOT NULL,
    data_inicio         DATE          NOT NULL,
    data_fim            DATE,
    CONSTRAINT pk_responsabilidade PRIMARY KEY (id_caso, id_profissional, data_inicio),
    CONSTRAINT fk_resp_caso FOREIGN KEY (id_caso)
        REFERENCES caso (id_caso),
    CONSTRAINT fk_resp_profissional FOREIGN KEY (id_profissional)
        REFERENCES profissional (id_profissional)
);

-- 0..1 por caso: quem nao tem WhatsApp nao tem contato.
CREATE TABLE contato (
    id_caso             NUMBER(8)     NOT NULL,
    tipo_whatsapp       VARCHAR2(25)  NOT NULL,
    nome_contato        VARCHAR2(60),
    numero_whatsapp     VARCHAR2(15)  NOT NULL,
    aceita_lembrete     CHAR(1)       NOT NULL,
    formato_lembrete    VARCHAR2(15),
    CONSTRAINT pk_contato PRIMARY KEY (id_caso),
    CONSTRAINT fk_contato_caso FOREIGN KEY (id_caso)
        REFERENCES caso (id_caso)
);

-- Associativa Caso x Documento: tem / nao tem / nao sabe.
CREATE TABLE documento_caso (
    id_caso             NUMBER(8)     NOT NULL,
    tipo_documento      VARCHAR2(40)  NOT NULL,
    situacao_documento  VARCHAR2(10)  NOT NULL,
    CONSTRAINT pk_documento_caso PRIMARY KEY (id_caso, tipo_documento),
    CONSTRAINT fk_doccaso_caso FOREIGN KEY (id_caso)
        REFERENCES caso (id_caso),
    CONSTRAINT fk_doccaso_documento FOREIGN KEY (tipo_documento)
        REFERENCES documento (tipo_documento)
);

-- Associativa Caso x Programa: o direito sugerido e a situacao marcada pelo agente.
CREATE TABLE item_plano (
    id_caso             NUMBER(8)     NOT NULL,
    id_programa         NUMBER(2)     NOT NULL,
    situacao            VARCHAR2(30)  NOT NULL,
    data_geracao        DATE          NOT NULL,
    CONSTRAINT pk_item_plano PRIMARY KEY (id_caso, id_programa),
    CONSTRAINT fk_item_caso FOREIGN KEY (id_caso)
        REFERENCES caso (id_caso),
    CONSTRAINT fk_item_programa FOREIGN KEY (id_programa)
        REFERENCES programa (id_programa)
);

CREATE TABLE encaminhamento (
    id_encaminhamento   NUMBER(8)     NOT NULL,
    id_caso             NUMBER(8)     NOT NULL,
    id_programa         NUMBER(2)     NOT NULL,
    id_equipamento      NUMBER(6),
    tipo_destino        VARCHAR2(20)  NOT NULL,
    data_hora           DATE          NOT NULL,
    forma_agendamento   VARCHAR2(20),
    resultado           VARCHAR2(20)  NOT NULL,
    id_profissional     NUMBER(8)     NOT NULL,
    CONSTRAINT pk_encaminhamento PRIMARY KEY (id_encaminhamento),
    CONSTRAINT fk_enc_item FOREIGN KEY (id_caso, id_programa)
        REFERENCES item_plano (id_caso, id_programa),
    CONSTRAINT fk_enc_destino FOREIGN KEY (id_equipamento)
        REFERENCES equipamento (id_equipamento),
    CONSTRAINT fk_enc_profissional FOREIGN KEY (id_profissional)
        REFERENCES profissional (id_profissional)
);

CREATE TABLE lembrete (
    id_encaminhamento   NUMBER(8)     NOT NULL,
    momento_envio       VARCHAR2(20)  NOT NULL,
    id_caso_contato     NUMBER(8)     NOT NULL,
    formato             VARCHAR2(15)  NOT NULL,
    status_envio        VARCHAR2(15)  NOT NULL,
    CONSTRAINT pk_lembrete PRIMARY KEY (id_encaminhamento, momento_envio),
    CONSTRAINT fk_lembrete_enc FOREIGN KEY (id_encaminhamento)
        REFERENCES encaminhamento (id_encaminhamento),
    CONSTRAINT fk_lembrete_contato FOREIGN KEY (id_caso_contato)
        REFERENCES contato (id_caso)
);

CREATE TABLE marcacao (
    id_marcacao         NUMBER(10)    NOT NULL,
    id_caso             NUMBER(8)     NOT NULL,
    id_profissional     NUMBER(8)     NOT NULL,
    texto_marcacao      VARCHAR2(100) NOT NULL,
    origem_marcacao     VARCHAR2(10)  NOT NULL,
    data_marcacao       DATE          NOT NULL,
    CONSTRAINT pk_marcacao PRIMARY KEY (id_marcacao),
    CONSTRAINT fk_marcacao_caso FOREIGN KEY (id_caso)
        REFERENCES caso (id_caso),
    CONSTRAINT fk_marcacao_profissional FOREIGN KEY (id_profissional)
        REFERENCES profissional (id_profissional)
);

CREATE TABLE campanha (
    id_campanha         NUMBER(6)     NOT NULL,
    acao                VARCHAR2(200) NOT NULL,
    data_hora           DATE,
    prioridade          VARCHAR2(10)  NOT NULL,
    motivo              VARCHAR2(300),
    cod_distrito        NUMBER(3)     NOT NULL,
    id_programa         NUMBER(2),
    id_equipamento      NUMBER(6),
    CONSTRAINT pk_campanha PRIMARY KEY (id_campanha),
    CONSTRAINT fk_campanha_distrito FOREIGN KEY (cod_distrito)
        REFERENCES distrito (cod_distrito),
    CONSTRAINT fk_campanha_programa FOREIGN KEY (id_programa)
        REFERENCES programa (id_programa),
    CONSTRAINT fk_campanha_local FOREIGN KEY (id_equipamento)
        REFERENCES equipamento (id_equipamento)
);

-- Associativa Caso x Campanha.
CREATE TABLE indicacao (
    id_campanha         NUMBER(6)     NOT NULL,
    id_caso             NUMBER(8)     NOT NULL,
    id_profissional     NUMBER(8)     NOT NULL,
    data_indicacao      DATE          NOT NULL,
    confirmada          CHAR(1)       NOT NULL,
    CONSTRAINT pk_indicacao PRIMARY KEY (id_campanha, id_caso),
    CONSTRAINT fk_indicacao_campanha FOREIGN KEY (id_campanha)
        REFERENCES campanha (id_campanha),
    CONSTRAINT fk_indicacao_caso FOREIGN KEY (id_caso)
        REFERENCES caso (id_caso),
    CONSTRAINT fk_indicacao_profissional FOREIGN KEY (id_profissional)
        REFERENCES profissional (id_profissional)
);
