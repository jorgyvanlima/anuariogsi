<?php

final class CandidatoRepository
{
    public static function politicaDoMunicipio(string $ibgeCode): array
    {
        $stmt = Database::connection()->prepare(
            "SELECT c.id, c.cargo, c.numero_candidato, c.nome, c.votos, c.percentual,
                    c.situacao, c.ordem_suplencia, c.titular_id,
                    p.sigla AS partido_sigla, p.nome AS partido_nome
             FROM candidatos c
             LEFT JOIN partidos p ON p.numero = c.partido_numero
             WHERE c.municipio_id = :code AND c.ano_eleicao = 2024
             ORDER BY c.cargo,
                      CASE WHEN c.votos IS NULL THEN 1 ELSE 0 END,
                      c.votos DESC NULLS LAST"
        );
        $stmt->execute(['code' => $ibgeCode]);
        $rows = $stmt->fetchAll();

        $prefeito = null;
        $vice = null;
        $vereadoresEleitos = [];
        $vereadoresSuplentes = [];
        $vereadoresNaoEleitos = [];

        foreach ($rows as $row) {
            if ($row['cargo'] === 'PREFEITO' && $row['situacao'] === 'Eleito') {
                $prefeito = $row;
            } elseif ($row['cargo'] === 'VICE_PREFEITO' && $prefeito && $row['titular_id'] == $prefeito['id']) {
                $vice = $row;
            } elseif ($row['cargo'] === 'VEREADOR') {
                if (str_starts_with($row['situacao'], 'Eleito')) {
                    $vereadoresEleitos[] = $row;
                } elseif (str_contains($row['situacao'], 'Suplente')) {
                    $vereadoresSuplentes[] = $row;
                } else {
                    $vereadoresNaoEleitos[] = $row;
                }
            }
        }

        $candidatosPrefeito = array_values(array_filter($rows, fn($r) => $r['cargo'] === 'PREFEITO'));

        return [
            'prefeito' => $prefeito,
            'vice' => $vice,
            'candidatos_prefeito' => $candidatosPrefeito,
            'vereadores_eleitos' => $vereadoresEleitos,
            'vereadores_suplentes' => $vereadoresSuplentes,
            'vereadores_nao_eleitos' => $vereadoresNaoEleitos,
        ];
    }
}
