<?php

final class MapaRepository
{
    public static function agrupadosPorCategoria(): array
    {
        $stmt = Database::connection()->query(
            "SELECT categoria, titulo, arquivo, ano FROM mapas_tematicos ORDER BY categoria, titulo"
        );
        $grouped = [];
        while ($row = $stmt->fetch()) {
            $grouped[$row['categoria']][] = $row;
        }
        return $grouped;
    }
}
