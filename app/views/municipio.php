<?php
/** @var array $municipio */
/** @var array $indicadores */
/** @var array $politica */
/** @var array $mppa */
$pageTitle = $municipio['nome'] . ' — Anuário do Pará';
$page = 'municipio';
require __DIR__ . '/partials/header.php';

function situacao_badge(string $situacao): string
{
    $s = mb_strtolower($situacao);
    if (str_starts_with($s, 'eleito')) return 'success';
    if (str_contains($s, 'suplente')) return 'secondary';
    if (str_contains($s, 'anulad') || str_contains($s, 'indeferid')) return 'danger';
    return 'light text-dark';
}

$temasIcones = [
    'Demografia' => 'people-group', 'Economia' => 'coins', 'Social' => 'hand-holding-heart',
    'Território' => 'map', 'Meio Ambiente' => 'leaf', 'Infraestrutura' => 'road',
];
$temasDisponiveis = array_keys($indicadores);
$chartPayload = [];
?>

<section class="content-header">
    <div class="container-fluid">
        <div class="row mb-2 align-items-center">
            <div class="col-sm-8">
                <h1><i class="fas fa-city"></i> <?= htmlspecialchars($municipio['nome']) ?></h1>
                <p class="text-muted mb-0">
                    <?= htmlspecialchars($municipio['microrregiao'] ?? '') ?> ·
                    <?= htmlspecialchars($municipio['mesorregiao'] ?? '') ?>
                    <?php if (!empty($municipio['regiao_integracao'])): ?>
                        · Região de Integração <?= htmlspecialchars($municipio['regiao_integracao']) ?>
                    <?php endif; ?>
                    · Código IBGE <?= htmlspecialchars($municipio['ibge_code']) ?>
                </p>
            </div>
            <div class="col-sm-4 text-sm-right">
                <a href="index.php?page=municipio&codigo=<?= htmlspecialchars($municipio['ibge_code']) ?>&export=pdf"
                   class="btn btn-outline-success" target="_blank">
                    <i class="fas fa-file-pdf"></i> Exportar PDF
                </a>
            </div>
        </div>
    </div>
</section>

