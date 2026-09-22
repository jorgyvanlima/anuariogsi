<?php
declare(strict_types=1);

require_once __DIR__ . '/../src/Database.php';
require_once __DIR__ . '/../src/Repository/MunicipioRepository.php';
require_once __DIR__ . '/../src/Repository/IndicadorRepository.php';
require_once __DIR__ . '/../src/Repository/CandidatoRepository.php';
require_once __DIR__ . '/../src/Repository/MapaRepository.php';
require_once __DIR__ . '/../vendor/autoload.php';

$page = $_GET['page'] ?? 'home';

try {
    switch ($page) {
        case 'municipio':
            $codigo = $_GET['codigo'] ?? '';
            $municipio = $codigo !== '' ? MunicipioRepository::find($codigo) : null;
            if (!$municipio) {
                http_response_code(404);
                echo "Município não encontrado.";
                break;
            }
            $indicadores = IndicadorRepository::agrupadosPorMunicipio($codigo);
            $politica = CandidatoRepository::politicaDoMunicipio($codigo);

            if (($_GET['export'] ?? '') === 'pdf') {
                require __DIR__ . '/../views/municipio_pdf.php';
            } else {
                require __DIR__ . '/../views/municipio.php';
            }
            break;

        case 'home':
        default:
            $municipios = MunicipioRepository::all();
            $totalMunicipios = MunicipioRepository::count();
            $mapas = MapaRepository::agrupadosPorCategoria();
            $populacao = IndicadorRepository::estadoUltimoValor('População Total do Pará');
            $pib = IndicadorRepository::estadoUltimoValor('Produto Interno Bruto a Preços Correntes');
            $pibPerCapita = IndicadorRepository::estadoUltimoValor('Produto Interno Bruto per Capita');
            $populacaoSerie = IndicadorRepository::estadoSerie('População Total do Pará');
            require __DIR__ . '/../views/home.php';
            break;
    }
} catch (Throwable $e) {
    http_response_code(500);
    echo '<pre>Erro: ' . htmlspecialchars($e->getMessage()) . "\n" . htmlspecialchars($e->getTraceAsString()) . '</pre>';
}
