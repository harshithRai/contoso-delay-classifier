import argparse
import json
from azure.ai.ml.entities import ManagedOnlineEndpoint,ManagedOnlineDeployment
from azure_client import client
from common import ROOT,save_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--vm-size',default='Standard_DS2_v2');p.add_argument('--model',help='Registered CV winner; permits endpoint preparation while held-out evaluation runs.');args=p.parse_args()
    ml=client();path=ROOT/'artifacts/azure/model_runs.json';runs=json.loads(path.read_text()) if path.exists() else []
    if not runs and not args.model:raise ValueError('Evaluate models first, or explicitly provide the registered CV winner with --model.')
    model=args.model or runs[0]['registeredModel']
    endpoint=ManagedOnlineEndpoint(name=args.name,auth_mode='key',description='Contoso assignment; delete after demonstration')
    ml.online_endpoints.begin_create_or_update(endpoint).result()
    deployment=ManagedOnlineDeployment(name='blue',endpoint_name=args.name,model=model,instance_type=args.vm_size,instance_count=1)
    ml.online_deployments.begin_create_or_update(deployment).result()
    endpoint=ml.online_endpoints.get(args.name);endpoint.traffic={'blue':100};ml.online_endpoints.begin_create_or_update(endpoint).result()
    save_json(ROOT/'artifacts/azure/endpoint.json',{'endpointName':args.name,'registeredModel':model,'vmSize':args.vm_size,'instanceCount':1,'state':'Succeeded'})
    for run in runs:
        run['deployed']=run['registeredModel']==model
        run['endpointName']=args.name if run['deployed'] else None
    if runs:save_json(path,runs)
    print(f'Deployed {args.name}: {args.vm_size}, 1 instance. Set ML endpoint settings using scripts/configure_swa.py; keys are never printed.')
if __name__=='__main__':main()
