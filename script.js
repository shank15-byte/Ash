const state = { regions: [], selected: null, charts: {} };
const $ = (selector) => document.querySelector(selector);

function fmt(value) { return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value); }
function setSliderLabels() { $('#areaOutput').textContent = `${fmt($('#area').value)} ha`; $('#yearsOutput').textContent = `${$('#years').value} years`; $('#previewYears').textContent = `${$('#years').value} years`; }
['area','years'].forEach(id => $(`#${id}`).addEventListener('input', setSliderLabels));

async function loadRegions() {
  const response = await fetch('/api/regions'); state.regions = await response.json();
  const map = L.map('map', { zoomControl: false, scrollWheelZoom: false }).setView([10, 11], 2);
  L.control.zoom({ position: 'bottomright' }).addTo(map);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; OpenStreetMap &copy; CARTO', subdomains: 'abcd', maxZoom: 19 }).addTo(map);
  state.regions.forEach(region => {
    const color = region.degradation_percentage >= 65 ? '#e1bd58' : '#68c474';
    L.circleMarker([region.lat, region.lng], { radius: 8 + region.degradation_percentage / 18, color, weight: 1, fillColor: color, fillOpacity: .65 })
      .addTo(map).bindPopup(`<b>${region.name}</b><br>${region.degradation_percentage}% degradation`) .on('click', () => selectRegion(region, map));
  });
  selectRegion(state.regions[0], map, false);
}
function selectRegion(region, map, fly = true) {
  state.selected = region; if (fly) map.flyTo([region.lat, region.lng], 5, { duration: 1.1 });
  $('#previewRegion').textContent = region.name;
  $('#regionPanel').innerHTML = `<p class="eyebrow">Selected landscape</p><h3 class="region-name">${region.name}</h3><p class="region-location">${region.lat.toFixed(2)}°, ${region.lng.toFixed(2)}°</p><div class="region-grid"><div class="region-stat"><small>Degradation</small><strong>${region.degradation_percentage}%</strong></div><div class="region-stat"><small>Tree cover</small><strong>${region.current_tree_cover}%</strong></div><div class="region-stat"><small>Biodiversity</small><strong>${region.biodiversity_score}/100</strong></div><div class="region-stat"><small>Water access</small><strong>${region.water_availability}%</strong></div></div><button class="region-select" id="useRegion">Use in my scenario →</button>`;
  $('#useRegion').addEventListener('click', () => $('#simulator').scrollIntoView({ behavior: 'smooth' }));
}

