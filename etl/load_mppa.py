"""Carrega os dados do Ministério Público do Estado do Pará (MPPA) extraídos do
Relatório de Atividades 2023/2024 (submetido à ALEPA) para as tabelas mppa_*.

Duas fontes, tratadas de forma bem diferente:

1. "ALEPA - 2023 e 2024 - Atividades e Planos.pdf" é um infográfico (slide deck):
   números e listas de municípios em blocos gráficos, sem estrutura tabular
   extraível de forma genérica. Os fatos foram conferidos manualmente contra o
   PDF e estão transcritos em lib/mppa_data.py (mesma estratégia de "casos
   especiais" que lib/pdf_parser.py já usa para os boletins do TSE).

2. "Relatorio ALEPA - ano base 2023 DEFINITIVO. Artes Graficas.pdf" é o relatório
   narrativo (texto corrido) com as "Ações Finalísticas" por área de atuação
   (seções 3.1 a 3.11). Este sim é extraído de forma programática: cada área vira
   um grupo de "ações" (parágrafos/itens de bullet), e cada ação é vasculhada em
   busca de nomes de municípios paraenses citados no texto, para permitir montar
   a lista "Ações do MP no seu município" no perfil de cada município.
"""
import os
import re
import subprocess
import tempfile

from lib.mppa_data import INDICADORES_ESTADO, MUNICIPIOS_SEM_PROMOTORIA, MPPA_ALIAS_MUNICIPIO, OBRAS
from lib.normalize import normalize

SRC_DIR = "/sources/mppa"
RELATORIO_PDF = os.path.join(SRC_DIR, "Relatorio ALEPA - ano base 2023 DEFINITIVO. Artes Graficas.pdf")

ANO_RELATORIO = 2023

# Seções "3.N - ÁREA ..." do relatório narrativo, na ordem em que aparecem, com o
# título exato como impresso no corpo do documento (usado para localizar o início
# de cada seção via regex) e o rótulo amigável para exibir no site.
AREAS = [
    (r"3\.1\s*-\s*ÁREA AMBIENTAL", "Área Ambiental"),
    (r"3\.2\s*-\s*ÁREA CÍVEL", "Área Cível, Processual e do Cidadão"),
    (r"3\.3\s*-\s*ÁREA CRIMINAL", "Área Criminal"),
    (r"3\.4\s*-\s*ÁREA INFÂNCIA E JUVENTUDE", "Área Infância e Juventude"),
    (r"3\.5\s*-\s*ÁREA DEFESA DO PATRIMÔNIO", "Área Defesa do Patrimônio Público e da Moralidade Administrativa"),
    (r"3\.6\s*-\s*ÁREA DIREITOS SOCIAIS", "Área Direitos Sociais"),
    (r"3\.7\s*-\s*ÁREA DIREITOS HUMANOS", "Área Direitos Humanos"),
    (r"3\.8\s*[-–]\s*AUTOCOMPOSIÇÃO", "Autocomposição"),
    (r"3\.9\s*[-–]\s*CORREGEDORIA-GERAL", "Corregedoria-Geral"),
    (r"3\.10\s*-\s*GRUPO DE ATUAÇÃO ESPECIALIZADA", "GAECO — Combate ao Crime Organizado"),
    (r"3\.11\s*[-–]\s*GRUPO DE ATUAÇÃO ESPECIAL", "Inteligência e Segurança Institucional"),
    (r"^\s*4\.\s*RELACIONAMENTO COM A SOCIEDADE", None),  # marca o fim da seção 3
]

HEADER_RE = re.compile(r"^PROCURADORIA GERAL DE JUSTIÇA$")
PAGE_NUM_RE = re.compile(r"^\d{1,4}$")
MIN_ACAO_LEN = 40


