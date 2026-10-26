'use strict';
const $=id=>document.getElementById(id);
let userId;
try { userId=localStorage.getItem('contoso-user-id'); if(!userId || !/^[A-Za-z0-9_-]{3,64}$/.test(userId)) {userId=crypto.randomUUID();localStorage.setItem('contoso-user-id',userId);} }
catch { userId=crypto.randomUUID(); }
$('user-id').textContent=userId;
let lastId='', refreshing=false;
const ms=value=>value===null || value===undefined ? '—' : `${Math.round(value).toLocaleString()} ms`;
const time=value=>new Date(value).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
async function api(url,options={}) {
  const response=await fetch(url,{...options,signal:AbortSignal.timeout(25000)});
  const data=await response.json();
  return {ok:response.ok,data};
}
const samples={safe:{carrier:'BlueDart',distance_km:200,weight_kg:1,items:1,order_hour:10,is_sale_day:0,warehouse_backlog:18,weather_index:0.03},risk:{carrier:'IndiaPost',distance_km:5500,weight_kg:12,items:7,order_hour:22,is_sale_day:1,warehouse_backlog:65,weather_index:0.85}};
for(const name of ['safe','risk']) $(`${name}-preset`).addEventListener('click',()=>{for(const [key,value] of Object.entries(samples[name])) $('order-form').elements.namedItem(key).value=value;});
$('order-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const body={userId};
  for(const [key,value] of new FormData(event.target)) body[key]=key==='carrier'?value:Number(value);
  $('predict-button').disabled=true;$('spinner').hidden=false;$('button-arrow').hidden=true;$('button-text').textContent='Assessing order…';
  $('result-card').className='card result-card';$('result-title').textContent='Assessing delivery risk…';$('result-description').textContent='Calling the model and recording your request.';$('result-status').textContent='In progress';
  try {
    const {ok,data}=await api('/api/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    lastId=data.requestId || '';
    $('copy-id').textContent=lastId || '—';$('copy-id').disabled=!lastId;$('copy-id').title=lastId || 'Request ID';
    $('result-latency').textContent=ms(data.latencyMs);$('model-latency').textContent=ms(data.modelLatencyMs);
    $('result-status').textContent=ok?'Complete':data.status==='invalid'?'Invalid input':'Service error';
    if(ok) {
      const delayed=data.label==='delayed';
      $('result-title').textContent=delayed?'Likely delayed':'Likely on time';
      $('result-description').textContent=delayed?'This order has delivery risk. Consider proactive tracking or a customer update.':'The model expects this order to arrive on time. Keep an eye on changes in conditions.';
      $('result-symbol').textContent=delayed?'!':'✓';$('result-card').classList.toggle('delayed',delayed);
    } else {$('result-card').classList.add('failed');$('result-symbol').textContent='!';$('result-title').textContent='Unable to assess';$('result-description').textContent=data.error || 'Something went wrong. Please try again.';}
  } catch {
    lastId='';$('copy-id').textContent='—';$('copy-id').disabled=true;$('result-latency').textContent='—';$('model-latency').textContent='—';
    $('result-card').classList.add('failed');$('result-symbol').textContent='!';$('result-status').textContent='Connection error';$('result-title').textContent='Connection interrupted';$('result-description').textContent='Could not reach the API. Your request may still have completed; check recent requests before retrying.';
  } finally {$('predict-button').disabled=false;$('spinner').hidden=true;$('button-arrow').hidden=false;$('button-text').textContent='Assess delivery risk';await refresh();}
});
$('copy-id').addEventListener('click',async()=>{try {await navigator.clipboard.writeText(lastId);$('copy-id').textContent='Copied';setTimeout(()=>{$('copy-id').textContent=lastId;},1200);} catch {$('lookup-id').value=lastId;$('lookup-id').focus();}});
function renderMetrics(data) {
  $('mode-banner').hidden=data.mode!=='local';$('model-name').textContent=data.modelVersion;
  $('connection').textContent=data.mode==='local'?'Local service connected':'Azure service connected';$('connection').className='connection connected';
  $('request-count').textContent=data.requests15m.toLocaleString();$('all-time').textContent=`${data.requestsAllTime.toLocaleString()} all time`;
  $('p50').textContent=ms(data.p50Ms);$('p95').textContent=ms(data.p95Ms);$('error-rate').textContent=`${data.errorRatePercent.toFixed(1)}%`;
  const elevated=data.errorRatePercent>data.errorThresholdPercent;
  $('error-metric').classList.toggle('alert',elevated);$('error-note').textContent=`Alert > ${data.errorThresholdPercent}% · ${data.invalid15m} invalid excluded`;
  $('health-state').textContent=elevated?'Elevated errors':data.requests15m?'Operational':'No recent traffic';
  $('last-updated').textContent=`Updated ${time(data.computedAt)}`;
  $('cold-start').textContent=data.lastColdStart?`First / idle call · ${ms(data.lastColdStart.latencyMs)} at ${time(data.lastColdStart.at)}`:'First / idle call · no sample yet';
  $('slowest').textContent=`Slowest · ${ms(data.slowestMs)}`;
  const chart=$('latency-chart');chart.replaceChildren();
  if(!data.last50.length) {const empty=document.createElement('span');empty.className='chart-empty';empty.textContent='Make a prediction to start measuring.';chart.append(empty);}
  const max=Math.max(1,...data.last50.map(r=>r.latencyMs));
  for(const point of data.last50) {const bar=document.createElement('div');bar.className=`bar ${point.status}`;bar.style.height=`${Math.max(3,point.latencyMs/max*85)}%`;bar.title=`${time(point.at)} · ${point.status} · ${point.latencyMs} ms`;chart.append(bar);}
  chart.setAttribute('aria-label',`${data.last50.length} recent latencies. Maximum ${max} milliseconds.`);
}
function renderHistory(rows) {
  const target=$('history-body');target.replaceChildren();
  if(!rows.length) {const row=document.createElement('tr'),cell=document.createElement('td');cell.colSpan=6;cell.className='empty-cell';cell.textContent='Your requests will appear here.';row.append(cell);target.append(row);}
  for(const r of rows) {
    const tr=document.createElement('tr');
    for(const value of [time(r.at),r.id.slice(0,8)+'…',r.input?.carrier || '—',r.label?`Likely ${r.label}`:'—',ms(r.totalLatencyMs)]) {const td=document.createElement('td');td.textContent=value;tr.append(td);}
    tr.children[1].title=r.id;tr.children[1].style.cursor='pointer';tr.children[1].addEventListener('click',()=>{$('lookup-id').value=r.id;$('lookup-form').requestSubmit();});
    const td=document.createElement('td'),badge=document.createElement('span');badge.className=`pill ${['ok','error','invalid'].includes(r.status)?r.status:'error'}`;badge.textContent=r.status;td.append(badge);tr.append(td);target.append(tr);
  }
}
async function refresh() {
  if(refreshing)return;refreshing=true;
  try {
    const outcomes=await Promise.allSettled([api('/api/metrics'),api(`/api/requests?userId=${encodeURIComponent(userId)}`)]);
    const failures=[];
    if(outcomes[0].status==='fulfilled' && outcomes[0].value.ok) renderMetrics(outcomes[0].value.data);
    else {failures.push('Service health is unavailable.');$('connection').textContent='Service unavailable';$('connection').className='connection failed';$('health-state').textContent='Unavailable';}
    if(outcomes[1].status==='fulfilled' && outcomes[1].value.ok) renderHistory(outcomes[1].value.data.requests);
    else failures.push('Request history is unavailable.');
    $('health-error').hidden=!failures.length;$('health-error').textContent=failures.join(' ');
  } finally {refreshing=false;}
}
$('lookup-form').addEventListener('submit',async event=>{
  event.preventDefault();const result=$('lookup-result');result.hidden=false;result.textContent='Looking up request…';
  try {const {ok,data}=await api(`/api/requests?userId=${encodeURIComponent(userId)}&requestId=${encodeURIComponent($('lookup-id').value.trim())}`);result.textContent=ok?JSON.stringify(data,null,2):data.error;} catch {result.textContent='Request lookup is unavailable. Please try again.';}
});
$('refresh-button').addEventListener('click',refresh);
refresh();setInterval(()=>{if(!document.hidden)refresh();},15000);
