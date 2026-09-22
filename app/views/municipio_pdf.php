<?php
/** @var array $municipio */
/** @var array $indicadores */
/** @var array $politica */

use Dompdf\Dompdf;
use Dompdf\Options;

function pdf_num($v, $dec = 2) {
    return number_format((float) $v, $dec, ',', '.');
}

ob_start();
?>
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    body { font-family: DejaVu Sans, sans-serif; font-size: 11px; color: #222; }
    h1 { color: #0b5d3b; font-size: 20px; margin-bottom: 0; }
    h2 { color: #0b5d3b; font-size: 15px; border-bottom: 1px solid #0b5d3b; margin-top: 22px; padding-bottom: 3px; }
    h3 { font-size: 12px; margin-bottom: 4px; margin-top: 12px; color: #333; }
    .subtitulo { color: #555; margin-top: 2px; margin-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
    th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; font-size: 10px; }
    th { background: #e8f3ec; }
    .badge { padding: 1px 5px; border-radius: 3px; color: #fff; font-size: 9px; }
    .badge-eleito { background: #1e7e34; }
    .footer-note { color: #888; font-size: 9px; margin-top: 20px; }
</style>
</head>
<body>

<h1><?= htmlspecialchars($municipio['nome']) ?></h1>
<p class="subtitulo">
    <?= htmlspecialchars($municipio['microrregiao'] ?? '') ?> · <?= htmlspecialchars($municipio['mesorregiao'] ?? '') ?>
    <?php if (!empty($municipio['regiao_integracao'])): ?> · Região de Integração <?= htmlspecialchars($municipio['regiao_integracao']) ?><?php endif; ?>
    · Código IBGE <?= htmlspecialchars($municipio['ibge_code']) ?>
    · Relatório gerado em <?= date('d/m/Y H:i') ?>
</p>

<h2>Política — Eleições Municipais 2024</h2>
<?php if ($politica['prefeito']): ?>
    <p><strong>Prefeito(a) eleito(a):</strong> <?= htmlspecialchars($politica['prefeito']['nome']) ?>
        (<?= htmlspecialchars($politica['prefeito']['partido_sigla'] ?? '') ?>) —
        <?= pdf_num($politica['prefeito']['votos'], 0) ?> votos
        (<?= pdf_num($politica['prefeito']['percentual'] ?? 0) ?>%)</p>
    <?php if ($politica['vice']): ?>
        <p><strong>Vice-prefeito(a):</strong> <?= htmlspecialchars($politica['vice']['nome']) ?>
            (<?= htmlspecialchars($politica['vice']['partido_sigla'] ?? '') ?>)</p>
    <?php endif; ?>
<?php else: ?>
    <p><em>Resultado da eleição para prefeito(a) ainda não definido (situação sub judice).</em></p>
<?php endif; ?>

<h3>Vereadores(as) eleitos(as) (<?= count($politica['vereadores_eleitos']) ?>)</h3>
<table>
    <thead><tr><th>Nº</th><th>Nome</th><th>Partido</th><th>Votos</th><th>Situação</th></tr></thead>
    <tbody>
    <?php foreach ($politica['vereadores_eleitos'] as $v): ?>
        <tr>
            <td><?= htmlspecialchars((string)$v['numero_candidato']) ?></td>
            <td><?= htmlspecialchars($v['nome']) ?></td>
            <td><?= htmlspecialchars($v['partido_sigla'] ?? '') ?></td>
            <td><?= pdf_num($v['votos'] ?? 0, 0) ?></td>
            <td><span class="badge badge-eleito"><?= htmlspecialchars($v['situacao']) ?></span></td>
        </tr>
    <?php endforeach; ?>
    </tbody>
</table>

<?php foreach ($indicadores as $tema => $porSubtema): ?>
    <h2><?= htmlspecialchars($tema) ?></h2>
    <?php foreach ($porSubtema as $subtema => $porIndicador): ?>
        <h3><?= $subtema !== '' ? htmlspecialchars($subtema) : 'Indicadores gerais' ?></h3>
        <table>
            <thead><tr><th>Indicador</th><th>Categoria</th><th>Ano</th><th>Valor</th></tr></thead>
            <tbody>
            <?php foreach ($porIndicador as $indicador => $porCategoria): ?>
                <?php foreach ($porCategoria as $categoria => $serie):
                    $n = count($serie['anos']);
                ?>
                    <tr>
                        <td><?= htmlspecialchars($indicador) ?></td>
                        <td><?= htmlspecialchars($categoria) ?></td>
                        <td><?= $serie['anos'][$n - 1] ?></td>
                        <td><?= pdf_num($serie['valores'][$n - 1]) ?></td>
                    </tr>
                <?php endforeach; ?>
            <?php endforeach; ?>
            </tbody>
        </table>
    <?php endforeach; ?>
<?php endforeach; ?>

<p class="footer-note">
    Fontes: Anuário Estatístico do Pará 2025, Justiça Eleitoral/TSE (Eleições Municipais 2024), IBGE.
    Relatório gerado automaticamente pelo Anuário do Pará — uso interno, não substitui as fontes oficiais.
</p>

</body>
</html>
<?php
$html = ob_get_clean();

$options = new Options();
$options->set('isRemoteEnabled', false);
$options->set('defaultFont', 'DejaVu Sans');

$dompdf = new Dompdf($options);
$dompdf->loadHtml($html);
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();
$dompdf->stream(
    'anuario-' . preg_replace('/[^a-z0-9]+/i', '-', $municipio['nome']) . '.pdf',
    ['Attachment' => false]
);
