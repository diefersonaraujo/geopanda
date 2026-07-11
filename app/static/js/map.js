/**
 * GeoPanda SIG — Mapa Leaflet.js
 * Gerencia camadas, filtros e interações no mapa.
 */

let map;
let currentLayers = {};
let baseLayer;
let stateData = [];

const LAYER_COLORS = {
    regioes: '#e94560',
    estados: '#533483',
    mesorregioes: '#0f3460',
    microrregioes: '#1a8a5c',
    municipios: '#e9a045',
    setores_censitarios: '#45a0e9',
};

const LAYER_NAMES = {
    regioes: 'Regiões',
    estados: 'Estados',
    mesorregioes: 'Mesorregiões',
    microrregioes: 'Microrregiões',
    municipios: 'Municípios',
    setores_censitarios: 'Setores Censitários',
};

function initMap() {
    map = L.map('map', {
        center: [-14.235, -51.925],
        zoom: 4,
        zoomControl: true,
        maxZoom: 18,
        minZoom: 2,
    });

    baseLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19,
    }).addTo(map);

    loadLayerControls();
    loadStates();
    loadDefaultLayers();
}

function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

async function fetchJSON(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
}

function getGeoJsonStyle(layerName, feature) {
    const color = LAYER_COLORS[layerName] || '#e94560';
    const opacity = parseFloat(document.getElementById('opacity-slider').value);
    const theme = document.getElementById('theme-select').value;

    let fillColor = color;
    let weight = 1.5;
    let fillOpacity = opacity * 0.5;

    if (layerName === 'setores_censitarios') {
        weight = 0.5;
        fillOpacity = opacity * 0.4;
    }

    if (theme === 'populacao' && feature.properties?.populacao) {
        const pop = feature.properties.populacao;
        if (pop > 1000000) fillColor = '#e94560';
        else if (pop > 100000) fillColor = '#e9a045';
        else if (pop > 10000) fillColor = '#45a0e9';
        else fillColor = '#1a8a5c';
        fillOpacity = opacity * 0.7;
    }

    if (theme === 'area' && feature.properties?.area_km2) {
        const area = feature.properties.area_km2;
        if (area > 100000) fillColor = '#e94560';
        else if (area > 10000) fillColor = '#e9a045';
        else if (area > 1000) fillColor = '#45a0e9';
        else fillColor = '#1a8a5c';
        fillOpacity = opacity * 0.7;
    }

    return {
        color: fillColor,
        weight: weight,
        opacity: opacity,
        fillOpacity: fillOpacity,
        fillColor: fillColor,
    };
}

function formatNumber(num) {
    if (num === null || num === undefined) return '—';
    return num.toLocaleString('pt-BR');
}

function buildPopupContent(layerName, props) {
    let html = `<strong>${LAYER_NAMES[layerName] || layerName}</strong><br/>`;
    if (props.nome) html += `<b>${props.nome}</b><br/>`;
    if (props.uf) html += `UF: ${props.uf}<br/>`;
    if (props.codigo_ibge) html += `Código IBGE: ${props.codigo_ibge}<br/>`;
    if (props.populacao) html += `População: ${formatNumber(props.populacao)}<br/>`;
    if (props.area_km2) html += `Área: ${formatNumber(props.area_km2)} km²<br/>`;
    if (props.ddd) html += `DDD: ${props.ddd}<br/>`;
    if (props.domicilios) html += `Domicílios: ${formatNumber(props.domicilios)}<br/>`;
    return html;
}

async function loadLayer(layerName, visible = false) {
    try {
        const data = await fetchJSON(`/api/geojson/${layerName}?limit=10000`);

        if (currentLayers[layerName]) {
            map.removeLayer(currentLayers[layerName]);
        }

        const layer = L.geoJSON(data, {
            style: (feature) => getGeoJsonStyle(layerName, feature),
            onEachFeature: (feature, l) => {
                const popupHtml = buildPopupContent(layerName, feature.properties);
                l.bindPopup(popupHtml);
                l.on('click', () => showFeatureInfo(feature.properties, layerName));
                l.on('mouseover', function () {
                    this.setStyle({ weight: 3, fillOpacity: 0.8 });
                    this.bringToFront();
                });
                l.on('mouseout', function () {
                    layer.resetStyle(this);
                });
            },
        });

        currentLayers[layerName] = layer;
        if (visible) layer.addTo(map);

        updateLayerCount(layerName, data.features.length);
    } catch (err) {
        console.error(`Erro ao carregar camada ${layerName}:`, err);
    }
}

