"""Carrega a tabela `municipios` a partir da lista oficial do IBGE (144 municípios do Pará)
e enriquece com a Região de Integração declarada no Anuário_2025."""
import csv
import json

from lib.normalize import normalize

IBGE_JSON = "/data_static/pa_municipios_ibge.json"
ANUARIO_CSV = "/sources/anuario/Anuário_2025.csv"


def load_regioes_integracao():
    ri_by_norm_name = {}
    with open(ANUARIO_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            loc = row["localidade"]
            ri = row["ri"]
            if not loc or loc == "Pará" or not ri or ri == "Pará":
                continue
            ri_by_norm_name[normalize(loc)] = ri
    return ri_by_norm_name


def run(conn):
    with open(IBGE_JSON, encoding="utf-8") as f:
        municipios = json.load(f)

    ri_map = load_regioes_integracao()

    cur = conn.cursor()
    count = 0
    for m in municipios:
        ibge_code = str(m["id"])
        nome = m["nome"]
        nome_norm = normalize(nome)
        mesorregiao = m.get("microrregiao", {}).get("mesorregiao", {}).get("nome")
        microrregiao = m.get("microrregiao", {}).get("nome")
        regiao_imediata = m.get("regiao-imediata", {}).get("nome")
        regiao_intermediaria = (
            m.get("regiao-imediata", {}).get("regiao-intermediaria", {}).get("nome")
        )
        regiao_integracao = ri_map.get(nome_norm)

        cur.execute(
            """
            INSERT INTO municipios
                (ibge_code, nome, nome_normalizado, mesorregiao, microrregiao,
                 regiao_imediata, regiao_intermediaria, regiao_integracao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ibge_code) DO UPDATE SET
                nome = EXCLUDED.nome,
                nome_normalizado = EXCLUDED.nome_normalizado,
                mesorregiao = EXCLUDED.mesorregiao,
                microrregiao = EXCLUDED.microrregiao,
                regiao_imediata = EXCLUDED.regiao_imediata,
                regiao_intermediaria = EXCLUDED.regiao_intermediaria,
                regiao_integracao = EXCLUDED.regiao_integracao
            """,
            (
                ibge_code, nome, nome_norm, mesorregiao, microrregiao,
                regiao_imediata, regiao_intermediaria, regiao_integracao,
            ),
        )
        count += 1
    conn.commit()
    print(f"[municipios] {count} municípios carregados/atualizados.")
