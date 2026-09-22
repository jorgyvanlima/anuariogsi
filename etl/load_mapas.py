"""Cataloga os mapas temáticos estáticos (mapas/<categoria>/*.jpg|png) na tabela
`mapas_tematicos` e copia os arquivos para o volume público servido pelo app PHP."""
import os
import re
import shutil

SRC_DIR = "/sources/mapas"
DST_DIR = "/output/mapas"

IMG_EXT = {".jpg", ".jpeg", ".png"}

CATEGORIA_LABEL = {
    "demografia": "Demografia",
    "economia": "Economia",
    "social": "Social",
    "meio_ambiente": "Meio Ambiente",
    "territorio": "Território",
    "infraestrutura": "Infraestrutura",
}


def titulo_from_filename(stem: str) -> str:
    # remove prefixo de categoria (ex.: "Social_", "MeioAmb_", "Economia_")
    stem = re.sub(r"^[A-Za-zÀ-ú]+_", "", stem)
    stem = stem.replace("_", " ").strip()
    stem = re.sub(r"(?<=[a-zà-ú])(?=[A-ZÀ-Ú])", " ", stem)
    return stem.strip() or stem


def run(conn):
    cur = conn.cursor()
    cur.execute("DELETE FROM mapas_tematicos")

    os.makedirs(DST_DIR, exist_ok=True)
    total = 0

    if not os.path.isdir(SRC_DIR):
        print("[mapas] diretório de origem não encontrado, pulando.")
        return

    for categoria_dir in sorted(os.listdir(SRC_DIR)):
        full_dir = os.path.join(SRC_DIR, categoria_dir)
        if not os.path.isdir(full_dir):
            continue
        categoria = CATEGORIA_LABEL.get(categoria_dir, categoria_dir.title())

        dst_categoria_dir = os.path.join(DST_DIR, categoria_dir)
        os.makedirs(dst_categoria_dir, exist_ok=True)

        for filename in sorted(os.listdir(full_dir)):
            stem, ext = os.path.splitext(filename)
            if ext.lower() not in IMG_EXT:
                continue

            shutil.copy2(os.path.join(full_dir, filename), os.path.join(dst_categoria_dir, filename))

            year_match = re.search(r"(20\d{2})", stem)
            ano = year_match.group(1) if year_match else None
            titulo = titulo_from_filename(stem)
            arquivo = f"{categoria_dir}/{filename}"

            cur.execute(
                """
                INSERT INTO mapas_tematicos (categoria, titulo, arquivo, ano)
                VALUES (%s, %s, %s, %s)
                """,
                (categoria, titulo, arquivo, ano),
            )
            total += 1

    conn.commit()
    print(f"[mapas] {total} mapas temáticos catalogados.")