function buildChart(id, labels, datasets, options = {}) {
  if (state.charts[id]) state.charts[id].destroy();
  state.charts[id] = new Chart($(`#${id}`), { type: 'line', data: { labels, datasets }, options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { labels: { color: '#aac3af', boxWidth: 8, usePointStyle: true, font: { size: 10 } } } }, scales: { x: { ticks: { color: '#74907c', font: { size: 9 }, maxTicksLimit: 7 }, grid: { color: '#ffffff09' } }, y: { ticks: { color: '#74907c', font: { size: 9 } }, grid: { color: '#ffffff09' }, beginAtZero: true }, ...options.scales } } });
}
const line = (label, data, color, yAxisID = 'y') => ({ label, data, borderColor: color, backgroundColor: `${color}22`, yAxisID, tension: .38, fill: true, pointRadius: 0, borderWidth: 2 });
function renderResults(data) {
  const final = data.summary; const set = (id, value) => { const el = $(`#${id}`); el.textContent = value; el.parentElement.animate([{transform:'translateY(6px)',opacity:.5},{transform:'translateY(0)',opacity:1}], {duration:450}); };
  set('treeMetric', `${final.tree_cover}%`); set('carbonMetric', `${fmt(final.carbon_sequestered)} t`); set('bioMetric', `${final.biodiversity_index}/100`); set('waterMetric', `${final.water_availability}%`); set('tempMetric', `−${final.temperature_reduction}°C`); set('costMetric', `$${fmt(final.total_cost)}`);
  const labels = data.timeline.years.map(y => `Y${y}`);
  buildChart('treeCarbonChart', labels, [line('Tree cover (%)', data.timeline.tree_cover, '#9ee66c'), line('Carbon (tCO₂)', data.timeline.carbon, '#61d5c6', 'y1')], { scales: { y: { ticks:{color:'#74907c',font:{size:9}}, grid:{color:'#ffffff09'}, min: 0, max:100 }, y1: { position:'right', ticks:{color:'#74907c',font:{size:9},callback:v=>`${Math.round(v/1000)}k`}, grid:{drawOnChartArea:false}, beginAtZero:true }, x:{ticks:{color:'#74907c',font:{size:9},maxTicksLimit:7},grid:{color:'#ffffff09'}} } });
  buildChart('bioWaterChart', labels, [line('Biodiversity', data.timeline.biodiversity, '#e9c66e'), line('Water access (%)', data.timeline.water, '#66d9d2', 'y1')], { scales: { y:{min:0,max:100,ticks:{color:'#74907c',font:{size:9}},grid:{color:'#ffffff09'}}, y1:{position:'right',min:0,max:100,ticks:{color:'#74907c',font:{size:9}},grid:{drawOnChartArea:false}},x:{ticks:{color:'#74907c',font:{size:9},maxTicksLimit:7},grid:{color:'#ffffff09'}} } });
  buildChart('tempChart', labels, [line('Cooling (°C)', data.timeline.temperature, '#d3b1ee')], { scales: { y:{ticks:{color:'#74907c',font:{size:9},callback:v=>`${v}°`},grid:{color:'#ffffff09'},beginAtZero:true},x:{ticks:{color:'#74907c',font:{size:9},maxTicksLimit:7},grid:{color:'#ffffff09'}} } });
  $('#riskBars').innerHTML = Object.entries(data.risks).map(([name, r]) => `<div class="risk-row"><span class="risk-name">${name}</span><div class="risk-track"><i class="risk-current" style="width:${r.current}%"></i></div><div class="risk-track"><i class="risk-projected" style="width:${r.projected}%"></i></div><span class="risk-reduction">−${r.reduction}%</span></div>`).join('');
  $('#costTotal').textContent = `$${fmt(final.total_cost)}`;
  $('#costBreakdown').innerHTML = Object.entries(data.cost_breakdown).map(([key, value]) => `<div class="cost-line"><span>${key}</span><strong>$${fmt(value)}</strong></div>`).join('');
  $('#resultStatus').textContent = `${state.selected.name} · ${data.input.years}-year ${data.input.strategy.replace('_',' ')} pathway`;
  $('#results').classList.remove('hidden'); setTimeout(() => $('#insights').scrollIntoView({ behavior:'smooth', block:'start' }), 150);
}
$('#simulationForm').addEventListener('submit', async event => { event.preventDefault(); const button = $('.run-button'); button.classList.add('loading'); button.querySelector('.button-text').textContent = 'Calculating pulse…';
  const payload = { area_hectares: +$('#area').value, strategy: $('#strategy').value, soil_type: $('#soil').value, latitude: state.selected?.lat ?? 0, longitude: state.selected?.lng ?? 0, years: +$('#years').value };
  try { const response = await fetch('/api/simulate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }); if (!response.ok) throw new Error('Simulation unavailable'); renderResults(await response.json()); } catch (error) { $('#resultStatus').textContent = 'Unable to run the simulation. Please check the server and try again.'; } finally { button.classList.remove('loading'); button.querySelector('.button-text').textContent = 'Run simulation'; }
});
loadRegions().catch(() => { $('#regionPanel').innerHTML = '<p class="eyebrow">Connection needed</p><p class="empty-region">Start the Flask server to load regional data.</p>'; }); setSliderLabels();