<section class="content">
    <div class="container-fluid">

        <div class="card card-outline card-success">
            <div class="card-header p-2">
                <ul class="nav nav-pills" id="tabs-municipio" role="tablist">
                    <?php foreach ($temasDisponiveis as $i => $tema): ?>
                        <li class="nav-item">
                            <a class="nav-link <?= $i === 0 ? 'active' : '' ?>" data-toggle="pill"
                               href="#pane-<?= md5($tema) ?>" role="tab">
                                <i class="fas fa-<?= $temasIcones[$tema] ?? 'chart-simple' ?>"></i>
                                <?= htmlspecialchars($tema) ?>
                            </a>
                        </li>
                    <?php endforeach; ?>
                    <li class="nav-item">
                        <a class="nav-link" data-toggle="pill" href="#pane-politica" role="tab">
                            <i class="fas fa-landmark-dome"></i> Política
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-toggle="pill" href="#pane-mppa" role="tab">
                            <i class="fas fa-scale-balanced"></i> Ministério Público
                        </a>
                    </li>
                </ul>
            </div>
            <div class="card-body">
                <div class="tab-content">
                    <?php foreach ($temasDisponiveis as $ti => $tema): ?>
                        <div class="tab-pane fade <?= $ti === 0 ? 'show active' : '' ?>" id="pane-<?= md5($tema) ?>">
                            <?php foreach ($indicadores[$tema] as $subtema => $porIndicador): ?>
                                <h5 class="mt-3 border-bottom pb-1">
                                    <?= $subtema !== '' ? htmlspecialchars($subtema) : 'Indicadores gerais' ?>
                                </h5>
                                <div class="row">
                                    <?php foreach ($porIndicador as $indicador => $porCategoria): ?>
                                        <?php foreach ($porCategoria as $categoria => $serie):
                                            $labelCompleto = $indicador . ($categoria !== '' ? " — {$categoria}" : '');
                                            $n = count($serie['anos']);
                                            $ultimoValor = $serie['valores'][$n - 1];
                                            $ultimoAno = $serie['anos'][$n - 1];
                                        ?>
                                        <?php if ($n >= 2): ?>
                                            <?php $canvasId = 'c' . substr(md5($tema . $indicador . $categoria), 0, 12); ?>
                                            <div class="col-md-4 col-sm-6 mb-4">
                                                <div class="stat-card">
                                                    <div class="rotulo"><?= htmlspecialchars($labelCompleto) ?></div>
                                                    <div class="valor"><?= number_format($ultimoValor, 2, ',', '.') ?>
                                                        <small class="text-muted">(<?= $ultimoAno ?>)</small></div>
                                                    <canvas id="<?= $canvasId ?>" height="120"></canvas>
                                                </div>
                                            </div>
                                            <?php $chartPayload[$canvasId] = ['labels' => $serie['anos'], 'data' => $serie['valores']]; ?>
                                        <?php else: ?>
                                            <div class="col-md-4 col-sm-6 mb-3">
                                                <div class="stat-card">
                                                    <div class="rotulo"><?= htmlspecialchars($labelCompleto) ?></div>
                                                    <div class="valor"><?= number_format($ultimoValor, 2, ',', '.') ?>
                                                        <small class="text-muted">(<?= $ultimoAno ?>)</small></div>
                                                </div>
                                            </div>
                                        <?php endif; ?>
                                        <?php endforeach; ?>
                                    <?php endforeach; ?>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php endforeach; ?>

                    <div class="tab-pane fade" id="pane-politica">
                        <?php if ($politica['prefeito']): ?>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card bg-success text-white">
                                        <div class="card-body">
                                            <h5><i class="fas fa-user-tie"></i> Prefeito(a) eleito(a)</h5>
                                            <h4><?= htmlspecialchars($politica['prefeito']['nome']) ?></h4>
                                            <p class="mb-0">
                                                <?= htmlspecialchars($politica['prefeito']['partido_sigla'] ?? '') ?>
                                                · <?= number_format($politica['prefeito']['votos'], 0, ',', '.') ?> votos
                                                (<?= number_format($politica['prefeito']['percentual'] ?? 0, 2, ',', '.') ?>%)
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <?php if ($politica['vice']): ?>
                                <div class="col-md-6">
                                    <div class="card bg-light">
                                        <div class="card-body">
                                            <h5><i class="fas fa-user"></i> Vice-prefeito(a)</h5>
                                            <h4><?= htmlspecialchars($politica['vice']['nome']) ?></h4>
                                            <p class="mb-0 text-muted"><?= htmlspecialchars($politica['vice']['partido_sigla'] ?? '') ?></p>
                                        </div>
                                    </div>
                                </div>
                                <?php endif; ?>
                            </div>
                        <?php else: ?>
                            <div class="alert alert-warning">
                                <i class="fas fa-triangle-exclamation"></i>
                                Resultado da eleição para prefeito(a) deste município ainda não está definido
                                (situação sub judice na fonte oficial).
                            </div>
                        <?php endif; ?>

                        <h5 class="mt-4">Candidatos(as) a prefeito(a) — 2024</h5>
                        <table class="table table-sm table-striped">
                            <thead><tr><th>Nº</th><th>Candidato(a)</th><th>Partido</th><th>Votos</th><th>%</th><th>Situação</th></tr></thead>
                            <tbody>
                            <?php foreach ($politica['candidatos_prefeito'] as $c): ?>
                                <tr>
                                    <td><?= htmlspecialchars((string)$c['numero_candidato']) ?></td>
                                    <td><?= htmlspecialchars($c['nome']) ?></td>
                                    <td><?= htmlspecialchars($c['partido_sigla'] ?? '') ?></td>
                                    <td><?= number_format($c['votos'] ?? 0, 0, ',', '.') ?></td>
                                    <td><?= $c['percentual'] !== null ? number_format($c['percentual'], 2, ',', '.') . '%' : '—' ?></td>
                                    <td><span class="badge badge-<?= situacao_badge($c['situacao']) ?>"><?= htmlspecialchars($c['situacao']) ?></span></td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>

                        <h5 class="mt-4">Vereadores(as) eleitos(as) — <?= count($politica['vereadores_eleitos']) ?> cadeiras</h5>
                        <table class="table table-sm table-striped">
                            <thead><tr><th>Nº</th><th>Vereador(a)</th><th>Partido</th><th>Votos</th><th>Situação</th></tr></thead>
                            <tbody>
                            <?php foreach ($politica['vereadores_eleitos'] as $v): ?>
                                <tr>
                                    <td><?= htmlspecialchars((string)$v['numero_candidato']) ?></td>
                                    <td><?= htmlspecialchars($v['nome']) ?></td>
                                    <td><?= htmlspecialchars($v['partido_sigla'] ?? '') ?></td>
                                    <td><?= number_format($v['votos'] ?? 0, 0, ',', '.') ?></td>
                                    <td><span class="badge badge-success"><?= htmlspecialchars($v['situacao']) ?></span></td>
                                </tr>
                            <?php endforeach; ?>
                            </tbody>
                        </table>

                        <button class="btn btn-sm btn-outline-secondary" type="button" data-toggle="collapse" data-target="#collapse-suplentes">
                            <i class="fas fa-chevron-down"></i> Ver suplentes (<?= count($politica['vereadores_suplentes']) ?>)
                        </button>
                        <div class="collapse mt-2" id="collapse-suplentes">
                            <table class="table table-sm table-striped">
                                <thead><tr><th>Nº</th><th>Candidato(a)</th><th>Partido</th><th>Votos</th><th>Situação</th></tr></thead>
                                <tbody>
                                <?php foreach ($politica['vereadores_suplentes'] as $v): ?>
                                    <tr>
                                        <td><?= htmlspecialchars((string)$v['numero_candidato']) ?></td>
                                        <td><?= htmlspecialchars($v['nome']) ?></td>
                                        <td><?= htmlspecialchars($v['partido_sigla'] ?? '') ?></td>
                                        <td><?= number_format($v['votos'] ?? 0, 0, ',', '.') ?></td>
                                        <td><span class="badge badge-secondary"><?= htmlspecialchars($v['situacao']) ?></span></td>
                                    </tr>
                                <?php endforeach; ?>
                                </tbody>
                            </table>
                        </div>

                        <button class="btn btn-sm btn-outline-secondary mt-2" type="button" data-toggle="collapse" data-target="#collapse-naoeleitos">
                            <i class="fas fa-chevron-down"></i> Ver demais candidatos(as) a vereador(a) (<?= count($politica['vereadores_nao_eleitos']) ?>)
                        </button>
                        <div class="collapse mt-2" id="collapse-naoeleitos">
                            <table class="table table-sm table-striped">
                                <thead><tr><th>Nº</th><th>Candidato(a)</th><th>Partido</th><th>Votos</th><th>Situação</th></tr></thead>
                                <tbody>
                                <?php foreach ($politica['vereadores_nao_eleitos'] as $v): ?>
                                    <tr>
                                        <td><?= htmlspecialchars((string)$v['numero_candidato']) ?></td>
                                        <td><?= htmlspecialchars($v['nome']) ?></td>
                                        <td><?= htmlspecialchars($v['partido_sigla'] ?? '') ?></td>
                                        <td><?= number_format($v['votos'] ?? 0, 0, ',', '.') ?></td>
                                        <td><span class="badge badge-light"><?= htmlspecialchars($v['situacao']) ?></span></td>
                                    </tr>
                                <?php endforeach; ?>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="tab-pane fade" id="pane-mppa">
                        <?php if ($mppa['promotoria_instalada'] === true): ?>
                            <div class="alert alert-success"><i class="fas fa-circle-check"></i> Município possui Promotoria de Justiça instalada.</div>
                        <?php elseif ($mppa['promotoria_instalada'] === false): ?>
                            <div class="alert alert-warning"><i class="fas fa-triangle-exclamation"></i> Município ainda não possui Promotoria de Justiça instalada (situação vigente no relatório 2023/2024 do MPPA).</div>
                        <?php else: ?>
                            <div class="alert alert-light border"><i class="fas fa-circle-question"></i> Situação da Promotoria de Justiça não informada para este município.</div>
                        <?php endif; ?>

                        <?php if ($mppa['obras']): ?>
                            <h5 class="mt-4">Sedes, obras e reformas</h5>
                            <table class="table table-sm table-striped">
                                <thead><tr><th>Ano</th><th>Tipo</th><th>Observação</th></tr></thead>
                                <tbody>
                                <?php foreach ($mppa['obras'] as $o): ?>
                                    <tr>
                                        <td><?= htmlspecialchars((string)$o['ano']) ?></td>
                                        <td><?= htmlspecialchars($o['tipo']) ?></td>
                                        <td><?= htmlspecialchars($o['titulo'] ?? '') ?></td>
                                    </tr>
                                <?php endforeach; ?>
                                </tbody>
                            </table>
                        <?php endif; ?>

                        <?php if ($mppa['acoes']): ?>
                            <h5 class="mt-4">Ações do MPPA que mencionam este município <small class="text-muted">(Relatório de Atividades 2023)</small></h5>
                            <?php foreach ($mppa['acoes'] as $area => $itens): ?>
                                <h6 class="mt-3 text-success"><?= htmlspecialchars($area) ?></h6>
                                <ul class="list-group list-group-flush mb-2">
                                    <?php foreach ($itens as $item): ?>
                                        <li class="list-group-item px-0"><?= htmlspecialchars($item['resumo']) ?></li>
                                    <?php endforeach; ?>
                                </ul>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <p class="text-muted mt-3">Nenhuma ação específica deste município foi identificada no texto do relatório — isso não significa ausência de atuação do MPPA, apenas que o relatório não citou o município nominalmente.</p>
                        <?php endif; ?>

                        <p class="footer-note text-muted small mt-4">
                            Fonte: Relatório de Atividades do Ministério Público do Estado do Pará (MPPA), ano base 2023/2024, submetido à ALEPA.
                            As ações por município foram identificadas automaticamente a partir do texto do relatório e podem não ser exaustivas.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<script>
const chartPayload = <?= json_encode($chartPayload) ?>;
const chartsInitialized = new Set();

function initChartsIn(paneEl) {
    paneEl.querySelectorAll('canvas').forEach((canvas) => {
        if (chartsInitialized.has(canvas.id) || !chartPayload[canvas.id]) return;
        chartsInitialized.add(canvas.id);
        const cfg = chartPayload[canvas.id];
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: cfg.labels,
                datasets: [{
                    data: cfg.data,
                    borderColor: '#0b5d3b',
                    backgroundColor: 'rgba(11,93,59,0.12)',
                    fill: true,
                    tension: 0.25,
                    pointRadius: 2,
                }],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { x: { display: true }, y: { display: true } },
            },
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const primeiraAba = document.querySelector('.tab-pane.active');
    if (primeiraAba) initChartsIn(primeiraAba);

    document.querySelectorAll('#tabs-municipio a[data-toggle="pill"]').forEach((tabLink) => {
        tabLink.addEventListener('shown.bs.tab', (e) => {
            const alvo = document.querySelector(e.target.getAttribute('href'));
            if (alvo) initChartsIn(alvo);
        });
    });
});
</script>

<?php require __DIR__ . '/partials/footer.php'; ?>
</body>
</html>
