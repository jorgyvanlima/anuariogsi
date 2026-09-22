<?php

final class PcpaRepository
{
    /** Todas as unidades, agrupadas por tipo (Delegacia, Seccional, ...), para a visão geral do Estado. */
    public static function todasAgrupadasPorTipo(): array
    {
        $stmt = Database::connection()->query(
            "SELECT u.tipo, u.nome, u.endereco, u.bairro, u.telefone, u.funcionamento,
                    m.nome AS municipio_nome, m.ibge_code
             FROM pcpa_unidades u
             LEFT JOIN municipios m ON m.ibge_code = u.municipio_id
             ORDER BY u.tipo, m.nome NULLS LAST, u.nome"
        );
        $grouped = [];
        while ($row = $stmt->fetch()) {
            $grouped[$row['tipo']][] = $row;
        }
        return $grouped;
    }

    public static function porMunicipio(string $ibgeCode): array
    {
        $stmt = Database::connection()->prepare(
            "SELECT tipo, nome, endereco, bairro, telefone, funcionamento
             FROM pcpa_unidades
             WHERE municipio_id = :code
             ORDER BY tipo, nome"
        );
        $stmt->execute(['code' => $ibgeCode]);
        return $stmt->fetchAll();
    }

    public static function totalUnidades(): int
    {
        return (int) Database::connection()->query("SELECT COUNT(*) FROM pcpa_unidades")->fetchColumn();
    }
}
