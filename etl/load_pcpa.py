"""Carrega as Unidades Policiais da Polícia Civil do Pará (PCPA), a partir de um
PDF salvo de https://www.pc.pa.gov.br/delegacias (`pcpa/delegcias.pdf`).

O PDF não tem camada de texto — é uma sequência de capturas de tela da página
(imagem pura, texto=0 caracteres extraíveis). Por isso cada página é renderizada
e passada por OCR (Tesseract, idioma português) em vez de extraída diretamente.

O layout da página é um card por unidade, sempre no mesmo template:
    <NOME DA UNIDADE>
    Endereço: ...
    Município: <município>, <bairro>
    Telefone: ...
    Funcionamento: ...
O parser junta o texto OCR de todas as páginas em um único fluxo e reconhece
esses blocos por linha, então não depende de nenhum bloco ficar inteiro dentro
de uma página."""
import io
import os
import re

import fitz
import pytesseract
from PIL import Image

from lib.normalize import normalize

SRC_PDF = "/sources/pcpa/delegcias.pdf"
OCR_DPI = 200
OCR_LANG = "por"

FIELD_RE = re.compile(r"^(Endere[cç]o|Telefone|Funcionamento)\s*:\s*(.*)$", re.I)

# O rótulo "Município:" é o que o OCR mais corrompe neste PDF (acento + negrito
# derrubam o "í"/"p", às vezes some o ":" inteiro: "Munic io:", "Munici ",
# "Munic " sem dois-pontos...). Por isso não exige o rótulo completo, só o
# prefixo "Mun" + resto de letras minúsculas/acentuadas típicas do rótulo, e
# descarta esse prefixo em vez de exigir casar a palavra inteira.
MUNI_START_RE = re.compile(r"^Mun[a-zçí]{0,8}\b", re.I)
MUNI_LABEL_STRIP_RE = re.compile(r"^Mun[a-zçí]*\s*(io)?\s*:?\s*", re.I)

TIPO_KEYWORDS = [
    ("DELEGACIA", "Delegacia"),
    ("SECCIONAL", "Seccional"),
    ("SUPERINTEND", "Superintendência (Regional)"),
    ("DIVISÃO", "Divisão"),
    ("DIVISAO", "Divisão"),
    ("DIRETORIA", "Diretoria"),
]

# Ruído fixo do cabeçalho/filtros da página (só aparece antes do primeiro card,
# no topo da 1ª página) que não deve virar (parte de) um título de unidade.
TITLE_NOISE_LINES = {
    "IR PARA CONTEÚDO", "IR PARA MENU", "IR PARA SERVIÇOS", "IR PARA RODAPÉ",
    "ACESSIBILIDADE", "ALTO CONTRASTE", "MAPA DO SITE", "TRANSPARÊNCIA",
    "UNIDADES POLICIAIS", "MUNICÍPIO", "UNIDADE",
    "TODOS", "DIRETORIA", "DIVISÃO", "SUPERINTENDÊNCIA (REGIONAL)", "SECCIONAL", "DELEGACIA",
}


def _classify_tipo(titulo: str) -> str:
    upper = titulo.upper()
    for keyword, tipo in TIPO_KEYWORDS:
        if keyword in upper:
            return tipo
    return "Outro"


def _ocr_full_text() -> str:
    doc = fitz.open(SRC_PDF)
    parts = []
    zoom = OCR_DPI / 72
    matrix = fitz.Matrix(zoom, zoom)
    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        parts.append(pytesseract.image_to_string(img, lang=OCR_LANG))
    doc.close()
    return "\n".join(parts)


