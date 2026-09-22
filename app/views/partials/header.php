<?php
/** @var string|null $pageTitle */
$pageTitle = $pageTitle ?? 'Anuário Estatístico e Político do Pará';
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($pageTitle) ?></title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.2/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/admin-lte/3.2.0/css/adminlte.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
    <link rel="stylesheet" href="assets/css/custom.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/4.6.2/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/admin-lte/3.2.0/js/adminlte.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.5.1/chart.umd.min.js"></script>
</head>
<body class="hold-transition sidebar-mini layout-fixed">
<div class="wrapper">

<nav class="main-header navbar navbar-expand navbar-dark" style="background:#0b5d3b;">
    <ul class="navbar-nav">
        <li class="nav-item">
            <a class="nav-link" data-widget="pushmenu" href="#" role="button"><i class="fas fa-bars"></i></a>
        </li>
        <li class="nav-item d-none d-sm-inline-block">
            <a href="index.php" class="nav-link">Início</a>
        </li>
    </ul>
    <ul class="navbar-nav ml-auto">
        <li class="nav-item">
            <span class="nav-link"><i class="fas fa-map-location-dot"></i> Estado do Pará &mdash; 144 municípios</span>
        </li>
    </ul>
</nav>

<aside class="main-sidebar sidebar-dark-success elevation-4">
    <a href="index.php" class="brand-link">
        <i class="fas fa-landmark-dome ml-2 mr-2"></i>
        <span class="brand-text font-weight-light">Anuário do Pará</span>
    </a>
    <div class="sidebar">
        <nav class="mt-2">
            <ul class="nav nav-pills nav-sidebar flex-column" role="menu">
                <li class="nav-item">
                    <a href="index.php" class="nav-link <?= ($page ?? '') === 'home' ? 'active' : '' ?>">
                        <i class="nav-icon fas fa-house"></i>
                        <p>Painel do Estado</p>
                    </a>
                </li>
                <li class="nav-header">MUNICÍPIO SELECIONADO</li>
                <?php if (!empty($municipio)): ?>
                <li class="nav-item">
                    <a href="index.php?page=municipio&codigo=<?= htmlspecialchars($municipio['ibge_code']) ?>" class="nav-link active">
                        <i class="nav-icon fas fa-city"></i>
                        <p><?= htmlspecialchars($municipio['nome']) ?></p>
                    </a>
                </li>
                <?php else: ?>
                <li class="nav-item">
                    <span class="nav-link text-muted"><small>Escolha uma cidade no mapa ou na busca</small></span>
                </li>
                <?php endif; ?>
                <li class="nav-header">TEMAS DO ANUÁRIO</li>
                <?php foreach (['Demografia' => 'people-group', 'Economia' => 'coins', 'Social' => 'hand-holding-heart',
                                'Território' => 'map', 'Meio Ambiente' => 'leaf', 'Infraestrutura' => 'road'] as $tema => $icon): ?>
                <li class="nav-item">
                    <a href="#tema-<?= strtolower(str_replace(' ', '-', $tema)) ?>" class="nav-link">
                        <i class="nav-icon fas fa-<?= $icon ?>"></i>
                        <p><?= $tema ?></p>
                    </a>
                </li>
                <?php endforeach; ?>
            </ul>
        </nav>
    </div>
</aside>

<div class="content-wrapper">
