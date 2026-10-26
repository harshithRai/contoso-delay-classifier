import {spawn} from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
process.chdir(root);
const port=Number(process.env.PORT || 7071), modelPort=Number(process.env.MODEL_PORT || 7072);
if(!fs.existsSync('artifacts/local/model.joblib')) { console.error('Train first: .venv/bin/python ml/train_local.py'); process.exit(1); }
const python=process.env.PYTHON || path.join(root,'.venv/bin/python');
const child=spawn(python,['ml/serve_local.py','--port',String(modelPort)],{stdio:'inherit',env:{...process.env,LOCAL_MODEL_KEY:'local-development-only'}});
const require=createRequire(import.meta.url);
const {createService}=require('../api/shared/service.cjs');
const service=createService({env:{...process.env,APP_MODE:'local',ML_ENDPOINT_URL:`http://127.0.0.1:${modelPort}/score`,ML_ENDPOINT_KEY:process.env.LOCAL_API_MODEL_KEY || 'local-development-only',MODEL_VERSION:'local-sklearn-baseline'}});
const types={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'};
const server=http.createServer(async(req,res)=>{
  try {
    const url=new URL(req.url,'http://localhost');
    if(url.pathname.startsWith('/api/')) {
      const route=url.pathname.slice(5); let result;
      if(route==='predict' && req.method==='POST') {
        let body='', tooBig=false;
        for await (const chunk of req) { if(Buffer.byteLength(body)+chunk.length>8192) tooBig=true; if(!tooBig) body+=chunk; }
        let parsed; try { parsed=tooBig?null:JSON.parse(body); } catch { parsed=null; }
        result=await service.predict(parsed);
      } else if(route==='metrics' && req.method==='GET') result=await service.metrics();
      else if(route==='requests' && req.method==='GET') result=await service.requests(Object.fromEntries(url.searchParams));
      else result={status:404,headers:{'Content-Type':'application/json'},body:{error:'Route not found.'}};
      res.writeHead(result.status,result.headers);res.end(JSON.stringify(result.body));return;
    }
    const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
    if(!['index.html','app.js','styles.css','staticwebapp.config.json'].includes(name)) {res.writeHead(404);res.end('Not found');return;}
    res.writeHead(200,{'Content-Type':types[path.extname(name)] || 'text/plain'});res.end(fs.readFileSync(path.join(root,'app',name)));
  } catch {res.writeHead(500,{'Content-Type':'application/json'});res.end(JSON.stringify({error:'Service unavailable.'}));}
});
let ready=false;
for(let i=0;i<100;i++) {if(child.exitCode!==null)break;try {const response=await fetch(`http://127.0.0.1:${modelPort}/health`);if(response.ok){ready=true;break;}} catch {} await new Promise(r=>setTimeout(r,100));}
if(!ready){child.kill();console.error('Local model could not start. Check the Python environment and port.');process.exit(1);}
server.listen(port,'127.0.0.1',()=>console.log(`Contoso local portal: http://127.0.0.1:${port}\nLocal trained model + local request store. Azure is not deployed.`));
const stop=()=>{server.close();child.kill();process.exit(0);};
process.on('SIGINT',stop);process.on('SIGTERM',stop);
child.on('exit',code=>{if(code) {console.error('Local model stopped.');server.close();process.exit(code);}});
