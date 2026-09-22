# Anuário Estatístico e Político do Pará

Sistema web **100% Docker** para consulta de dados demográficos, econômicos,
sociais, territoriais e políticos dos **144 municípios do Pará**, com mapa
interativo, perfil analítico completo por município e exportação em PDF.

Stack: **PHP 8.2 (Apache) + AdminLTE 3** no front-end, **PostgreSQL 16** como
banco de dados, e um pipeline **ETL em Python** que carrega tudo
automaticamente na primeira subida — não é necessário nenhum passo manual de
importação de dados.

---

## Índice

1. [Visão geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Fontes de dados](#fontes-de-dados)
4. [Arquitetura](#arquitetura)
5. [Estrutura do projeto](#estrutura-do-projeto)
6. [Modelo de dados (PostgreSQL)](#modelo-de-dados-postgresql)
7. [Pipeline de ETL — como cada fonte é processada](#pipeline-de-etl--como-cada-fonte-é-processada)
8. [Como executar](#como-executar)
9. [Configuração (`.env`)](#configuração-env)
10. [Rotas da aplicação web](#rotas-da-aplicação-web)
11. [Limitações e ressalvas sobre os dados](#limitações-e-ressalvas-sobre-os-dados)
12. [Manutenção e recarga de dados](#manutenção-e-recarga-de-dados)
13. [Solução de problemas](#solução-de-problemas)
14. [Créditos e fontes oficiais](#créditos-e-fontes-oficiais)

---

## Visão geral

O usuário escolhe um município do Pará — pelo **mapa interativo** (SVG/Leaflet
com a malha oficial do IBGE) ou pela **busca por nome** — e é levado a uma
página analítica dedicada com:

- Indicadores históricos de **Demografia, Economia, Social, Território, Meio
  Ambiente e Infraestrutura**, organizados por tema e com gráficos de série
  temporal;
- Uma aba **Política** com o(a) prefeito(a) e vice eleitos, todos os
  candidatos ao cargo majoritário, e a lista completa de vereadores(as)
  eleitos(as), suplentes e não eleitos, com partido e votação — dados das
  **Eleições Municipais 2024**;
- Um botão para **exportar o perfil completo em PDF**.

A página inicial mostra um painel do Estado (KPIs agregados, gráfico da
população do Pará, galeria de mapas temáticos oficiais) além do mapa e da
busca.

Todo o banco de dados já vem **populado desde o primeiro `docker compose up`**
— o objetivo do projeto era ter uma base organizada e relacionada (município ↔
indicadores ↔ candidatos) pronta para uso, sem etapas manuais de importação.

## Funcionalidades

- [x] Mapa interativo do Pará (144 municípios clicáveis, com tooltip do nome)
- [x] Busca de município por nome
- [x] Painel do Estado com KPIs (população, PIB, PIB per capita, nº de municípios)
- [x] Perfil do município com abas por tema e gráficos históricos (Chart.js)
- [x] Aba Política: prefeito/vice eleitos, candidatos a prefeito, vereadores
      eleitos/suplentes/não eleitos, com partido e votação
- [x] Exportação do perfil do município em PDF (dompdf)
- [x] Galeria de mapas temáticos oficiais do Estado, por categoria
- [x] Carga de dados 100% automática no primeiro `docker compose up`
- [x] Pipeline idempotente (pode ser re-executado a qualquer momento sem duplicar dados)

## Fontes de dados

| Fonte | Conteúdo | Onde entra no sistema |
|---|---|---|
| `Anuário_2025/Anuário_2025.csv.gz` (IDESP/SEPLAD) | ~930 mil linhas: indicador × categoria × ano × município (ou Estado), nos temas Demografia, Economia, Social, Território, Meio Ambiente e Infraestrutura. Versão comprimida (~8MB) do CSV original (134MB) para caber nos limites do GitHub — o ETL lê o `.gz` diretamente | tabela `indicadores` |
| `Relatorio_Resultado_Totalizacao_2024_PA/*.pdf` (Justiça Eleitoral/TSE) | 148 boletins oficiais de totalização das Eleições Municipais 2024 (um por município, + 2 boletins de 2º turno) | tabela `candidatos` (via parser próprio, ver [seção de ETL](#pipeline-de-etl--como-cada-fonte-é-processada)) |
| `mapas/<categoria>/*.jpg\|png` | Mapas temáticos estáticos do Estado, organizados por categoria (demografia, economia, social, território, meio ambiente, infraestrutura) | tabela `mapas_tematicos` + galeria da página inicial |
| API do IBGE (`servicodados.ibge.gov.br`) | Lista oficial dos 144 municípios do Pará (nome, mesorregião, microrregião, região imediata/intermediária) e a malha geográfica (GeoJSON) dos seus limites | tabela `municipios` + `app/public/assets/geo/pa_municipios.geojson` (mapa interativo) |

> **Telefone e endereço de candidatos e políticos não existem em nenhuma
> fonte oficial** — a Justiça Eleitoral não publica esse dado (é informação
> pessoal protegida) e, por isso, **não fazem parte do modelo de dados**. O
> que existe publicamente sobre cada candidato é: nome, nome de urna, número,
> partido, cargo, votação e situação de totalização — é exatamente isso que o
> sistema armazena.

## Arquitetura

```
┌─────────────┐      ┌──────────────────────────┐      ┌─────────────────┐
│   Fontes    │      │      docker compose       │      │                 │
│  de dados   │      │                            │      │    Navegador    │
│ (pasta raiz)│      │  ┌──────┐   ┌───────────┐  │      │                 │
│             │─────▶│  │ etl  │──▶│    db     │◀─┼──────┤  AdminLTE 3 +   │
│ Anuário CSV │      │  │(py)  │   │(postgres) │  │      │  Leaflet.js +   │
│ PDFs TSE    │      │  └──────┘   └───────────┘  │      │  Chart.js       │
│ mapas/*.jpg │      │      (roda 1x, idempotente) │      │                 │
│ API IBGE    │      │                    ▲        │      └────────▲────────┘
└─────────────┘      │                    │        │               │
                      │              ┌─────┴─────┐  │      HTTP :8095
                      │              │    web    │──┼───────────────┘
                      │              │(php+apache)│  │
                      │              └───────────┘  │
                      └──────────────────────────────┘
```

- O serviço **`etl`** roda **uma única vez**, antes do `web` subir
  (`depends_on: condition: service_completed_successfully`), lê as fontes
  brutas montadas como volumes somente-leitura e grava tudo no Postgres.
- O serviço **`web`** só serve a aplicação PHP — nunca acessa arquivos brutos
  diretamente, apenas o banco (e os mapas estáticos, já copiados para um
  volume compartilhado pelo `etl`).
- Não há build step de front-end (webpack/vite/npm): AdminLTE, Bootstrap,
  Leaflet e Chart.js são carregados via CDN (cdnjs.cloudflare.com) direto no
  `<head>` das páginas.

## Estrutura do projeto

```
mapagsi/
├── docker-compose.yml        # orquestração dos 3 serviços (db, etl, web)
├── .env                       # variáveis de ambiente (usuário/senha do banco, porta)
├── .dockerignore               # exclui as pastas de dados brutos do build context
├── db/
│   └── schema.sql              # DDL completo, aplicado automaticamente pelo Postgres
├── etl/
│   ├── Dockerfile
│   ├── requirements.txt        # psycopg2-binary, PyMuPDF
│   ├── run_all.py               # orquestrador: chama os 4 loaders em ordem
│   ├── load_municipios.py       # carrega os 144 municípios (IBGE) + região de integração
│   ├── load_anuario.py          # carrega os ~930 mil indicadores do Anuário_2025.csv
│   ├── load_mapas.py            # cataloga os mapas temáticos estáticos
│   ├── load_politicos.py        # orquestra a extração de candidatos dos 148 PDFs
│   └── lib/
│       ├── db.py                 # conexão psycopg2 com retry
│       ├── normalize.py          # normalização de nomes de município (acento/caixa/alias)
│       ├── partidos.py           # tabela nacional nº→sigla/nome de partido (fallback)
│       └── pdf_parser.py         # parser dos boletins de totalização do TSE (núcleo do ETL político)
├── app/
│   ├── Dockerfile
│   ├── composer.json            # dompdf/dompdf (exportação em PDF)
│   ├── public/
│   │   ├── index.php             # front controller / roteador por query string
│   │   └── assets/
│   │       ├── css/custom.css
│   │       ├── js/home.js         # mapa Leaflet + busca + gráfico da população
│   │       ├── geo/pa_municipios.geojson  # malha do IBGE (copiada no build)
│   │       └── mapas/…            # mapas temáticos (copiados pelo etl via volume)
│   ├── src/
│   │   ├── Database.php          # PDO singleton
│   │   └── Repository/
│   │       ├── MunicipioRepository.php
│   │       ├── IndicadorRepository.php
│   │       ├── CandidatoRepository.php
│   │       └── MapaRepository.php
│   └── views/
│       ├── partials/header.php    # layout AdminLTE (navbar + sidebar + CDNs)
│       ├── partials/footer.php
│       ├── home.php               # painel do Estado (mapa + KPIs + busca + galeria)
│       ├── municipio.php          # perfil do município (abas + Política)
│       └── municipio_pdf.php      # template para exportação em PDF (dompdf)
├── data/geo/                    # snapshot local do IBGE (municípios + geojson) usado no build
├── Anuário_2025/                 # fonte bruta (montada só-leitura no etl)
├── Relatorio_Resultado_Totalizacao_2024_PA/  # fonte bruta (148 PDFs do TSE)
└── mapas/                        # fonte bruta (mapas temáticos estáticos)
```

## Modelo de dados (PostgreSQL)

```
municipios                    partidos
├── ibge_code (PK)            ├── numero (PK)
├── nome                      ├── sigla
├── nome_normalizado          └── nome
├── mesorregiao
├── microrregiao                candidatos
├── regiao_imediata           ├── id (PK)
├── regiao_intermediaria      ├── municipio_id  (FK → municipios)
└── regiao_integracao         ├── ano_eleicao, turno
                               ├── cargo  (PREFEITO | VICE_PREFEITO | VEREADOR)
indicadores                   ├── numero_candidato, nome
├── id (PK)                   ├── partido_numero (FK → partidos)
├── municipio_id (FK, null    ├── votos, percentual
│   se escopo = ESTADO)       ├── situacao  ("Eleito", "Eleito por QP",
├── escopo (MUNICIPIO|ESTADO) │            "Eleito por média", "N Suplente",
├── tematica, subtema         │            "Não eleito", "Anulado…" etc.)
├── indicador, categoria      ├── ordem_suplencia
├── ano, valor                └── titular_id (FK → candidatos; liga vice ao titular)

mapas_tematicos
├── id (PK)
├── categoria, titulo, arquivo, ano
```

Pontos de design que valem explicação:

- **`indicadores` é genérica** (tema/subtema/indicador/categoria/ano/valor) em
  vez de ter uma coluna por indicador. Isso permite carregar **todos** os ~930
  mil pontos do Anuário sem precisar mapear cada indicador manualmente, e o
  app agrupa dinamicamente para montar os gráficos.
- **`escopo`** distingue linhas por município das linhas agregadas do Estado
  (usadas nos KPIs da página inicial).
- **`candidatos`** guarda **todos** os candidatos (eleitos, suplentes, não
  eleitos) de prefeito/vice/vereador — não só quem venceu — para permitir a
  tabela completa na aba Política.
- **`titular_id`** liga o registro do(a) vice-prefeito(a) ao seu titular,
  já que o vice não tem número de urna nem votação próprios no boletim.

## Pipeline de ETL — como cada fonte é processada

Executado por `etl/run_all.py`, em ordem, cada etapa é **idempotente**
(faz `DELETE`/recria antes de inserir, então pode ser rodada de novo a
qualquer momento sem duplicar nada):

### 1. `load_municipios.py`
Lê `data/geo/pa_municipios_ibge.json` (snapshot da API do IBGE,
`/localidades/estados/PA/municipios`) para os 144 municípios oficiais, e
enriquece cada um com a **Região de Integração** declarada no Anuário_2025
(coluna `ri` do CSV), casando os nomes por uma função de normalização
(maiúsculas, sem acento, sem hífen).

### 2. `load_anuario.py`
Processa o CSV de ~930 mil linhas com `COPY` em lotes de 50 mil (muito mais
rápido que `INSERT` linha a linha). Para cada linha:
- resolve `localidade` → `municipio_id` via nome normalizado (com uma lista
  de alias para as poucas divergências reais entre TSE/Anuário/IBGE — ex.:
  *"Eldorado dos Carajás"* no TSE vs. *"Eldorado do Carajás"* no IBGE);
- linhas cuja `localidade` é o total "Pará" viram `escopo='ESTADO'`;
- linhas que não casam com nenhum município real (ex.: subdistritos como
  *Outeiro*, *Vila do Conde*, ou a linha `Jacareacanga (*)` com nota de
  rodapé) são descartadas — são ~700 de 930 mil linhas.

### 3. `load_mapas.py`
Varre `mapas/<categoria>/*.jpg|png`, copia cada arquivo para o volume
compartilhado com o `web` (`/output/mapas`) e registra categoria/título/ano
(extraídos do próprio nome do arquivo) em `mapas_tematicos`.

### 4. `load_politicos.py` + `lib/pdf_parser.py` (a parte mais complexa)

Não existe, em nenhuma fonte disponível, um CSV pronto de candidatos das
**Eleições Municipais 2024** — só os 148 boletins em PDF (um por município,
gerados pelo sistema SISTOT da Justiça Eleitoral), cada um com ~15–40
páginas de texto semi-estruturado. O parser (`pdf_parser.py`) funciona assim:

1. Extrai o texto de cada página com PyMuPDF e remove o cabeçalho/rodapé que
   se repete em toda página (`Justiça Eleitoral/PA`, `SISTOT — …`, data/hora
   de geração, título do anexo repetido no topo de cada página).
2. Localiza, por regex sobre o título do anexo (que muda de número conforme o
   município tem ou não 2º turno), duas seções:
   - **"Anexo N — Resultado de votação"** (candidato a candidato, final, com
     a situação de totalização: `Eleito`, `Não eleito`, `Anulado sub
     judice`…) — usada para **Prefeito**;
   - **"Anexo N — Resultado de votação por partido/federação/coligação"** —
     mesmos dados de **Vereador**, mas agrupados por partido, o que permite
     descobrir a **sigla do partido de cada candidato** diretamente do
     boletim (sem depender de uma tabela de numeração fixa). Quando a
     candidatura está numa federação (heading sem número, ex. *"FEDERAÇÃO
     BRASIL DA ESPERANÇA"*), o partido é derivado dos 2 primeiros dígitos do
     número de urna (convenção nacional do TSE), com a tabela estática de
     `lib/partidos.py` como último fallback.
3. Um pequeno autômato de estados percorre as linhas já limpas reconhecendo,
   por padrão (não por posição fixa na página, já que nomes longos quebram em
   várias linhas): número de votos → situação → "número — nome" do
   candidato → validade do voto → (só para Prefeito) nome do vice.
4. **Casos especiais tratados** (descobertos e validados durante o
   desenvolvimento, comparando com o resultado real das eleições):
   - **Belém e Santarém** tiveram 2º turno: existe um PDF `_T1` (1º turno,
     com os vereadores — decididos em turno único) e um `_T2` (2º turno,
     só com o resultado final de prefeito). O sistema usa o **vereador do
     T1** e o **prefeito do T2**.
   - **Melgaço** teve a eleição de vereador anulada e refeita numa **eleição
     suplementar** em 2026 (PDF à parte, sem seção de Prefeito). O sistema
     detecta que o PDF original tem 0 vereadores eleitos, usa o da eleição
     suplementar para vereador e mantém o prefeito do PDF original.
   - **Tucuruí**: o candidato mais votado teve o registro anulado *sub
     judice*, e a própria Justiça Eleitoral declara no boletim que não há
     "prefeito eleito" definido. O sistema reflete isso literalmente (todos
     os candidatos aparecem com sua situação real, e a página do município
     mostra um aviso em vez de destacar um vencedor inexistente) em vez de
     inventar um resultado.
   - A regra geral usada para esses casos é: **para cada cargo (prefeito /
     vereador), escolher entre os PDFs do mesmo município aquele que tem
     algum candidato "Eleito"; em caso de empate, o de geração mais
     recente; na ausência de qualquer eleito confirmado, usar o único
     disponível** (`pick_best()` em `load_politicos.py`).

Todo o pipeline foi validado comparando os dados extraídos com os resultados
reais publicamente conhecidos das eleições de 2024 em Belém e Soure.

## Como executar

**Pré-requisitos:** Docker + Docker Compose (no macOS, o
[Colima](https://github.com/abiosoft/colima) funciona como alternativa ao
Docker Desktop: `colima start`). Nenhuma outra dependência é necessária —
PHP, PostgreSQL e Python rodam só dentro dos containers.

```bash
git clone https://github.com/jorgyvanlima/anuariogsi.git
cd anuariogsi
cp .env.example .env
docker compose up -d --build
```

Na primeira subida, o serviço `etl` roda uma única vez (carrega ~930 mil
indicadores, os 144 municípios, os mapas temáticos e ~17 mil candidatos) antes
do `web` iniciar — leva menos de um minuto. Acompanhe com:

```bash
docker compose logs -f etl
```

Quando o `web` estiver de pé, acesse:

```
http://localhost:8095
```

(porta definida em `APP_PORT` no `.env` — mude se `8095` já estiver em uso).

Para derrubar tudo (mantendo os dados no volume):

```bash
docker compose down
```

Para apagar também os dados e recomeçar do zero:

```bash
docker compose down -v
docker compose up -d --build
```

## Configuração (`.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `POSTGRES_DB` | `anuario_pa` | Nome do banco |
| `POSTGRES_USER` | `anuario` | Usuário do Postgres |
| `POSTGRES_PASSWORD` | `anuario_pa_2025` | Senha do Postgres |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `db` / `5432` | Usados internamente pelos containers `etl` e `web` |
| `APP_PORT` | `8095` | Porta no host mapeada para o container `web` (porta 80) |

## Rotas da aplicação web

Roteamento simples por query string (sem framework), em `app/public/index.php`:

| Rota | Descrição |
|---|---|
| `/` ou `/index.php?page=home` | Painel do Estado: KPIs, mapa interativo, busca, galeria de mapas temáticos |
| `/index.php?page=municipio&codigo={ibge_code}` | Perfil completo do município (abas por tema + Política) |
| `/index.php?page=municipio&codigo={ibge_code}&export=pdf` | Exporta o mesmo perfil em PDF (`Content-Type: application/pdf`) |

## Limitações e ressalvas sobre os dados

- **Telefone e endereço de candidatos não existem** em nenhuma fonte oficial
  e não estão no modelo de dados (ver aviso na seção de fontes).
- **Tucuruí**: na fonte oficial disponível, o resultado da eleição para
  prefeito está *sub judice* (sem vencedor confirmado) — o sistema exibe essa
  situação de forma explícita em vez de presumir um resultado.
- Os **mapas temáticos** da galeria são imagens estáticas do Estado (não são
  recortáveis por município nem interativos) — o mapa clicável da página
  inicial é a malha vetorial do IBGE, renderizada com Leaflet.
- O Anuário_2025 tem algumas linhas (~700 de 930 mil) referentes a
  subdistritos ou notas de rodapé que não correspondem a um município oficial
  e são descartadas na carga (ver [`load_anuario.py`](etl/load_anuario.py)).

## Manutenção e recarga de dados

O pipeline é idempotente — pode ser executado novamente a qualquer momento
(por exemplo, após atualizar o `Anuário_2025.csv` ou adicionar um PDF de
totalização) sem duplicar registros, pois cada loader limpa sua(s) própria(s)
tabela(s) antes de inserir:

```bash
docker compose run --rm etl
```

Isso não afeta o container `web`, que continua servindo normalmente durante a
recarga (os dados só "trocam" no commit final de cada loader).

## Solução de problemas

**Porta já em uso ao subir o `web`:** mude `APP_PORT` no `.env` para uma porta
livre e rode `docker compose up -d web` novamente.

**`etl` roda de novo toda vez que dou `docker compose up`:** é esperado — como
o container do `etl` tem `restart: "no"` e o `web` depende dele via
`service_completed_successfully`, o Compose o reexecuta a cada `up`. Isso é
seguro (idempotente) e leva menos de um minuto; se quiser subir só o `web` sem
reprocessar nada, use `docker compose start web` (em vez de `up`) depois da
primeira carga.

**Quero ver os dados diretamente no banco:**

```bash
docker compose exec db psql -U anuario -d anuario_pa
```

## Créditos e fontes oficiais

- **Anuário Estatístico do Pará 2025** — IDESP/SEPLAD (Governo do Estado do Pará)
- **Eleições Municipais 2024** — Justiça Eleitoral / Tribunal Superior Eleitoral (TSE)
- **Malha municipal e lista de municípios** — IBGE (`servicodados.ibge.gov.br`)

Sistema de uso interno/analítico — não substitui as fontes oficiais para fins
legais, jurídicos ou eleitorais.
