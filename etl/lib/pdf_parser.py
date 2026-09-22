"""Extrai prefeito/vice-prefeito e vereadores eleitos, suplentes e não eleitos dos
Relatórios de Resultado da Totalização (PDF oficial da Justiça Eleitoral/TSE) das
Eleições Municipais 2024 do Pará.

Estratégia: os boletins têm um "Anexo N - Resultado de votação" (final, por
candidato) e um "Anexo N - Resultado de votação por partido/federação/coligação"
(mesmos dados, porém agrupados por partido -- usado para descobrir a sigla do
partido de cada candidato a vereador). Os números dos anexos variam conforme o
município (municípios com 2º turno têm menos anexos), por isso a localização é
feita por regex sobre o título do anexo, não por número fixo.
"""
import re
import unicodedata

import fitz

BOILERPLATE_EXACT = {
    "Oficial",
    "Votos computados",
    "Situação da totalização",
    "Destinação de votos",
    "Candidata ou candidato",
    "% Votos",
    " % Votos",
    "computados **",
    "Justiça Eleitoral",
}

BOILERPLATE_RE = re.compile(
    r"^(Justiça Eleitoral(/[A-Z]{2})?"
    r"|SISTOT - SISTEMA DE GERENCIAMENTO DA TOTALIZAÇÃO"
    r"|Eleições Municipais 2024.*"
    r"|Eleição Suplementar.*"
    r"|\d{2}/\d{2}/\d{4}"
    r"|\d{2}:\d{2}:\d{2}"
    r"|Relatório( do)? Resultado da Totalização"
    r"|Resumo Geral do Município de .+"
    r"|\d{1,2} de \w+ de \d{4}"
    r"|\d+º Turno"
    r"|Resultado em .+"
    r"|\*+Candidata.*"
    r"|\*+Percentual.*"
    r"|\*A origem da destinação.*"
    r")$"
)

RESULTADO_FINAL_RE = re.compile(r"^Anexo [IVXLC]+\s*-\s*Resultado de votação$")
RESULTADO_PARTIDO_RE = re.compile(r"^Anexo [IVXLC]+\s*-\s*Resultado de votação por partido")
ANEXO_ANY_RE = re.compile(r"^Anexo [IVXLC]+\b")

VOTE_RE = re.compile(r"^\d{1,3}(\.\d{3})*$")
PCT_RE = re.compile(r"^\d{1,3}[.,]\d{2}%$")
CAND_RE = re.compile(r"^(\*)?(\d{1,6})\s*-\s*(.+)$")
PARTY_HEADING_RE = re.compile(r"^(\d{1,3}) - ([A-ZÀ-Ü][A-ZÀ-Ü/.\s]*)$")
HEADER_CODE_RE = re.compile(r"(\d+)\s*-\s*(.+?)\s*-\s*PA")

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def clean_lines(text):
    lines = [l.strip() for l in text.split("\n")]
    out = []
    for l in lines:
        if not l:
            continue
        if l in BOILERPLATE_EXACT:
            continue
        if BOILERPLATE_RE.match(l):
            continue
        out.append(l)
    return out


def is_status_line(s):
    return any(c.islower() for c in s)


def find_section_re(lines, start_re, end_re):
    try:
        start = next(i for i, l in enumerate(lines) if start_re.match(l))
    except StopIteration:
        return []
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if start_re.match(lines[i]):
            continue
        if end_re.match(lines[i]):
            end = i
            break
    section = lines[start + 1:end]
    return [l for l in section if not ANEXO_ANY_RE.match(l)]


def split_cargo(lines, cargo_marker_prefix="Cargo: "):
    idxs = [i for i, l in enumerate(lines) if l.startswith(cargo_marker_prefix)]
    blocks = {}
    for n, i in enumerate(idxs):
        cargo = lines[i][len(cargo_marker_prefix):]
        end = idxs[n + 1] if n + 1 < len(idxs) else len(lines)
        blocks.setdefault(cargo, []).extend(lines[i + 1:end])
    return blocks


