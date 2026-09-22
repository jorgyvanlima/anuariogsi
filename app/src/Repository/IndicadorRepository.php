<?php

final class IndicadorRepository
{
    /**
     * Retorna os indicadores de um município agrupados em
     * [tematica][subtema][indicador][categoria] = ['anos' => [...], 'valores' => [...]]
     */
    public static function agrupadosPorMunicipio(string $ibgeCode): array
    {
        $stmt = Database::connection()->prepare(
            "SELECT tematica, subtema, indicador, categoria, ano, valor
             FROM indicadores
             WHERE municipio_id = :code
             ORDER BY tematica, subtema NULLS FIRST, indicador, categoria NULLS FIRST, ano"
        );
        $stmt->execute(['code' => $ibgeCode]);

        $grouped = [];
        while ($row = $stmt->fetch()) {
            $tematica = $row['tematica'];
            $subtema = $row['subtema'] ?? '';
            $indicador = $row['indicador'];
            $categoria = $row['categoria'] ?? '';

            $grouped[$tematica][$subtema][$indicador][$categoria] ??= ['anos' => [], 'valores' => []];
            $grouped[$tematica][$subtema][$indicador][$categoria]['anos'][] = (int) $row['ano'];
            $grouped[$tematica][$subtema][$indicador][$categoria]['valores'][] = (float) $row['valor'];
        }
        return $grouped;
    }

    public static function estadoSerie(string $indicadorLike): array
    {
        $stmt = Database::connection()->prepare(
            "SELECT ano, valor FROM indicadores
             WHERE escopo = 'ESTADO' AND (categoria IS NULL OR categoria = '')
               AND indicador ILIKE :pat
             ORDER BY ano"
        );
        $stmt->execute(['pat' => '%' . $indicadorLike . '%']);
        return $stmt->fetchAll();
    }

    public static function estadoUltimoValor(string $indicadorLike): ?array
    {
        $serie = self::estadoSerie($indicadorLike);
        return $serie ? end($serie) : null;
    }
}