def _extract_text(pdf_path: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", pdf_path, tmp_path],
            check=True, capture_output=True,
        )
        with open(tmp_path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


BODY_START_MARKER_RE = re.compile(r"MENSAGEM DA PROCURADORIA-GERAL DE JUSTIÇA")


def _find_area_bounds(lines: list[str]) -> list[tuple[str, int, int]]:
    """Localiza, em número de linha, o início/fim de cada área da seção 3.
    A busca começa depois do sumário (âncora: título da mensagem de abertura,
    que só aparece no corpo do texto), para nunca casar com uma entrada do
    sumário em vez do título real da seção."""
    body_start = 0
    for i, line in enumerate(lines):
        if BODY_START_MARKER_RE.search(line):
            body_start = i
            break

    positions = []
    for pattern, label in AREAS:
        rx = re.compile(pattern)
        found = None
        for i in range(body_start, len(lines)):
            if rx.search(lines[i]):
                found = i
                break
        positions.append((label, found))

    bounds = []
    for idx in range(len(positions) - 1):
        label, start = positions[idx]
        _, end = positions[idx + 1]
        if label is None or start is None:
            continue
        end = end if end is not None else len(lines)
        bounds.append((label, start + 1, end))
    return bounds


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _filter_noise(lines_slice: list[str]) -> list[str]:
    out = []
    for l in lines_slice:
        s = l.strip()
        if not s:
            continue
        if HEADER_RE.match(s) or PAGE_NUM_RE.match(s):
            continue
        out.append(l)
    return out


def _segment_paragraphs(lines_slice: list[str]) -> list[str]:
    """Reconstrói parágrafos/itens: cada bullet '•' ou linha com indentação de
    início de parágrafo (>=4 espaços) inicia uma nova 'ação'; as demais linhas são
    continuação (quebra de linha do PDF)."""
    segments = []
    current = []
    for l in lines_slice:
        starts_new = l.lstrip().startswith("•") or _leading_spaces(l) >= 4
        piece = l.strip().lstrip("•").strip()
        if not piece:
            continue
        if starts_new and current:
            segments.append(" ".join(current))
            current = [piece]
        else:
            current.append(piece)
    if current:
        segments.append(" ".join(current))
    return segments


def _build_municipio_lookup(conn) -> dict:
    cur = conn.cursor()
    cur.execute("SELECT ibge_code, nome, nome_normalizado FROM municipios")
    by_norm = {}
    for ibge_code, nome, nome_normalizado in cur.fetchall():
        by_norm[nome_normalizado] = (ibge_code, nome)
    return by_norm


def _resolve_municipio(nome: str, by_norm: dict):
    norm = normalize(nome)
    norm = MPPA_ALIAS_MUNICIPIO.get(norm, norm)
    return by_norm.get(norm)


def _find_municipios_in_text(texto: str, norms_sorted: list[str], by_norm: dict) -> list[tuple[str, str]]:
    norm_texto = " " + normalize(texto) + " "
    found = []
    for norm in norms_sorted:
        if (" " + norm + " ") in norm_texto:
            found.append(by_norm[norm])
    return found


def _load_indicadores_estado(cur):
    for categoria, indicador, ano, valor, unidade in INDICADORES_ESTADO:
        cur.execute(
            """
            INSERT INTO mppa_indicadores (municipio_id, escopo, categoria, indicador, ano, valor, unidade)
            VALUES (NULL, 'ESTADO', %s, %s, %s, %s, %s)
            """,
            (categoria, indicador, ano, valor, unidade),
        )
    return len(INDICADORES_ESTADO)


def _load_promotoria_status(cur, by_norm):
    sem_promotoria_norm = {normalize(n) for n in MUNICIPIOS_SEM_PROMOTORIA}
    total = 0
    nao_casados = []
    for nome_norm in sem_promotoria_norm:
        if nome_norm not in by_norm:
            nao_casados.append(nome_norm)

    for nome_norm, (ibge_code, nome) in by_norm.items():
        instalada = 0 if nome_norm in sem_promotoria_norm else 1
        cur.execute(
            """
            INSERT INTO mppa_indicadores (municipio_id, escopo, categoria, indicador, ano, valor, unidade)
            VALUES (%s, 'MUNICIPIO', 'Estrutura Física', 'Promotoria de Justiça instalada', %s, %s, NULL)
            """,
            (ibge_code, 2024, instalada),
        )
        total += 1

    if nao_casados:
        print(f"[mppa] aviso: municípios 'sem promotoria' não encontrados na base: {nao_casados}")
    return total


def _load_obras(cur, by_norm):
    total = 0
    nao_casados = []
    for tipo, ano, municipios in OBRAS:
        for nome in municipios:
            match = _resolve_municipio(nome, by_norm)
            if not match:
                nao_casados.append(nome)
                continue
            ibge_code, nome_oficial = match
            titulo = f"Distrito de {nome}" if normalize(nome) == "MOSQUEIRO" else None
            cur.execute(
                """
                INSERT INTO mppa_obras (municipio_id, tipo, titulo, ano)
                VALUES (%s, %s, %s, %s)
                """,
                (ibge_code, tipo, titulo, ano),
            )
            total += 1

    if nao_casados:
        print(f"[mppa] aviso: municípios de obras não encontrados na base: {nao_casados}")
    return total


def _load_acoes_narrativas(cur, by_norm):
    if not os.path.isfile(RELATORIO_PDF):
        print("[mppa] relatório narrativo não encontrado, pulando extração de ações.")
        return 0, 0

    text = _extract_text(RELATORIO_PDF)
    lines = text.split("\n")
    bounds = _find_area_bounds(lines)

    norms_sorted = sorted((n for n in by_norm if len(n) >= 4), key=len, reverse=True)

    total_acoes = 0
    total_com_municipio = 0

    for area_label, start, end in bounds:
        seg_lines = _filter_noise(lines[start:end])
        for texto in _segment_paragraphs(seg_lines):
            if len(texto) < MIN_ACAO_LEN:
                continue
            municipios = _find_municipios_in_text(texto, norms_sorted, by_norm)
            escopo = "MUNICIPIO" if municipios else "ESTADO"

            cur.execute(
                """
                INSERT INTO mppa_acoes (area, escopo, ano, resumo)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (area_label, escopo, ANO_RELATORIO, texto),
            )
            acao_id = cur.fetchone()[0]
            total_acoes += 1

            if municipios:
                total_com_municipio += 1
                vistos = set()
                for ibge_code, _nome in municipios:
                    if ibge_code in vistos:
                        continue
                    vistos.add(ibge_code)
                    cur.execute(
                        "INSERT INTO mppa_acoes_municipios (acao_id, municipio_id) VALUES (%s, %s)",
                        (acao_id, ibge_code),
                    )

    return total_acoes, total_com_municipio


def run(conn):
    cur = conn.cursor()

    cur.execute("DELETE FROM mppa_acoes_municipios")
    cur.execute("DELETE FROM mppa_acoes")
    cur.execute("DELETE FROM mppa_obras")
    cur.execute("DELETE FROM mppa_indicadores")

    by_norm = _build_municipio_lookup(conn)

    n_indicadores = _load_indicadores_estado(cur)
    n_promotoria = _load_promotoria_status(cur, by_norm)
    n_obras = _load_obras(cur, by_norm)
    n_acoes, n_acoes_municipio = _load_acoes_narrativas(cur, by_norm)

    conn.commit()
    print(
        f"[mppa] {n_indicadores} indicadores estaduais, {n_promotoria} municípios com status de promotoria, "
        f"{n_obras} obras/sedes, {n_acoes} ações extraídas do relatório ({n_acoes_municipio} vinculadas a município)."
    )
