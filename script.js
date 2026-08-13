const $ = (id) => document.getElementById(id);
let dashboard;
const fmt = (n) => n >= 1e6 ? `${(n / 1e6).toFixed(2)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : n;
function toast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 4200); }
function cloud(id, values) { $(id).innerHTML = values.map((word, index) => `<span style="font-size:${11 + index * 2}px">${word}</span>`).join(''); }
function escapeHtml(value) { const el = document.createElement('div'); el.textContent = value; return el.innerHTML; }
function render(data) {
  dashboard = data; const { channel, metrics, sentiment } = data;
  $('channelName').textContent = channel.name; $('channelHandle').textContent = `${channel.handle || 'Public channel'} · Last ${data.videos.length} videos`;
  $('sourceLabel').textContent = data.source === 'live' ? 'LIVE DATA' : 'DEMO MODE';
  $('totalViews').textContent = fmt(metrics.views); $('subscribers').textContent = fmt(metrics.subscribers); $('avgViews').textContent = fmt(metrics.avgViews); $('engagement').textContent = `${metrics.engagement}%`;
  $('positive').textContent = `${sentiment.positive}%`; $('neutral').textContent = `${sentiment.neutral}%`; $('negative').textContent = `${sentiment.negative}%`; $('sentimentPct').textContent = `${sentiment.positive}%`;
  $('donut').style.background = `conic-gradient(#10b981 0 ${sentiment.positive}%,#758196 ${sentiment.positive}% ${sentiment.positive + sentiment.neutral}%,#f45a6b ${sentiment.positive + sentiment.neutral}% 100%)`;
  cloud('positiveCloud', data.wordCloud.positive); cloud('negativeCloud', data.wordCloud.negative);
  $('commentFeed').innerHTML = (data.comments || []).map(comment => { const colors = {positive:['#72e5bd','#143b32'],negative:['#ff98a5','#3a2029'],neutral:['#b1bfd1','#273244']}[comment.sentiment] || ['#b1bfd1','#273244']; return `<div style="display:flex;align-items:center;gap:8px;border-top:1px solid #1b2637;padding:7px 0;font-size:10px;color:#aebbd0"><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(comment.text)}</span><b style="margin-left:auto;text-transform:uppercase;font:8px 'DM Mono';letter-spacing:.5px;padding:3px 5px;border-radius:3px;color:${colors[0]};background:${colors[1]}">${comment.sentiment}</b></div>`; }).join('') || '<p style="font-size:10px;color:#7688a4">No public comments were available for these videos.</p>';
  $('trendGraph').innerHTML = data.trend.map((x, i) => `<div class="bar" title="${x.name}: ${x.score}%" style="height:${Math.max(7, x.score - 35)}%"></div>`).join('');
  $('gapRows').innerHTML = data.gaps.map(g => `<div class="gap-row"><span>${g.topic}</span><span>${g.volume}</span><b class="opp">${g.opportunity}</b></div>`).join('');
  $('prescriptionRows').innerHTML = data.prescriptions.map(p => `<div class="prescription"><span class="priority ${p.priority}">${p.priority}</span><div><b>${p.title}</b><p>${p.detail}</p></div></div>`).join('');
  if (data.notice) toast(data.notice);
}
async function analyze(channel = '') {
  const btn = $('analyzeBtn'); btn.disabled = true; btn.textContent = 'Analyzing…'; $('analysisHint').textContent = 'Pulling channel videos, metrics and audience signals…';
  try { const res = await fetch('/api/analyze', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({channel})}); if (!res.ok) throw new Error('Analysis request failed'); render(await res.json()); }
  catch { toast('Could not reach the analysis service. Please try again.'); }
  finally { btn.disabled = false; btn.innerHTML = 'Analyze <span>→</span>'; $('analysisHint').textContent = dashboard?.source === 'live' ? 'Live data successfully analyzed.' : 'Live YouTube analysis when your API key is connected.'; }
}
$('analyzeForm').addEventListener('submit', e => { e.preventDefault(); analyze($('channelInput').value.trim()); });
$('demoBtn').onclick = () => { $('channelInput').value = ''; analyze(''); };
$('gapBtn').onclick = () => { if (dashboard) { const btn = $('gapBtn'); btn.textContent = 'Scanning…'; setTimeout(() => { render(dashboard); btn.textContent = 'Refresh scan ↻'; toast('Competitor topics refreshed from the current analysis.'); }, 600); } };
$('predictBtn').onclick = async () => { const title = $('videoTitle').value.trim(); const length = $('videoLength').value; if (!title) { toast('Add a working video title to run the prediction.'); $('videoTitle').focus(); return; } const btn = $('predictBtn'); btn.textContent = 'Modeling…'; btn.disabled = true; try { const res = await fetch('/api/predict', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,length})}); if (!res.ok) throw new Error('Prediction request failed'); const p = await res.json(); $('prediction').innerHTML = `<span>PREDICTED ENGAGEMENT</span><strong>${p.engagement}%</strong><p>vs. your channel average: ${dashboard?.metrics.engagement || 6.2}% · ${p.uplift >= 0 ? '+' : ''}${p.uplift}% potential lift</p><div class="confidence"><i style="background:linear-gradient(90deg,#29d39d ${p.confidence}%,#26354c ${p.confidence}%)"></i><span>Confidence score</span><b>${p.confidence}%</b></div>`; $('upliftPreview').textContent = `${p.uplift >= 0 ? '+' : ''}${p.uplift}%`; } catch { toast('Prediction service unavailable. Please try again.'); } finally { btn.innerHTML = 'Predict engagement <span>✦</span>'; btn.disabled = false; } };
analyze('');
