<?php

final class MppaRepository
{
    /** Indicadores estaduais agrupados por categoria: [categoria][] = row */
    public static function indicadoresEstado(): array
    {
        $stmt = Database::connection()->query(
            "SELECT categoria, indicador, ano, valor, unidade
             FROM mppa_indicadores
             WHERE escopo = 'ESTADO'
             ORDER BY categoria, indicador, ano"
        );
        $grouped = [];
        while ($row = $stmt->fetch()) {
            $grouped[$row['categoria']][] = $row;
        }
        return $grouped;
    }

    /** Lista de obras/sedes agrupada por tipo, para a visão geral do Estado. */
    public static function obrasEstado(): array
    {
        $stmt = Database::connection()->query(
            "SELECT o.tipo, o.ano, o.titulo, m.nome AS municipio_nome, m.ibge_code
             FROM mppa_obras o
             JOIN municipios m ON m.ibge_code = o.municipio_id
             ORDER BY o.ano DESC, o.tipo, m.nome"
        );
        $grouped = [];
        while ($row = $stmt->fetch()) {
            $grouped[$row['tipo']][] = $row;
        }
        return $grouped;
    }

    public static function promotoriaInstalada(string $ibgeCode): ?bool
    {
        $stmt = Database::connection()->prepare(
            "SELECT valor FROM mppa_indicadores
             WHERE escopo = 'MUNICIPIO' AND municipio_id = :code
               AND indicador = 'Promotoria de Justiça instalada'
             LIMIT 1"
        );
        $stmt->execute(['code' => $ibgeCode]);
        $valor = $stmt->fetchColumn();
        return $valor === false ? null : ((float) $valor > 0);
    }

    public static function obrasPorMunicipio(string $ibgeCode): array
    {
        $stmt = Database::connection()->prepare(
            "SELECT tipo, titulo, ano FROM mppa_obras
             WHERE municipio_id = :code
             ORDER BY ano DESC, tipo"
        );
        $stmt->execute(['code' => $ibgeCode]);
        return $stmt->fetchAll();
    }

    /** Ações do relatório que citam o município, agrupadas por área. */
    public static function acoesPorMunicipio(string $ibgeCode): array
    {
        $stmt = Database::connection()->prepare(
            "SELECT a.area, a.ano, a.resumo
             FROM mppa_acoes a
             JOIN mppa_acoes_municipios am ON am.acao_id = a.id
             WHERE am.municipio_id = :code
             ORDER BY a.area, a.id"
        );
        $stmt->execute(['code' => $ibgeCode]);
        $grouped = [];
        while ($row = $stmt->fetch()) {
            $grouped[$row['area']][] = $row;
        }
        return $grouped;
    }

    /** Ações de âmbito estadual (sem município específico citado), agrupadas por área. */
    public static function acoesEstado(): array
    {
        $stmt = Database::connection()->query(
            "SELECT area, ano, resumo FROM mppa_acoes
             WHERE escopo = 'ESTADO'
             ORDER BY area, id"
        );
        $grouped = [];
        while ($row = $stmt->fetch()) {
            $grouped[$row['area']][] = $row;
        }
        return $grouped;
    }
}
