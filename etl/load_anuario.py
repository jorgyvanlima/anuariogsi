"""Carrega o Anuário_2025.csv (~930 mil linhas, todos os temas/indicadores/anos)
para a tabela `indicadores`, usando COPY em lotes para desempenho.

O CSV bruto tem ~134MB (acima do limite de arquivo do GitHub), por isso o
repositório guarda apenas a versão comprimida `Anuário_2025.csv.gz` (~8MB);
este loader lê o `.gz` se existir e cai para o `.csv` sem compressão caso
alguém rode o ETL a partir dos arquivos originais sem compactar."""
import csv
import gzip
import io
import os

from lib.normalize import normalize

ANUARIO_DIR = "/sources/anuario"
ANUARIO_CSV_GZ = os.path.join(ANUARIO_DIR, "Anuário_2025.csv.gz")
ANUARIO_CSV_PLAIN = os.path.join(ANUARIO_DIR, "Anuário_2025.csv")
CHUNK_SIZE = 50_000


def open_anuario():
    if os.path.exists(ANUARIO_CSV_GZ):
        return gzip.open(ANUARIO_CSV_GZ, mode="rt", encoding="utf-8", newline="")
    return open(ANUARIO_CSV_PLAIN, encoding="utf-8", newline="")

NULL_MARKERS = {"-", "NA", ""}


def clean(value):
    v = (value or "").strip()
    return "" if v in NULL_MARKERS else v


def clean_ano(value):
    v = (value or "").strip().rstrip("*").strip()
    return v if v.isdigit() else ""


def build_municipio_map(conn):
    cur = conn.cursor()
    cur.execute("SELECT ibge_code, nome_normalizado FROM municipios")
    return {nome_norm: code for code, nome_norm in cur.fetchall()}


def run(conn):
    municipio_map = build_municipio_map(conn)

    cur = conn.cursor()
    cur.execute("DELETE FROM indicadores")

    total = 0
    skipped = 0
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=",", quoting=csv.QUOTE_MINIMAL)

    def flush():
        nonlocal buf, writer
        buf.seek(0)
        cur.copy_expert(
            """
            COPY indicadores (municipio_id, escopo, tematica, subtema, indicador, categoria, ano, valor)
            FROM STDIN WITH (FORMAT csv, NULL '')
            """,
            buf,
        )
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=",", quoting=csv.QUOTE_MINIMAL)

    with open_anuario() as f:
        reader = csv.DictReader(f)
        pending = 0
        for row in reader:
            tematica = clean(row["tematica"])
            indicador = clean(row["indicador"])
            if not tematica or not indicador:
                skipped += 1
                continue

            localidade = (row["localidade"] or "").strip()
            ri = (row["ri"] or "").strip()

            if localidade == "Pará" and ri == "Pará":
                escopo = "ESTADO"
                municipio_id = ""
            else:
                norm = normalize(localidade)
                municipio_id = municipio_map.get(norm, "")
                if not municipio_id:
                    skipped += 1
                    continue
                escopo = "MUNICIPIO"

            writer.writerow(
                [
                    municipio_id,
                    escopo,
                    tematica,
                    clean(row["subtema"]),
                    indicador,
                    clean(row["categoria"]),
                    clean_ano(row["ano"]),
                    (row["valor"] or "").strip(),
                ]
            )
            total += 1
            pending += 1
            if pending >= CHUNK_SIZE:
                flush()
                pending = 0

        if pending:
            flush()

    conn.commit()
    print(f"[anuario] {total} indicadores carregados, {skipped} linhas ignoradas.")
