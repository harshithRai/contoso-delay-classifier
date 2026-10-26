"""No external dependencies. Reports actual HTTP results, excluding invalid from error rate."""
import argparse
import json
import math
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:7071');p.add_argument('--count',type=int,default=100);p.add_argument('--concurrency',type=int,default=5);p.add_argument('--out');p.add_argument('--user-id',default='load-'+str(uuid.uuid4()));p.add_argument('--environment',choices=['local','azure'],default='local');p.add_argument('--vm-size',default='local process');args=p.parse_args()
    if args.count<1 or args.concurrency<1:p.error('count and concurrency must be positive')
    payload={'userId':args.user_id,'carrier':'IndiaPost','distance_km':2100,'weight_kg':6.0,'items':3,'order_hour':19,'is_sale_day':1,'warehouse_backlog':55,'weather_index':0.4}
    def call(_):
        start=time.perf_counter();result={};code=0
        try:
            with urlopen(Request(args.url.rstrip('/')+'/api/predict',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=30) as response:code=response.status;result=json.load(response)
        except HTTPError as e:
            code=e.code
            try:result=json.load(e)
            except Exception:result={}
        except (URLError,TimeoutError):pass
        return {'httpStatus':code,'status':result.get('status','error'),'latencyMs':round((time.perf_counter()-start)*1000),'apiLatencyMs':result.get('latencyMs'),'requestId':result.get('requestId')}
    start=time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:results=list(pool.map(call,range(args.count)))
    total=time.perf_counter()-start
    good=[r for r in results if r['status']=='ok'];errors=[r for r in results if r['status']=='error'];latencies=sorted(r['latencyMs'] for r in good)
    def pct(p):return latencies[max(0,math.ceil(len(latencies)*p)-1)] if latencies else None
    p50=(latencies[(len(latencies)-1)//2]+latencies[len(latencies)//2])/2 if latencies else None
    report={'environment':args.environment,'vmSize':args.vm_size,'instances':1,'requests':args.count,'concurrency':args.concurrency,'userId':args.user_id,'totalSeconds':round(total,3),'p50ClientMs':p50,'p95ClientMs':pct(.95),'errorRatePercent':100*len(errors)/(len(good)+len(errors)) if good or errors else 0,'invalidCount':sum(r['status']=='invalid' for r in results),'latencyWindow':'successful requests in this load test; client wall time includes transport','results':results}
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
    if args.out:Path(args.out).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