def parse_resultado_final(lines, is_prefeito):
    """Parseia o Anexo 'Resultado de votação' (final, por candidato)."""
    records = []
    i, n = 0, len(lines)
    while i < n:
        if not VOTE_RE.match(lines[i]):
            i += 1
            continue
        votos = int(lines[i].replace(".", ""))
        i += 1
        pct = None
        if is_prefeito and i < n and PCT_RE.match(lines[i]):
            pct = lines[i]
            i += 1
        situ = []
        while i < n and not CAND_RE.match(lines[i]):
            situ.append(lines[i])
            i += 1
        situacao_tot = " ".join(situ).strip()
        if i >= n:
            break
        m = CAND_RE.match(lines[i])
        numero = int(m.group(2))
        name_parts = [m.group(3)]
        i += 1
        while i < n and not is_status_line(lines[i]) and not VOTE_RE.match(lines[i]):
            name_parts.append(lines[i])
            i += 1
        nome = " ".join(name_parts).strip()
        validade = None
        if i < n and is_status_line(lines[i]) and not VOTE_RE.match(lines[i]):
            validade = lines[i]
            i += 1
        vice_nome = None
        if is_prefeito:
            vice_parts = []
            while (i < n and not VOTE_RE.match(lines[i]) and not CAND_RE.match(lines[i])
                   and not is_status_line(lines[i])):
                vice_parts.append(lines[i])
                i += 1
            vice_nome = " ".join(vice_parts).strip() or None
            # linhas remanescentes de observação (ex.: eleição sem vencedor definido por
            # decisão sub judice) não pertencem a nenhum candidato; apenas avançamos.
            while i < n and is_status_line(lines[i]) and not VOTE_RE.match(lines[i]):
                i += 1
        records.append(dict(votos=votos, pct=pct, situacao_totalizacao=situacao_tot,
                             numero=numero, nome=nome, validade=validade, vice_nome=vice_nome))
    return records


def parse_resultado_por_partido_vereador(lines):
    """Parseia o Anexo 'Resultado de votação por partido/federação/coligação' (Vereador),
    retornando o mapa numero_partido->sigla e os registros com partido atribuído."""
    party_map = {}
    records = []
    current_party = None
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if VOTE_RE.match(line):
            votos = int(line.replace(".", ""))
            i += 1
            situ = []
            while i < n and not CAND_RE.match(lines[i]):
                situ.append(lines[i])
                i += 1
            situacao_tot = " ".join(situ).strip()
            if i >= n:
                break
            m = CAND_RE.match(lines[i])
            numero = int(m.group(2))
            name_parts = [m.group(3)]
            i += 1
            while i < n and not is_status_line(lines[i]) and not VOTE_RE.match(lines[i]):
                name_parts.append(lines[i])
                i += 1
            nome = " ".join(name_parts).strip()
            validade = None
            if i < n and is_status_line(lines[i]) and not VOTE_RE.match(lines[i]):
                validade = lines[i]
                i += 1
            if current_party is not None:
                partido_numero = current_party
            else:
                numero_str = str(numero)
                partido_numero = int(numero_str[:2]) if len(numero_str) >= 2 else numero
            records.append(dict(votos=votos, situacao_totalizacao=situacao_tot,
                                 numero=numero, nome=nome, validade=validade,
                                 partido_numero=partido_numero))
            continue

        m = PARTY_HEADING_RE.match(line)
        if m:
            numero_p = int(m.group(1))
            party_map[numero_p] = m.group(2).strip()
            current_party = numero_p
            i += 1
            continue

        current_party = None  # cabeçalho de federação/coligação: usa prefixo do número
        i += 1
    return party_map, records


def parse_header(doc):
    """Extrai código TSE, nome do município, turno e data/hora de geração da página 0."""
    text = doc[0].get_text()
    m = HEADER_CODE_RE.search(text)
    tse_codigo, nome = (m.group(1), m.group(2)) if m else (None, None)

    turno = 2 if re.search(r"2º Turno", text) else 1

    hora_m = re.search(r"(\d{2}:\d{2}:\d{2})", text)
    data_m = re.search(r"(\d{1,2}) de (\w+) de (\d{4})", text)
    gerado_em = None
    if data_m and hora_m:
        dia, mes_nome, ano = data_m.groups()
        mes = MESES.get(_strip_accents(mes_nome.lower()))
        if mes:
            h, mnt, s = (int(x) for x in hora_m.group(1).split(":"))
            from datetime import datetime
            gerado_em = datetime(int(ano), mes, int(dia), h, mnt, s)

    return dict(tse_codigo=tse_codigo, nome_tse=nome, turno=turno, gerado_em=gerado_em)


def parse_pdf(path):
    doc = fitz.open(path)
    header = parse_header(doc)

    lines = []
    for page in doc:
        lines.extend(clean_lines(page.get_text()))

    ax_final = find_section_re(lines, RESULTADO_FINAL_RE, ANEXO_ANY_RE)
    ax_partido = find_section_re(lines, RESULTADO_PARTIDO_RE, ANEXO_ANY_RE)

    cargos_final = split_cargo(ax_final)
    cargos_partido = split_cargo(ax_partido)

    prefeito = parse_resultado_final(cargos_final.get("Prefeito", []), True)

    party_map, vereador = parse_resultado_por_partido_vereador(cargos_partido.get("Vereador", []))
    if not vereador and "Vereador" in cargos_final:
        vereador = parse_resultado_final(cargos_final.get("Vereador", []), False)

    header["prefeito"] = prefeito
    header["vereador"] = vereador
    header["party_map"] = party_map
    return header
