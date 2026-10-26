'use strict';
const fs = require('node:fs');
const path = require('node:path');
class LocalStore {
  constructor(directory) { this.dir=directory; fs.mkdirSync(directory,{recursive:true}); }
  file(id) { if (!/^[0-9a-f-]{36}$/.test(id)) throw Error('Invalid request ID'); return path.join(this.dir, `${id}.json`); }
  async insert(doc) {
    fs.writeFileSync(this.file(doc.id),JSON.stringify(doc));
    const countersFile = path.join(this.dir, 'counters.json');
    const counts = Object.assign(Object.create(null),fs.existsSync(countersFile) ? JSON.parse(fs.readFileSync(countersFile)) : {});
    counts[doc.userId]=(counts[doc.userId] || 0)+1;
    fs.writeFileSync(countersFile,JSON.stringify(counts));
  }
  async finalize(doc) { fs.writeFileSync(this.file(doc.id),JSON.stringify(doc)); }
  all() { return fs.readdirSync(this.dir).filter(n => /^[0-9a-f-]{36}\.json$/.test(n)).map(n => JSON.parse(fs.readFileSync(path.join(this.dir,n)))).filter(r => Date.parse(r.at)>Date.now()-2592000000).sort((a,b)=>b.at.localeCompare(a.at)); }
  async point(id,userId) { const file=this.file(id); if(!fs.existsSync(file)) return null; const doc=JSON.parse(fs.readFileSync(file)); return doc.userId===userId && Date.parse(doc.at)>Date.now()-2592000000 ? doc : null; }
  async recent(userId) { return this.all().filter(r=>r.userId===userId).slice(0,20); }
  async health(since) {
    const rows=this.all(); const cf=path.join(this.dir,'counters.json');
    const count=fs.existsSync(cf) ? Object.values(JSON.parse(fs.readFileSync(cf))).reduce((a,b)=>a+b,0) : 0;
    return {recent:rows.slice(0,100),window:rows.filter(r=>r.at>=since),allTime:count,coldStart:rows.find(r=>r.coldStart)};
  }
}
class CosmosStore {
  constructor(env) {
    if(!env.COSMOS_ENDPOINT || !env.COSMOS_KEY) throw Error('Cosmos settings missing');
    const {CosmosClient}=require('@azure/cosmos');
    this.container=new CosmosClient({endpoint:env.COSMOS_ENDPOINT,key:env.COSMOS_KEY}).database(env.COSMOS_DATABASE || 'contoso').container('requests');
  }
  async insert(doc) {
    // Each request and its cumulative counter commit atomically in one user partition.
    try { await this.container.items.create({id:'__counter',userId:doc.userId,type:'counter',count:0,ttl:-1}); }
    catch(e) { if(e.code!==409) throw e; }
    const result=await this.container.items.batch([
      {operationType:'Create',resourceBody:doc},
      {operationType:'Patch',id:'__counter',resourceBody:{operations:[{op:'incr',path:'/count',value:1}]}}
    ],doc.userId);
    if(result.code<200 || result.code>=300 || result.result?.some(x=>x.statusCode>=300)) throw Error('Request transaction failed');
  }
  async finalize(doc) {
    await this.container.item(doc.id,doc.userId).replace(doc);
  }
  async point(id,userId) { try { return (await this.container.item(id,userId).read()).resource || null; } catch(e) { if(e.code===404) return null; throw e; } }
  async recent(userId) {
    return (await this.container.items.query({query:"SELECT TOP 20 * FROM c WHERE c.type = 'request' AND c.userId = @u ORDER BY c.at DESC",parameters:[{name:'@u',value:userId}]},{partitionKey:userId}).fetchAll()).resources;
  }
  async health(since) {
    const query=async(q,parameters=[]) => (await this.container.items.query({query:q,parameters}).fetchAll()).resources;
    const [recent,window,counts,cold]=await Promise.all([
      query("SELECT TOP 100 * FROM c WHERE c.type = 'request' ORDER BY c.at DESC"),
      query("SELECT c.status FROM c WHERE c.type = 'request' AND c.at >= @s",[{name:'@s',value:since}]),
      query("SELECT VALUE SUM(c.count) FROM c WHERE c.type = 'counter'"),
      query("SELECT TOP 1 c.at, c.totalLatencyMs FROM c WHERE c.type = 'request' AND c.coldStart = true ORDER BY c.at DESC")
    ]);
    return {recent,window,allTime:counts[0] || 0,coldStart:cold[0]};
  }
}
function makeStore(env=process.env) { return env.APP_MODE==='local' ? new LocalStore(env.LOCAL_LOG_DIR || path.resolve('.local/requests')) : new CosmosStore(env); }
module.exports={LocalStore,CosmosStore,makeStore};