function updateLayerCount(layerName, count) {
    const el = document.querySelector(`#layer-${layerName} .layer-count`);
    if (el) el.textContent = `${count} feições`;
}

function showFeatureInfo(properties, layerName) {
    const infoPanel = document.getElementById('feature-info');
    const details = document.getElementById('feature-details');

    let html = '';
    for (const [key, value] of Object.entries(properties)) {
        if (value === null || value === undefined) continue;
        let displayValue = value;
        if (typeof value === 'number' && key !== 'ddd' && key !== 'codigo_ibge') {
            displayValue = formatNumber(value);
        }
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `<div class="prop-row"><span class="prop-key">${label}</span><span class="prop-value">${displayValue}</span></div>`;
    }

    details.innerHTML = html;
    infoPanel.style.display = 'block';
}

async function loadLayerControls() {
    try {
        const data = await fetchJSON('/api/layers');
        const container = document.getElementById('layer-controls');

        container.innerHTML = '';

        data.layers.forEach(layer => {
            const div = document.createElement('div');
            div.className = 'layer-toggle';
            div.id = `layer-${layer.id}`;

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `check-${layer.id}`;
            checkbox.checked = layer.id === 'estados';
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    loadLayer(layer.id, true);
                } else if (currentLayers[layer.id]) {
                    map.removeLayer(currentLayers[layer.id]);
                    delete currentLayers[layer.id];
                }
            });

            const nameSpan = document.createElement('span');
            nameSpan.className = 'layer-name';
            nameSpan.textContent = LAYER_NAMES[layer.id] || layer.id;

            const countSpan = document.createElement('span');
            countSpan.className = 'layer-count';
            countSpan.textContent = `${layer.total_features} feições`;

            div.appendChild(checkbox);
            div.appendChild(nameSpan);
            div.appendChild(countSpan);
            container.appendChild(div);
        });
    } catch (err) {
        console.error('Erro ao carregar camadas:', err);
        const container = document.getElementById('layer-controls');
        const fallback = ['regioes', 'estados', 'municipios', 'setores_censitarios'];
        fallback.forEach(id => {
            const div = document.createElement('div');
            div.className = 'layer-toggle';
            div.id = `layer-${id}`;

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `check-${id}`;
            checkbox.checked = id === 'estados';
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) loadLayer(id, true);
                else if (currentLayers[id]) {
                    map.removeLayer(currentLayers[id]);
                    delete currentLayers[id];
                }
            });

            const nameSpan = document.createElement('span');
            nameSpan.className = 'layer-name';
            nameSpan.textContent = LAYER_NAMES[id] || id;

            const countSpan = document.createElement('span');
            countSpan.className = 'layer-count';

            div.appendChild(checkbox);
            div.appendChild(nameSpan);
            div.appendChild(countSpan);
            container.appendChild(div);
        });
    }
}

async function loadStates() {
    try {
        const data = await fetchJSON('/api/states');
        stateData = data.states;
        const select = document.getElementById('state-filter');
        select.innerHTML = '<option value="">Todos</option>';
        data.states.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.codigo_ibge;
            opt.textContent = `${s.nome} (${s.uf})`;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Erro ao carregar estados:', err);
    }
}

