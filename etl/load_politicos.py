"""Carrega prefeitos, vice-prefeitos e vereadores (eleitos, suplentes e não eleitos)
das Eleições Municipais 2024 do Pará, extraídos dos 148 PDFs de totalização, na
tabela `candidatos`."""
import glob
import re

from lib.normalize import normalize
from lib.partidos import PARTIDOS, sigla_nome
from lib.pdf_parser import parse_pdf

PDF_DIR = "/sources/pdfs"
FILENAME_RE = re.compile(r"^\d+_PA_.+_2024_T[12]\.pdf$")

SUPLENTE_RE = re.compile(r"^(\d+)º Suplente$")


def ordem_suplencia(situacao):
    m = SUPLENTE_RE.match(situacao)
    return int(m.group(1)) if m else None


def parse_pct(pct):
    if not pct:
        return None
    return float(pct.replace("%", "").replace(",", "."))


def build_municipio_map(conn):
    cur = conn.cursor()
    cur.execute("SELECT ibge_code, nome_normalizado FROM municipios")
    return {nome_norm: code for code, nome_norm in cur.fetchall()}


def load_all_pdfs():
    files = sorted(f for f in glob.glob(f"{PDF_DIR}/*.pdf") if FILENAME_RE.match(f.split("/")[-1]))
    parsed = []
    for f in files:
        try:
            parsed.append((f, parse_pdf(f)))
        except Exception as e:
            print(f"[politicos] ERRO ao processar {f}: {e}")
    return parsed


def group_by_tse_code(parsed):
    groups = {}
    for path, data in parsed:
        code = data["tse_codigo"]
        if not code:
            print(f"[politicos] não foi possível identificar o município de {path}, ignorando.")
            continue
        groups.setdefault(code, []).append(data)
    return groups


def has_eleito(records, prefix="Eleito"):
    return any(r["situacao_totalizacao"].startswith(prefix) for r in records)


def pick_best(docs, key):
    """Escolhe, entre os PDFs do mesmo município, a melhor fonte para `key`
    ('prefeito' ou 'vereador'): prioriza a que tem algum candidato Eleito,
    depois a mais recente (data de geração do relatório); usa a única
    disponível se nenhuma tiver eleito confirmado (ex.: resultado sub judice)."""
    candidatas = [d for d in docs if d[key]]
    if not candidatas:
        return None
    com_eleito = [d for d in candidatas if has_eleito(d[key])]
    pool = com_eleito or candidatas
    pool.sort(key=lambda d: d["gerado_em"] or 0, reverse=True)
    return pool[0]


def run(conn):
    municipio_map = build_municipio_map(conn)
    parsed = load_all_pdfs()
    groups = group_by_tse_code(parsed)

    cur = conn.cursor()
    cur.execute("DELETE FROM candidatos")

    global_party_map = {}
    for _, data in parsed:
        global_party_map.update(data["party_map"])

    for numero, (sigla, _nome) in PARTIDOS.items():
        global_party_map.setdefault(numero, sigla)

    for numero, sigla in sorted(global_party_map.items()):
        _, nome_completo = sigla_nome(numero)
        cur.execute(
            """
            INSERT INTO partidos (numero, sigla, nome) VALUES (%s, %s, %s)
            ON CONFLICT (numero) DO UPDATE SET sigla = EXCLUDED.sigla, nome = EXCLUDED.nome
            """,
            (numero, sigla, nome_completo),
        )

    total_municipios = 0
    total_candidatos = 0
    sem_municipio = []

    for tse_code, docs in groups.items():
        nome_tse = docs[0]["nome_tse"]
        municipio_id = municipio_map.get(normalize(nome_tse))
        if not municipio_id:
            sem_municipio.append((tse_code, nome_tse))
            continue

        pref_doc = pick_best(docs, "prefeito")
        ver_doc = pick_best(docs, "vereador")
        total_municipios += 1

        if pref_doc:
            for r in pref_doc["prefeito"]:
                sigla, _ = sigla_nome(r["numero"])
                partido_numero = r["numero"] if r["numero"] in global_party_map else None
                cur.execute(
                    """
                    INSERT INTO candidatos
                        (municipio_id, ano_eleicao, turno, cargo, numero_candidato, nome,
                         partido_numero, votos, percentual, situacao, ordem_suplencia)
                    VALUES (%s, 2024, %s, 'PREFEITO', %s, %s, %s, %s, %s, %s, NULL)
                    RETURNING id
                    """,
                    (municipio_id, pref_doc["turno"], r["numero"], r["nome"],
                     partido_numero, r["votos"], parse_pct(r["pct"]), r["situacao_totalizacao"]),
                )
                titular_id = cur.fetchone()[0]
                total_candidatos += 1

                if r.get("vice_nome"):
                    cur.execute(
                        """
                        INSERT INTO candidatos
                            (municipio_id, ano_eleicao, turno, cargo, nome, partido_numero,
                             situacao, titular_id)
                        VALUES (%s, 2024, %s, 'VICE_PREFEITO', %s, %s, %s, %s)
                        """,
                        (municipio_id, pref_doc["turno"], r["vice_nome"], partido_numero,
                         r["situacao_totalizacao"], titular_id),
                    )
                    total_candidatos += 1

        if ver_doc:
            for r in ver_doc["vereador"]:
                cur.execute(
                    """
                    INSERT INTO candidatos
                        (municipio_id, ano_eleicao, turno, cargo, numero_candidato, nome,
                         partido_numero, votos, situacao, ordem_suplencia)
                    VALUES (%s, 2024, %s, 'VEREADOR', %s, %s, %s, %s, %s, %s)
                    """,
                    (municipio_id, ver_doc["turno"], r["numero"], r["nome"],
                     r["partido_numero"], r["votos"], r["situacao_totalizacao"],
                     ordem_suplencia(r["situacao_totalizacao"])),
                )
                total_candidatos += 1

    conn.commit()
    print(f"[politicos] {total_municipios} municípios, {total_candidatos} candidatos carregados.")
    if sem_municipio:
        print(f"[politicos] {len(sem_municipio)} municípios do TSE não localizados: {sem_municipio}")
