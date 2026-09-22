<?php

final class MunicipioRepository
{
    public static function all(): array
    {
        $stmt = Database::connection()->query(
            "SELECT ibge_code, nome, mesorregiao, microrregiao, regiao_imediata,
                    regiao_intermediaria, regiao_integracao
             FROM municipios ORDER BY nome"
        );
        return $stmt->fetchAll();
    }

    public static function find(string $ibgeCode): ?array
    {
        $stmt = Database::connection()->prepare(
            "SELECT ibge_code, nome, mesorregiao, microrregiao, regiao_imediata,
                    regiao_intermediaria, regiao_integracao
             FROM municipios WHERE ibge_code = :code"
        );
        $stmt->execute(['code' => $ibgeCode]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public static function count(): int
    {
        return (int) Database::connection()->query("SELECT COUNT(*) FROM municipios")->fetchColumn();
    }
}
