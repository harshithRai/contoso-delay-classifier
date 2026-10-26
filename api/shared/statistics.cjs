'use strict';
function percentile(values, p) {
  if (!values.length) return null;
  const sorted = [...values].sort((a,b) => a-b);
  return sorted[Math.max(0, Math.ceil(p * sorted.length) - 1)];
}
function summarize(recent, window, allTime, now = Date.now()) {
  const okLatencies = recent.filter(r => r.status === 'ok').map(r => r.totalLatencyMs);
  const errors = window.filter(r => r.status === 'error').length;
  const good = window.filter(r => r.status === 'ok').length;
  const sorted = recent.toSorted((a,b) => b.at.localeCompare(a.at));
  return {
    requests15m: window.length, requestsAllTime: allTime,
    successfulSamples: okLatencies.length,
    p50Ms: okLatencies.length ? (()=>{const s=[...okLatencies].sort((a,b)=>a-b);return (s[Math.floor((s.length-1)/2)]+s[Math.floor(s.length/2)])/2;})() : null, p95Ms: percentile(okLatencies, .95),
    slowestMs: recent.length ? Math.max(...recent.map(r => r.totalLatencyMs)) : null,
    errorRatePercent: good + errors ? 100 * errors / (good + errors) : 0,
    errors15m: errors, invalid15m: window.filter(r => r.status === 'invalid').length,
    lastColdStart: sorted.find(r => r.coldStart) ? (() => { const r=sorted.find(r=>r.coldStart); return {at:r.at,latencyMs:r.totalLatencyMs}; })() : null,
    last50: sorted.slice(0,50).reverse().map(r => ({at:r.at,latencyMs:r.totalLatencyMs,status:r.status})),
    computedAt: new Date(now).toISOString(), percentileMethod: 'p50 median; p95 nearest rank; successful requests among last 100'
  };
}
module.exports = {percentile, summarize};
