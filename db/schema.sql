-- Anuário Estatístico do Pará - modelo de dados
-- Executado automaticamente pelo Postgres no primeiro start (docker-entrypoint-initdb.d)

CREATE TABLE IF NOT EXISTS municipios (
    ibge_code           varchar(7) PRIMARY KEY,
    nome                varchar(120) NOT NULL,
    nome_normalizado    varchar(120) NOT NULL UNIQUE,
    mesorregiao         varchar(120),
    microrregiao        varchar(120),
    regiao_imediata     varchar(120),
    regiao_intermediaria varchar(120),
    regiao_integracao   varchar(120),
    tse_codigo          varchar(6)
);
CREATE INDEX IF NOT EXISTS idx_municipios_nome_normalizado ON municipios(nome_normalizado);

CREATE TABLE IF NOT EXISTS indicadores (
    id          bigserial PRIMARY KEY,
    municipio_id varchar(7) REFERENCES municipios(ibge_code) ON DELETE CASCADE,
    escopo      varchar(20) NOT NULL DEFAULT 'MUNICIPIO', -- MUNICIPIO | ESTADO
    tematica    varchar(60) NOT NULL,
    subtema     varchar(150),
    indicador   text NOT NULL,
    categoria   varchar(150),
    ano         integer,
    valor       numeric
);
CREATE INDEX IF NOT EXISTS idx_indicadores_municipio ON indicadores(municipio_id);
CREATE INDEX IF NOT EXISTS idx_indicadores_tematica ON indicadores(tematica);
CREATE INDEX IF NOT EXISTS idx_indicadores_escopo ON indicadores(escopo);
CREATE INDEX IF NOT EXISTS idx_indicadores_ano ON indicadores(ano);
CREATE INDEX IF NOT EXISTS idx_indicadores_grupo ON indicadores(municipio_id, tematica, subtema, indicador);

CREATE TABLE IF NOT EXISTS partidos (
    numero  smallint PRIMARY KEY,
    sigla   varchar(20) NOT NULL,
    nome    varchar(150)
);

CREATE TABLE IF NOT EXISTS candidatos (
    id               bigserial PRIMARY KEY,
    municipio_id     varchar(7) NOT NULL REFERENCES municipios(ibge_code) ON DELETE CASCADE,
    ano_eleicao      integer NOT NULL,
    turno            smallint NOT NULL,
    cargo            varchar(20) NOT NULL, -- PREFEITO | VICE_PREFEITO | VEREADOR
    numero_candidato integer,
    nome             varchar(300) NOT NULL,
    partido_numero   smallint REFERENCES partidos(numero),
    votos            integer,
    percentual       numeric(6,2),
    situacao         varchar(60),
    ordem_suplencia  integer,
    titular_id       bigint REFERENCES candidatos(id)
);
CREATE INDEX IF NOT EXISTS idx_candidatos_municipio ON candidatos(municipio_id, cargo);
CREATE INDEX IF NOT EXISTS idx_candidatos_situacao ON candidatos(situacao);

CREATE TABLE IF NOT EXISTS mapas_tematicos (
    id        serial PRIMARY KEY,
    categoria varchar(60) NOT NULL,
    titulo    varchar(200) NOT NULL,
    arquivo   varchar(300) NOT NULL,
    ano       varchar(10)
);
CREATE INDEX IF NOT EXISTS idx_mapas_categoria ON mapas_tematicos(categoria);

-- Ministério Público do Estado do Pará (MPPA) - Relatório de Atividades 2023/2024
CREATE TABLE IF NOT EXISTS mppa_indicadores (
    id           bigserial PRIMARY KEY,
    municipio_id varchar(7) REFERENCES municipios(ibge_code) ON DELETE CASCADE,
    escopo       varchar(20) NOT NULL DEFAULT 'ESTADO', -- MUNICIPIO | ESTADO
    categoria    varchar(120) NOT NULL,
    indicador    text NOT NULL,
    ano          integer,
    valor        numeric,
    unidade      varchar(30)
);
CREATE INDEX IF NOT EXISTS idx_mppa_indicadores_municipio ON mppa_indicadores(municipio_id);
CREATE INDEX IF NOT EXISTS idx_mppa_indicadores_escopo ON mppa_indicadores(escopo, categoria);

CREATE TABLE IF NOT EXISTS mppa_obras (
    id           bigserial PRIMARY KEY,
    municipio_id varchar(7) NOT NULL REFERENCES municipios(ibge_code) ON DELETE CASCADE,
    tipo         varchar(80) NOT NULL,
    titulo       varchar(200),
    ano          integer NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mppa_obras_municipio ON mppa_obras(municipio_id);

CREATE TABLE IF NOT EXISTS mppa_acoes (
    id     bigserial PRIMARY KEY,
    area   varchar(120) NOT NULL,
    escopo varchar(20) NOT NULL DEFAULT 'ESTADO', -- MUNICIPIO | ESTADO
    ano    integer,
    resumo text NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mppa_acoes_area ON mppa_acoes(area);

CREATE TABLE IF NOT EXISTS mppa_acoes_municipios (
    acao_id      bigint NOT NULL REFERENCES mppa_acoes(id) ON DELETE CASCADE,
    municipio_id varchar(7) NOT NULL REFERENCES municipios(ibge_code) ON DELETE CASCADE,
    PRIMARY KEY (acao_id, municipio_id)
);
CREATE INDEX IF NOT EXISTS idx_mppa_acoes_municipios_municipio ON mppa_acoes_municipios(municipio_id);

CREATE TABLE IF NOT EXISTS mppa_contatos (
    id           bigserial PRIMARY KEY,
    municipio_id varchar(7) NOT NULL UNIQUE REFERENCES municipios(ibge_code) ON DELETE CASCADE,
    entrancia    varchar(40),
    endereco     text,
    telefones    text
);
