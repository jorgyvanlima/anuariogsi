"""Orquestra a carga completa do banco de dados do Anuário Estatístico do Pará.
Executado uma vez pelo serviço `etl` do docker-compose antes do app subir; é
idempotente (cada loader limpa e recarrega sua(s) própria(s) tabela(s))."""
import sys

from lib.db import get_connection

import load_municipios
import load_anuario
import load_mapas
import load_politicos
import load_mppa


def main():
    conn = get_connection()
    try:
        print("[run_all] carregando municípios...")
        load_municipios.run(conn)

        print("[run_all] carregando indicadores do Anuário_2025...")
        load_anuario.run(conn)

        print("[run_all] catalogando mapas temáticos...")
        load_mapas.run(conn)

        print("[run_all] extraindo prefeitos/vereadores dos PDFs de totalização...")
        load_politicos.run(conn)

        print("[run_all] carregando dados do Ministério Público (MPPA)...")
        load_mppa.run(conn)

        print("[run_all] carga concluída com sucesso.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[run_all] FALHA: {e}", file=sys.stderr)
        raise
