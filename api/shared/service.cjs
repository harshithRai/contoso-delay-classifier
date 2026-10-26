'use strict';
const {randomUUID}=require('node:crypto');
const {performance}=require('node:perf_hooks');
const {validate,validUserId,safeInput,FEATURES}=require('./validation.cjs');
const {summarize}=require('./statistics.cjs');
const {makeStore}=require('./store.cjs');
const json=(status,body)=>({status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'},body});
function parseModel(value) {
  // The deployed AutoML model returns [false]/[true]; integer classes are also supported.
  if(value===0 || value===1 || typeof value==='boolean') return Number(value)===1 ? 'delayed' : 'on time';
  if(typeof value==='string') { try { return parseModel(JSON.parse(value)); } catch { throw Error('Invalid model response'); } }
  const item=Array.isArray(value) ? value[0] : (value?.prediction?.[0] ?? value?.predictions?.[0]);
  const label=item && typeof item==='object' ? (item.label ?? item.delayed) : item;
  if(![0,1,'0','1',false,true].includes(label)) throw Error('Invalid model response');
  return Number(label)===1 ? 'delayed' : 'on time';
}
function createService({env=process.env,store,fetcher=fetch,now=Date.now,clock=()=>performance.now()}={}) {
  let lastRequest=0;
  const getStore=()=>store || (store=makeStore(env));
  async function predict(body) {
    const start=clock(), stamp=now(), id=randomUUID();
    const userId=validUserId(body?.userId) ? body.userId : randomUUID();
    const coldStart=!lastRequest || stamp-lastRequest>=600000; lastRequest=stamp;
    const doc={id,userId,type:'request',at:new Date(stamp).toISOString(),input:safeInput(body),label:null,modelLatencyMs:0,totalLatencyMs:0,status:'ok',httpStatus:200,error:null,modelVersion:env.MODEL_VERSION || 'delay-endpoint',coldStart,ttl:2592000};
    let input;
    try { input=validate(body); doc.input=input; }
    catch(e) { doc.status='invalid';doc.httpStatus=400;doc.error=e.message; }
    if(input) {
      const mlStart=clock();
      try {
        const url=env.ML_ENDPOINT_URL;
        if(!url || (!url.startsWith('https://') && !(env.APP_MODE==='local' && /^http:\/\/127\.0\.0\.1:\d+\/score$/.test(url)))) throw Error('Missing model configuration');
        if(!env.ML_ENDPOINT_KEY) throw Error('Missing model configuration');
        const response=await fetcher(url,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${env.ML_ENDPOINT_KEY}`},body:JSON.stringify({input_data:{columns:FEATURES,index:[0],data:[FEATURES.map(k=>input[k])]}}),signal:AbortSignal.timeout(10000)});
        if(!response.ok) throw Error('Model unavailable');
        doc.label=parseModel(await response.json());
      } catch(e) {
        doc.status='error'; doc.httpStatus=['TimeoutError','AbortError'].includes(e.name)?504:502;
        doc.error=doc.httpStatus===504 ? 'The model timed out. Please try again.' : 'The prediction service is unavailable. Please try again.';
      } finally { doc.modelLatencyMs=Math.round(clock()-mlStart); }
    }
    doc.totalLatencyMs=Math.round(clock()-start);
    try {
      const dbStart=clock();
      // A partially persisted request remains an error if finalization cannot complete.
      await getStore().insert({...doc,status:'error',httpStatus:503,label:null,error:'Request tracking did not finish.'});
      doc.databaseWriteMs=Math.round(clock()-dbStart);
      doc.totalLatencyMs=Math.round(clock()-start);
      await getStore().finalize(doc);
    } catch {
      // Do not claim a tracked success when persistence failed; never emit credentials or raw errors.
      console.error(JSON.stringify({event:'request_log_unavailable',requestId:id,status:doc.status}));
      return json(503,{requestId:id,userId,status:'error',label:null,latencyMs:Math.round(clock()-start),error:'Request tracking is unavailable. Please try again.'});
    }
    return json(doc.httpStatus,{requestId:id,userId,label:doc.label,latencyMs:doc.totalLatencyMs,modelLatencyMs:doc.modelLatencyMs,status:doc.status,error:doc.error,coldStart});
  }
  async function metrics() {
    try {
      const data=await getStore().health(new Date(now()-900000).toISOString());
      return json(200,{...summarize(data.recent,data.window,data.allTime,now()),lastColdStart:data.coldStart ? {at:data.coldStart.at,latencyMs:data.coldStart.totalLatencyMs} : null,mode:env.APP_MODE==='local'?'local':'azure',modelVersion:env.MODEL_VERSION || 'delay-endpoint',errorThresholdPercent:Number(env.ERROR_THRESHOLD_PERCENT || 5)});
    } catch { return json(503,{status:'error',error:'Health metrics are temporarily unavailable.'}); }
  }
  async function requests(query={}) {
    if(!validUserId(query.userId)) return json(400,{status:'invalid',error:'Provide a valid userId.'});
    if(query.requestId && !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(query.requestId)) return json(400,{status:'invalid',error:'Provide a valid request ID.'});
    try {
      if(query.requestId) { const doc=await getStore().point(query.requestId,query.userId); return doc?.type==='request' ? json(200,doc) : json(404,{status:'error',error:'Request not found for this browser.'}); }
      return json(200,{requests:await getStore().recent(query.userId)});
    } catch { return json(503,{status:'error',error:'Request history is temporarily unavailable.'}); }
  }
  return {predict,metrics,requests};
}
let service;
module.exports={createService,parseModel,getService:()=>service || (service=createService())};
