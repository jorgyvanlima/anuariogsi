(function () {
    'use strict';

    function irParaMunicipio() {
        const input = document.getElementById('busca-municipio');
        const valor = (input.value || '').trim().toLowerCase();
        if (!valor) return;
        const opcoes = document.querySelectorAll('#lista-municipios option');
        for (const opt of opcoes) {
            if (opt.value.toLowerCase() === valor) {
                window.location.href = 'index.php?page=municipio&codigo=' + opt.dataset.codigo;
                return;
            }
        }
        alert('Município não encontrado. Selecione uma opção da lista.');
    }

    document.getElementById('btn-ir-municipio').addEventListener('click', irParaMunicipio);
    document.getElementById('busca-municipio').addEventListener('keydown', function (e) {
        if (e.key === 'Enter') irParaMunicipio();
    });

    // Mapa interativo (Leaflet, sem camada de tiles externa: só a malha do Pará)
    const map = L.map('mapa-pa', {
        zoomControl: true,
        attributionControl: false,
        scrollWheelZoom: false,
    });

    fetch(municipiosGeoUrl)
        .then((r) => r.json())
        .then((geojson) => {
            const layer = L.geoJSON(geojson, {
                style: () => ({
                    color: '#0b5d3b',
                    weight: 1,
                    fillColor: '#3fae6a',
                    fillOpacity: 0.55,
                }),
                onEachFeature: (feature, lyr) => {
                    const codigo = feature.properties.codarea;
                    const nome = municipiosPorCodigo[codigo] || codigo;
                    lyr.bindTooltip(nome, { sticky: true });
                    lyr.on({
                        mouseover: () => lyr.setStyle({ fillColor: '#f0ad4e', fillOpacity: 0.8 }),
                        mouseout: () => lyr.setStyle({ fillColor: '#3fae6a', fillOpacity: 0.55 }),
                        click: () => {
                            window.location.href = 'index.php?page=municipio&codigo=' + codigo;
                        },
                    });
                },
            }).addTo(map);
            map.fitBounds(layer.getBounds());
        });

    // Gráfico da população do Pará
    const ctx = document.getElementById('grafico-populacao-pa');
    if (ctx && populacaoSerie.length) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: populacaoSerie.map((r) => r.ano),
                datasets: [{
                    label: 'População do Pará',
                    data: populacaoSerie.map((r) => r.valor),
                    borderColor: '#0b5d3b',
                    backgroundColor: 'rgba(11,93,59,0.15)',
                    fill: true,
                    tension: 0.25,
                }],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { ticks: { callback: (v) => new Intl.NumberFormat('pt-BR').format(v) } } },
            },
        });
    }
})();
