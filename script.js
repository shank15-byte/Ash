const $ = (id) => document.getElementById(id);
let dashboard;
const fmt = (n) => n >= 1e6 ? `${(n / 1e6).toFixed(2)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : `${n}`;

function toast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 4200); }
function escapeHtml(value) { const el = document.createElement('div'); el.textContent = value; return el.innerHTML; }
function cloud(id, values) { $(id).innerHTML = values.map((word, index) => `<span style="font-size:${11 + index * 2}px">${escapeHtml(word)}</span>`).join(''); }

function render(data) {
  dashboard = data;
  const { channel, metrics, sentiment } = data;
  $('channelName').textContent = channel.name;
  $('channelHandle').textContent = `${channel.handle || 'Public channel'} · Last ${data.videos.length} videos`;
  $('sourceLabel').textContent = data.source === 'live' ? 'LIVE DATA' : 'DEMO MODE';
  $('totalViews').textContent = fmt(metrics.views); $('subscribers').textContent = fmt(metrics.subscribers); $('avgViews').textContent = fmt(metrics.avgViews); $('engagement').textContent = `${metrics.engagement}%`;
  $('positive').textContent = `${sentiment.positive}%`; $('neutral').textContent = `${sentiment.neutral}%`; $('negative').textContent = `${sentiment.negative}%`; $('sentimentPct').textContent = `${sentiment.positive}%`;
  $('donut').style.background = `conic-gradient(#10b981 0 ${sentiment.positive}%,#758196 ${sentiment.positive}% ${sentiment.positive + sentiment.neutral}%,#f45a6b ${sentiment.positive + sentiment.neutral}% 100%)`;
  cloud('positiveCloud', data.wordCloud.positive); cloud('negativeCloud', data.wordCloud.negative);
  const badge = { positive: ['#72e5bd', '#143b32'], negative: ['#ff98a5', '#3a2029'], neutral: ['#b1bfd1', '#273244'] };
  $('commentFeed').innerHTML = (data.comments || []).map((comment) => { const colors = badge[comment.sentiment] || badge.neutral; return `<div style="display:flex;align-items:center;gap:8px;border-top:1px solid #1b2637;padding:7px 0;font-size:10px;color:#aebbd0"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(comment.text)}</span><b style="margin-left:auto;text-transform:uppercase;font:8px 'DM Mono';letter-spacing:.5px;padding:3px 5px;border-radius:3px;color:${colors[0]};background:${colors[1]}">${comment.sentiment}</b></div>`; }).join('') || '<p style="font-size:10px;color:#7688a4">No public comments were available for these videos.</p>';
  $('trendGraph').innerHTML = data.trend.map((point) => `<div class="bar" title="${escapeHtml(point.name)}: ${point.score}%" style="height:${Math.max(7, point.score - 35)}%"></div>`).join('');
  $('gapRows').innerHTML = data.gaps.map((gap) => `<div class="gap-row"><span>${escapeHtml(gap.topic)}</span><span>${gap.volume}</span><b class="opp">${gap.opportunity}</b></div>`).join('');
  $('prescriptionRows').innerHTML = data.prescriptions.map((item) => `<div class="prescription"><span class="priority ${item.priority}">${item.priority}</span><div><b>${escapeHtml(item.title)}</b><p>${escapeHtml(item.detail)}</p></div></div>`).join('');
  if (data.notice) toast(data.notice);
}

async function callPrediction(payload) {
  const response = await fetch('/api/predict', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!response.ok) { const data = await response.json().catch(() => ({})); throw new Error(data.error || 'Prediction request failed'); }
  return response.json();
}

function channelBaseline() { return { channelEngagement: dashboard?.metrics.engagement || 6.2, channelAvgViews: dashboard?.metrics.avgViews || 46500 }; }

async function analyze(channel = '') {
  const btn = $('analyzeBtn'); btn.disabled = true; btn.textContent = 'Analyzing...'; $('analysisHint').textContent = 'Pulling channel videos, metrics and audience signals...';
  try { const response = await fetch('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channel }) }); if (!response.ok) throw new Error(); render(await response.json()); }
  catch { toast('Could not reach the analysis service. Please try again.'); }
  finally { btn.disabled = false; btn.innerHTML = 'Analyze <span>-&gt;</span>'; $('analysisHint').textContent = dashboard?.source === 'live' ? 'Live data successfully analyzed.' : 'Live YouTube analysis when your API key is connected.'; }
}

$('analyzeForm').addEventListener('submit', (event) => { event.preventDefault(); analyze($('channelInput').value.trim()); });
$('demoBtn').onclick = () => { $('channelInput').value = ''; analyze(''); };
$('gapBtn').onclick = () => { if (!dashboard) return; const btn = $('gapBtn'); btn.textContent = 'Scanning...'; setTimeout(() => { render(dashboard); btn.textContent = 'Refresh scan'; toast('Competitor topics refreshed from the current analysis.'); }, 600); };

$('preProductionForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const btn = $('diagnoseBtn'); btn.textContent = 'Analyzing your idea...'; btn.disabled = true;
  try {
    const result = await callPrediction({ title: $('preVideoTitle').value.trim(), length: $('preLength').value, category: $('preCategory').value, thumbnail: $('preThumbnail').value, hook: $('preHook').value, cta: $('preCta').value, ...channelBaseline() });
    $('preSummary').textContent = result.summary; $('preViews').textContent = fmt(result.views48); $('preEngagement').textContent = `${result.engagement}%`; $('preLift').textContent = `${result.uplift >= 0 ? '+' : ''}${result.uplift}%`; $('preConfidence').textContent = `${result.confidence}%`;
    $('preRecommendations').innerHTML = result.recommendations.map((item) => `<li>${escapeHtml(item)}</li>`).join(''); $('preResults').classList.remove('hidden'); $('preResults').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (error) { toast(error.message || 'Prediction service unavailable. Please try again.'); }
  finally { btn.textContent = 'DIAGNOSE VIDEO'; btn.disabled = false; }
});

$('predictBtn').onclick = async () => {
  const title = $('videoTitle').value.trim(); if (!title) { toast('Add a working video title to run the prediction.'); $('videoTitle').focus(); return; }
  const btn = $('predictBtn'); btn.textContent = 'Modeling...'; btn.disabled = true;
  try { const result = await callPrediction({ title, length: $('videoLength').value, ...channelBaseline() }); $('prediction').innerHTML = `<span>PREDICTED ENGAGEMENT</span><strong>${result.engagement}%</strong><p>vs. your channel average: ${dashboard?.metrics.engagement || 6.2}% · ${result.uplift >= 0 ? '+' : ''}${result.uplift}% potential lift</p><div class="confidence"><i style="background:linear-gradient(90deg,#29d39d ${result.confidence}%,#26354c ${result.confidence}%)"></i><span>Confidence score</span><b>${result.confidence}%</b></div>`; $('upliftPreview').textContent = `${result.uplift >= 0 ? '+' : ''}${result.uplift}%`; }
  catch (error) { toast(error.message || 'Prediction service unavailable. Please try again.'); }
  finally { btn.textContent = 'Predict engagement'; btn.disabled = false; }
};

analyze('');