async function loadDefaultLayers() {
    showLoading();
    await loadLayer('estados', true);
    hideLoading();
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('state-filter').addEventListener('change', async (e) => {
        const stateCode = e.target.value;
        showLoading();

        if (currentLayers['municipios']) {
            map.removeLayer(currentLayers['municipios']);
            delete currentLayers['municipios'];
        }
        if (currentLayers['setores_censitarios']) {
            map.removeLayer(currentLayers['setores_censitarios']);
            delete currentLayers['setores_censitarios'];
        }

        if (stateCode) {
            const municipioCheck = document.getElementById('check-municipios');
            if (municipioCheck) municipioCheck.checked = true;
            await loadLayerFiltered('municipios', stateCode);
        } else {
            const municipioCheck = document.getElementById('check-municipios');
            if (municipioCheck) municipioCheck.checked = false;
        }

        hideLoading();
    });

    document.getElementById('search-btn').addEventListener('click', searchMunicipio);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchMunicipio();
    });

    document.getElementById('opacity-slider').addEventListener('input', () => {
        for (const [name, layer] of Object.entries(currentLayers)) {
            layer.eachLayer(l => {
                if (l.setStyle) {
                    const opacity = parseFloat(document.getElementById('opacity-slider').value);
                    l.setStyle({ opacity: opacity, fillOpacity: opacity * 0.5 });
                }
            });
        }
    });

    document.getElementById('theme-select').addEventListener('change', () => {
        for (const [name, layer] of Object.entries(currentLayers)) {
            layer.eachLayer(l => {
                if (l.setStyle) {
                    const style = getGeoJsonStyle(name, l.feature);
                    l.setStyle(style);
                }
            });
        }
    });
});

async function loadLayerFiltered(layerName, stateCode) {
    try {
        const data = await fetchJSON(`/api/geojson/${layerName}?uf=${stateCode}&limit=10000`);

        if (currentLayers[layerName]) {
            map.removeLayer(currentLayers[layerName]);
        }

        const layer = L.geoJSON(data, {
            style: (feature) => getGeoJsonStyle(layerName, feature),
            onEachFeature: (feature, l) => {
                const popupHtml = buildPopupContent(layerName, feature.properties);
                l.bindPopup(popupHtml);
                l.on('click', () => showFeatureInfo(feature.properties, layerName));
                l.on('mouseover', function () {
                    this.setStyle({ weight: 3, fillOpacity: 0.8 });
                    this.bringToFront();
                });
                l.on('mouseout', function () {
                    layer.resetStyle(this);
                });
            },
        }).addTo(map);

        currentLayers[layerName] = layer;
        updateLayerCount(layerName, data.features.length);

        if (data.features.length > 0) {
            const bounds = layer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds, { padding: [20, 20] });
        }
    } catch (err) {
        console.error(`Erro ao carregar ${layerName} filtrado:`, err);
    }
}

async function searchMunicipio() {
    const query = document.getElementById('search-input').value.trim();
    if (query.length < 2) return;

    showLoading();
    try {
        const data = await fetchJSON(`/api/ibge/buscar?q=${encodeURIComponent(query)}&limit=20`);

        if (currentLayers['search-results']) {
            map.removeLayer(currentLayers['search-results']);
        }

        if (data.features.length === 0) {
            alert('Nenhum município encontrado.');
            hideLoading();
            return;
        }

        const layer = L.geoJSON(data, {
            style: () => ({
                color: '#e94560',
                weight: 3,
                fillOpacity: 0.3,
                dashArray: '5, 10',
            }),
            onEachFeature: (feature, l) => {
                const popupHtml = buildPopupContent('municipios', feature.properties);
                l.bindPopup(popupHtml);
                l.on('click', () => showFeatureInfo(feature.properties, 'municipios'));
            },
        }).addTo(map);

        currentLayers['search-results'] = layer;

        if (data.features.length === 1) {
            const coords = data.features[0].geometry.coordinates;
            if (coords) {
                const flatCoords = coords.flat(3);
                const lats = [], lons = [];
                for (let i = 0; i < flatCoords.length; i += 2) {
                    lons.push(flatCoords[i]);
                    lats.push(flatCoords[i + 1]);
                }
                const bounds = L.latLngBounds(
                    [Math.min(...lats), Math.min(...lons)],
                    [Math.max(...lats), Math.max(...lons)]
                );
                map.fitBounds(bounds, { padding: [30, 30] });
            }
        } else {
            const bounds = layer.getBounds();
            if (bounds.isValid()) map.fitBounds(bounds, { padding: [30, 30] });
        }
    } catch (err) {
        console.error('Erro na busca:', err);
        alert('Erro ao buscar município.');
    }
    hideLoading();
}
