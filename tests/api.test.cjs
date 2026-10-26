'use strict';
const {test}=require('node:test');const assert=require('node:assert/strict');
const {mkdtempSync,rmSync}=require('node:fs');const os=require('node:os');const path=require('node:path');
const {createService,parseModel}=require('../api/shared/service.cjs');
const {LocalStore}=require('../api/shared/store.cjs');const {summarize,percentile}=require('../api/shared/statistics.cjs');
const input={userId:'test-user',carrier:'IndiaPost',distance_km:2100,weight_kg:6,items:3,order_hour:19,is_sale_day:1,warehouse_backlog:55,weather_index:.4};
const env={APP_MODE:'local',ML_ENDPOINT_URL:'http://127.0.0.1:7072/score',ML_ENDPOINT_KEY:'local-test'};
function fixture(t,fetcher=async()=>({ok:true,json:async()=>[1]})) {const dir=mkdtempSync(path.join(os.tmpdir(),'contoso-test-'));t.after(()=>rmSync(dir,{recursive:true,force:true}));const store=new LocalStore(dir);return {store,service:createService({env,store,fetcher})};}
test('successful request maps class, persists, and supports partitioned point read',async t=>{
  const {service,store}=fixture(t);const r=await service.predict(input);
  assert.equal(r.status,200);assert.equal(r.body.label,'delayed');assert.equal(r.body.coldStart,true);
  const doc=await store.point(r.body.requestId,input.userId);assert.equal(doc.type,'request');assert.equal(doc.status,'ok');assert.equal(doc.ttl,2592000);assert.equal(doc.totalLatencyMs,r.body.latencyMs);
  assert.equal((await service.requests({requestId:r.body.requestId,userId:'other-user'})).status,404);
  assert.equal((await service.requests({requestId:r.body.requestId,userId:input.userId})).body.id,r.body.requestId);
});
test('invalid fields are rejected and logged without invoking the model',async t=>{
  let calls=0;const {service,store}=fixture(t,async()=>{calls++;throw Error();});
  const bad=[{...input,order_hour:24},{...input,weight_kg:'2'},{...input,items:1.2},{...input,weather_index:null},{...input,is_sale_day:true},{...input,carrier:'<script>private</script>'},{...input,secret:'unwanted'},null];
  for(const body of bad)assert.equal((await service.predict(body)).status,400);
  assert.equal(calls,0);assert.equal(store.all().length,bad.length);assert.ok(store.all().every(r=>r.status==='invalid' && !JSON.stringify(r.input).includes('private')));
  const m=(await service.metrics()).body;assert.equal(m.invalid15m,bad.length);assert.equal(m.errorRatePercent,0);assert.equal(m.p50Ms,null);
});
test('upstream auth failure and malformed response become tracked 502s',async t=>{
  const {service,store}=fixture(t,async()=>({ok:false,status:401}));const r=await service.predict(input);
  assert.equal(r.status,502);assert.equal(r.body.status,'error');assert.equal((await store.point(r.body.requestId,input.userId)).httpStatus,502);
  assert.equal((await service.metrics()).body.errorRatePercent,100);
  assert.throws(()=>parseModel({prediction:['unexpected']}));assert.equal(parseModel('[0]'),'on time');assert.equal(parseModel({predictions:[1]}),'delayed');assert.equal(parseModel(0),'on time');assert.equal(parseModel('1'),'delayed');
});
test('timeout maps to 504 with a safe message and a persisted ID',async t=>{
  const {service,store}=fixture(t,async()=>{const e=Error('sensitive details');e.name='TimeoutError';throw e;});
  const r=await service.predict(input);assert.equal(r.status,504);assert.match(r.body.error,/timed out/);assert.ok(!JSON.stringify(r).includes('sensitive'));assert.equal((await store.point(r.body.requestId,input.userId)).status,'error');
});
test('no success is claimed when request persistence is unavailable',async()=>{
  const service=createService({env,store:{insert:async()=>{throw Error('secret');}},fetcher:async()=>({ok:true,json:async()=>[0]})});
  const r=await service.predict(input);assert.equal(r.status,503);assert.equal(r.body.label,null);assert.ok(r.body.requestId);assert.ok(!JSON.stringify(r).includes('secret'));
});
test('health uses median and nearest-rank p95, excluding invalid from error denominator',()=>{
  const rows=[10,20,30,40].map((ms,i)=>({totalLatencyMs:ms,status:'ok',at:`2026-10-26T10:00:0${i}Z`}));
  rows.push({totalLatencyMs:90,status:'error',at:'2026-10-26T10:00:05Z'},{totalLatencyMs:2,status:'invalid',at:'2026-10-26T10:00:06Z'});
  const m=summarize(rows,rows,50);assert.equal(m.p50Ms,25);assert.equal(m.p95Ms,40);assert.equal(m.errorRatePercent,20);assert.equal(m.invalid15m,1);assert.equal(m.slowestMs,90);assert.equal(m.requestsAllTime,50);
  assert.equal(percentile(Array.from({length:100},(_,i)=>i+1),.95),95);assert.equal(summarize([],[],0).p95Ms,null);
});
test('idle marker is set again after ten idle minutes',async t=>{
  const {store}=fixture(t);let now=Date.now();const service=createService({env,store,now:()=>now,fetcher:async()=>({ok:true,json:async()=>[0]})});
  assert.equal((await service.predict(input)).body.coldStart,true);assert.equal((await service.predict(input)).body.coldStart,false);now+=600000;assert.equal((await service.predict(input)).body.coldStart,true);
});
test('15-minute window is separate from all-time count and recent history',async t=>{
  const {service,store}=fixture(t);await store.insert({id:'00000000-0000-0000-0000-000000000001',userId:input.userId,type:'request',at:new Date(Date.now()-1000000).toISOString(),status:'ok',totalLatencyMs:50,input:{}});
  const m=(await service.metrics()).body;assert.equal(m.requestsAllTime,1);assert.equal(m.requests15m,0);assert.equal(m.p50Ms,50);
});
test('query rejects missing identifiers and malformed UUID',async t=>{
  const {service}=fixture(t);assert.equal((await service.requests({})).status,400);assert.equal((await service.requests({userId:input.userId,requestId:'../../secret'})).status,400);
});
test('a partial logging failure remains an error rather than a false successful record',async t=>{
  const {store}=fixture(t);store.finalize=async()=>{throw Error('write failed');};
  const service=createService({env,store,fetcher:async()=>({ok:true,json:async()=>[0]})});
  const r=await service.predict(input);assert.equal(r.status,503);
  const doc=await store.point(r.body.requestId,input.userId);assert.equal(doc.status,'error');assert.equal(doc.httpStatus,503);assert.equal(doc.label,null);
});
test('a cold-start sample is retained even after it leaves the last 100 requests',async t=>{
  const {store}=fixture(t);
  const old={id:'00000000-0000-0000-0000-000000000002',userId:input.userId,type:'request',at:new Date(Date.now()-50000).toISOString(),status:'ok',totalLatencyMs:80,input:{},coldStart:true};
  await store.insert(old);
  for(let i=0;i<101;i++)await store.insert({...old,id:`00000000-0000-0000-0000-${String(i+3).padStart(12,'0')}`,coldStart:false,at:new Date().toISOString()});
  const service=createService({env,store});const m=(await service.metrics()).body;assert.equal(m.lastColdStart.latencyMs,80);assert.equal(m.last50.length,50);
});