def _parse_records(text: str) -> list[dict]:
    records = []
    current = None
    pending_title_lines: list[str] = []

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        m = FIELD_RE.match(line)
        if m:
            field, value = m.group(1).lower(), m.group(2).strip()
            if field.startswith("endere"):
                if current and current.get("endereco"):
                    records.append(current)
                titulo = " ".join(pending_title_lines).strip()
                current = {"titulo": titulo, "endereco": value}
                pending_title_lines = []
            elif current is None:
                pass
            elif field == "telefone":
                current["telefone"] = value
            elif field == "funcionamento":
                current["funcionamento"] = value
            continue

        # rótulo "Município:" quase sempre sai corrompido do OCR (ver comentário
        # acima de MUNI_START_RE) — não exige o rótulo inteiro, só o prefixo "Mun".
        if current is not None and "municipio_raw" not in current and MUNI_START_RE.match(line):
            current["municipio_raw"] = MUNI_LABEL_STRIP_RE.sub("", line, count=1).strip()
            continue

        upper = line.upper()
        is_noise = upper in TITLE_NOISE_LINES or sum(1 for w in TITLE_NOISE_LINES if w in upper) >= 3
        if not is_noise:
            pending_title_lines.append(line)
            pending_title_lines = pending_title_lines[-3:]

    if current and current.get("endereco"):
        records.append(current)
    return records


def _find_municipio_substring(text, norms_sorted, by_norm, prefer_last=False):
    """Varre `text` por qualquer nome de município conhecido (com word-boundary,
    após normalizar) e devolve o ibge_code do primeiro ou último achado.
    Usado como fallback quando o campo "Município:" não foi capturado — nesse
    caso o texto perdido normalmente "gruda" no título do card seguinte, então
    `prefer_last=True` pula esse ruído colado no início e pega a ocorrência mais
    à direita (mais perto do nome real da unidade)."""
    if not text:
        return None
    norm_text = " " + normalize(text) + " "
    matches = []
    for norm in norms_sorted:
        idx = norm_text.find(" " + norm + " ")
        if idx != -1:
            matches.append((idx, norm))
    if not matches:
        return None
    chosen = max(matches, key=lambda x: x[0]) if prefer_last else min(matches, key=lambda x: x[0])
    return by_norm.get(chosen[1])


def run(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM pcpa_unidades")

    if not os.path.isfile(SRC_PDF):
        print("[pcpa] PDF de delegacias não encontrado, pulando.")
        conn.commit()
        return

    cur.execute("SELECT ibge_code, nome_normalizado FROM municipios")
    by_norm = {nome_normalizado: ibge_code for ibge_code, nome_normalizado in cur.fetchall()}
    norms_sorted = sorted((n for n in by_norm if len(n) >= 4), key=len, reverse=True)

    text = _ocr_full_text()
    records = _parse_records(text)

    total = 0
    sem_municipio = 0
    for rec in records:
        titulo = rec.get("titulo") or ""
        if not titulo:
            continue

        municipio_raw = rec.get("municipio_raw", "") or ""
        municipio_nome, _, bairro = municipio_raw.partition(",")
        municipio_nome = municipio_nome.strip()
        bairro = bairro.strip() or None

        ibge_code = by_norm.get(normalize(municipio_nome))
        if ibge_code is None:
            # campo "Município:" ausente ou não reconhecido: tenta achar o nome
            # do município embutido no próprio título ("DELEGACIA DE X") ou no
            # fim do endereço (formato BR: "..., Bairro, Município/PA").
            ibge_code = _find_municipio_substring(titulo, norms_sorted, by_norm, prefer_last=True)
        if ibge_code is None:
            ibge_code = _find_municipio_substring(rec.get("endereco"), norms_sorted, by_norm, prefer_last=True)
        if ibge_code is None:
            sem_municipio += 1

        cur.execute(
            """
            INSERT INTO pcpa_unidades (municipio_id, tipo, nome, endereco, bairro, telefone, funcionamento)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ibge_code,
                _classify_tipo(titulo),
                titulo,
                rec.get("endereco"),
                bairro,
                rec.get("telefone"),
                rec.get("funcionamento"),
            ),
        )
        total += 1

    conn.commit()
    print(f"[pcpa] {total} unidades policiais carregadas ({sem_municipio} sem município identificado).")
