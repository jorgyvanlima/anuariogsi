<?php
/** @var array $municipios */
/** @var int $totalMunicipios */
/** @var array $mapas */
/** @var array|null $populacao */
/** @var array|null $pib */
/** @var array|null $pibPerCapita */
/** @var array $populacaoSerie */
/** @var array $mppaEstado */
/** @var array $pcpaEstado */
$pageTitle = 'Anuário Estatístico e Político do Pará';
$page = 'home';
require __DIR__ . '/partials/header.php';

function fmt_num($v, $decimais = 0) {
    if ($v === null) return '—';
    return number_format((float) $v, $decimais, ',', '.');
}
?>

<section class="content-header">
    <div class="container-fluid">
        <div class="row mb-2">
            <div class="col-sm-8">
                <h1><i class="fas fa-map-location-dot"></i> Painel do Estado do Pará</h1>
                <p class="text-muted">Escolha um município no mapa ou pela busca para ver o perfil completo: demografia, economia, social, território, meio ambiente, infraestrutura, política, Ministério Público e Polícia Civil.</p>
            </div>
            <div class="col-sm-4">
                <div class="input-group mt-2">
                    <input type="text" id="busca-municipio" class="form-control" list="lista-municipios"
                           placeholder="Buscar município do Pará...">
                    <datalist id="lista-municipios">
                        <?php foreach ($municipios as $m): ?>
                            <option data-codigo="<?= htmlspecialchars($m['ibge_code']) ?>" value="<?= htmlspecialchars($m['nome']) ?>"></option>
                        <?php endforeach; ?>
                    </datalist>
                    <div class="input-group-append">
                        <button class="btn btn-success" id="btn-ir-municipio" type="button"><i class="fas fa-magnifying-glass"></i> Ir</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="content">
    <div class="container-fluid">

        <div class="row">
            <div class="col-lg-3 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3><?= fmt_num($totalMunicipios) ?></h3>
                        <p>Municípios do Pará</p>
                    </div>
                    <div class="icon"><i class="fas fa-city"></i></div>
                </div>
            </div>
            <div class="col-lg-3 col-6">
                <div class="small-box bg-info">
                    <div class="inner">
                        <h3><?= fmt_num($populacao['valor'] ?? null) ?></h3>
                        <p>População estimada (<?= htmlspecialchars((string)($populacao['ano'] ?? '—')) ?>)</p>
                    </div>
                    <div class="icon"><i class="fas fa-people-group"></i></div>
                </div>
            </div>
            <div class="col-lg-3 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3>R$ <?= fmt_num(($pib['valor'] ?? 0) / 1000000, 1) ?> bi</h3>
                        <p>PIB do Pará (<?= htmlspecialchars((string)($pib['ano'] ?? '—')) ?>)</p>
                    </div>
                    <div class="icon"><i class="fas fa-coins"></i></div>
                </div>
            </div>
            <div class="col-lg-3 col-6">
                <div class="small-box bg-secondary">
                    <div class="inner">
                        <h3>R$ <?= fmt_num($pibPerCapita['valor'] ?? null) ?></h3>
                        <p>PIB per capita (<?= htmlspecialchars((string)($pibPerCapita['ano'] ?? '—')) ?>)</p>
                    </div>
                    <div class="icon"><i class="fas fa-sack-dollar"></i></div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-8">
                <div class="card card-success card-outline">
                    <div class="card-header">
                        <h3 class="card-title"><i class="fas fa-map"></i> Mapa interativo &mdash; clique em um município</h3>
                    </div>
                    <div class="card-body p-0">
                        <div id="mapa-pa" style="height: 560px;"></div>
                    </div>
                    <div class="card-footer text-muted">
                        <small>Passe o mouse para ver o nome do município e clique para abrir o perfil completo.</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card card-info card-outline">
                    <div class="card-header">
                        <h3 class="card-title"><i class="fas fa-chart-line"></i> População do Pará</h3>
                    </div>
                    <div class="card-body">
                        <canvas id="grafico-populacao-pa" height="220"></canvas>
                    </div>
                </div>
                <div class="card card-outline card-secondary">
                    <div class="card-header">
                        <h3 class="card-title"><i class="fas fa-list"></i> Todos os municípios</h3>
                    </div>
                    <div class="card-body p-0" style="max-height: 260px; overflow-y: auto;">
                        <ul class="list-group list-group-flush">
                            <?php foreach ($municipios as $m): ?>
                                <a class="list-group-item list-group-item-action py-1"
                                   href="index.php?page=municipio&codigo=<?= htmlspecialchars($m['ibge_code']) ?>">
                                    <?= htmlspecialchars($m['nome']) ?>
                                    <small class="text-muted float-right"><?= htmlspecialchars($m['regiao_integracao'] ?? '') ?></small>
                                </a>
                            <?php endforeach; ?>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <div class="card card-outline card-primary">
            <div class="card-header">
                <h3 class="card-title"><i class="fas fa-images"></i> Mapas temáticos do Estado</h3>
            </div>
            <div class="card-body">
                <ul class="nav nav-tabs" id="tabs-mapas" role="tablist">
                    <?php $first = true; foreach ($mapas as $categoria => $itens): ?>
                        <li class="nav-item">
                            <a class="nav-link <?= $first ? 'active' : '' ?>" id="tab-<?= strtolower(str_replace(' ', '-', $categoria)) ?>"
                               data-toggle="tab" href="#painel-<?= strtolower(str_replace(' ', '-', $categoria)) ?>" role="tab">
                                <?= htmlspecialchars($categoria) ?>
                            </a>
                        </li>
                    <?php $first = false; endforeach; ?>
                    <li class="nav-item">
                        <a class="nav-link" id="tab-ministerio-publico" data-toggle="tab" href="#painel-ministerio-publico" role="tab">
                            <i class="fas fa-scale-balanced"></i> Ministério Público
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" id="tab-policia-civil" data-toggle="tab" href="#painel-policia-civil" role="tab">
                            <i class="fas fa-shield-halved"></i> Polícia Civil
                        </a>
                    </li>
                </ul>
                <div class="tab-content pt-3" id="tema-demografia">
                    <?php $first = true; foreach ($mapas as $categoria => $itens): ?>
                        <div class="tab-pane fade <?= $first ? 'show active' : '' ?>" id="painel-<?= strtolower(str_replace(' ', '-', $categoria)) ?>">
                            <div class="row">
                                <?php foreach ($itens as $mapa): ?>
                                    <div class="col-md-3 col-6 mb-3 text-center">
                                        <a href="assets/mapas/<?= htmlspecialchars($mapa['arquivo']) ?>" target="_blank">
                                            <img src="assets/mapas/<?= htmlspecialchars($mapa['arquivo']) ?>" class="img-fluid img-thumbnail" loading="lazy">
                                        </a>
                                        <p class="small mt-1 mb-0"><?= htmlspecialchars($mapa['titulo']) ?></p>
                                    </div>
                                <?php endforeach; ?>
                            </div>
                        </div>
                    <?php $first = false; endforeach; ?>

                    <div class="tab-pane fade" id="painel-ministerio-publico">
                        <p class="text-muted">Ministério Público do Estado do Pará (MPPA) — dados do Relatório de Atividades, ano base 2023/2024, submetido à ALEPA.</p>

                        <?php foreach ($mppaEstado['indicadores'] as $categoria => $itens): ?>
                            <h5 class="mt-3 border-bottom pb-1"><?= htmlspecialchars($categoria) ?></h5>
                            <div class="row">
                                <?php foreach ($itens as $ind): ?>
                                    <?php
                                        $unidade = $ind['unidade'] ?? '';
                                        $decimais = $unidade === '%' ? 2 : ($unidade === 'R$' ? 0 : 0);
                                        $valorFmt = ($unidade === 'R$' ? 'R$ ' : '') . fmt_num($ind['valor'], $decimais);
                                    ?>
                                    <div class="col-md-4 col-sm-6 mb-3">
                                        <div class="stat-card">
                                            <div class="rotulo"><?= htmlspecialchars($ind['indicador']) ?></div>
                                            <div class="valor">
                                                <?= $valorFmt ?>
                                                <?php if ($unidade && $unidade !== 'R$'): ?><small class="text-muted"><?= htmlspecialchars($unidade) ?></small><?php endif; ?>
                                                <small class="text-muted">(<?= htmlspecialchars((string)$ind['ano']) ?>)</small>
                                            </div>
                                        </div>
                                    </div>
                                <?php endforeach; ?>
                            </div>
                        <?php endforeach; ?>

                        <?php if ($mppaEstado['obras']): ?>
                            <h5 class="mt-4 border-bottom pb-1">Sedes, obras e reformas por tipo</h5>
                            <?php foreach ($mppaEstado['obras'] as $tipo => $itens): ?>
                                <button class="btn btn-sm btn-outline-secondary mt-2 mr-1" type="button" data-toggle="collapse"
                                        data-target="#obras-<?= md5($tipo) ?>">
                                    <i class="fas fa-chevron-down"></i> <?= htmlspecialchars($tipo) ?> (<?= count($itens) ?>)
                                </button>
                                <div class="collapse mt-2" id="obras-<?= md5($tipo) ?>">
                                    <p class="small">
                                        <?php foreach ($itens as $i => $o): ?>
                                            <a href="index.php?page=municipio&codigo=<?= htmlspecialchars($o['ibge_code']) ?>"><?= htmlspecialchars($o['municipio_nome']) ?></a><?= $o['titulo'] ? ' (' . htmlspecialchars($o['titulo']) . ')' : '' ?><?= $i < count($itens) - 1 ? ', ' : '' ?>
                                        <?php endforeach; ?>
                                    </p>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>

                        <?php if ($mppaEstado['acoes']): ?>
                            <h5 class="mt-4 border-bottom pb-1">Ações finalísticas por área <small class="text-muted">(âmbito estadual)</small></h5>
                            <?php foreach ($mppaEstado['acoes'] as $area => $itens): ?>
                                <button class="btn btn-sm btn-outline-success mt-2 mr-1" type="button" data-toggle="collapse"
                                        data-target="#acoes-<?= md5($area) ?>">
                                    <i class="fas fa-chevron-down"></i> <?= htmlspecialchars($area) ?> (<?= count($itens) ?>)
                                </button>
                                <div class="collapse mt-2" id="acoes-<?= md5($area) ?>">
                                    <ul class="list-group list-group-flush mb-2">
                                        <?php foreach ($itens as $item): ?>
                                            <li class="list-group-item px-0 small"><?= htmlspecialchars($item['resumo']) ?></li>
                                        <?php endforeach; ?>
                                    </ul>
                                </div>
                            <?php endforeach; ?>
                        <?php endif; ?>

                        <p class="footer-note text-muted small mt-4">
                            Fonte: Relatório de Atividades do Ministério Público do Estado do Pará (MPPA), ano base 2023/2024, submetido à ALEPA.
                        </p>
                    </div>

                    <div class="tab-pane fade" id="painel-policia-civil">
                        <p class="text-muted">Polícia Civil do Estado do Pará (PCPA) — Unidades Policiais (pc.pa.gov.br/delegacias).</p>

                        <?php foreach ($pcpaEstado as $tipo => $itens): ?>
                            <button class="btn btn-sm btn-outline-secondary mt-2 mr-1" type="button" data-toggle="collapse"
                                    data-target="#pcpa-<?= md5($tipo) ?>">
                                <i class="fas fa-chevron-down"></i> <?= htmlspecialchars($tipo) ?> (<?= count($itens) ?>)
                            </button>
                            <div class="collapse mt-2" id="pcpa-<?= md5($tipo) ?>">
                                <?php foreach ($itens as $u): ?>
                                    <div class="card card-outline card-secondary mb-2">
                                        <div class="card-body py-2">
                                            <h6 class="mb-1">
                                                <?= htmlspecialchars($u['nome']) ?>
                                                <?php if ($u['ibge_code']): ?>
                                                    <a class="small" href="index.php?page=municipio&codigo=<?= htmlspecialchars($u['ibge_code']) ?>">(<?= htmlspecialchars($u['municipio_nome']) ?>)</a>
                                                <?php endif; ?>
                                            </h6>
                                            <?php if ($u['endereco']): ?>
                                                <p class="mb-1 small"><i class="fas fa-location-dot"></i>
                                                    <?= htmlspecialchars($u['endereco']) ?><?= $u['bairro'] ? ' — ' . htmlspecialchars($u['bairro']) : '' ?>
                                                </p>
                                            <?php endif; ?>
                                            <?php if ($u['telefone']): ?>
                                                <p class="mb-1 small"><i class="fas fa-phone"></i> <?= htmlspecialchars($u['telefone']) ?></p>
                                            <?php endif; ?>
                                            <?php if ($u['funcionamento']): ?>
                                                <p class="mb-0 small text-muted"><i class="fas fa-clock"></i> <?= htmlspecialchars($u['funcionamento']) ?></p>
                                            <?php endif; ?>
                                        </div>
                                    </div>
                                <?php endforeach; ?>
                            </div>
                        <?php endforeach; ?>

                        <p class="footer-note text-muted small mt-4">
                            Fonte: Polícia Civil do Estado do Pará — Unidades Policiais (pc.pa.gov.br/delegacias).
                            Dados extraídos automaticamente por OCR e podem conter pequenas imprecisões.
                        </p>
                    </div>
                </div>
            </div>
        </div>

    </div>
</section>

<script>
const municipiosGeoUrl = 'assets/geo/pa_municipios.geojson';
const populacaoSerie = <?= json_encode($populacaoSerie) ?>;
const municipiosPorCodigo = <?= json_encode(array_column($municipios, 'nome', 'ibge_code')) ?>;
</script>
<script src="assets/js/home.js"></script>

<?php require __DIR__ . '/partials/footer.php'; ?>
</body>
</html>
