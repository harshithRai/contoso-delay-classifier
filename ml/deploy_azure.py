import argparse
import json
from azure.ai.ml.entities import ManagedOnlineEndpoint,ManagedOnlineDeployment
from azure_client import client
from common import ROOT,save_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--vm-size',default='Standard_DS2_v2');args=p.parse_args()
    ml=client();path=ROOT/'artifacts/azure/model_runs.json';runs=json.loads(path.read_text())
    endpoint=ManagedOnlineEndpoint(name=args.name,auth_mode='key',description='Contoso assignment; delete after demonstration')
    ml.online_endpoints.begin_create_or_update(endpoint).result()
    deployment=ManagedOnlineDeployment(name='blue',endpoint_name=args.name,model=runs[0]['registeredModel'],instance_type=args.vm_size,instance_count=1)
    ml.online_deployments.begin_create_or_update(deployment).result()
    endpoint=ml.online_endpoints.get(args.name);endpoint.traffic={'blue':100};ml.online_endpoints.begin_create_or_update(endpoint).result()
    runs[0]['endpointName']=args.name;runs[0]['deployed']=True;save_json(path,runs)
    print(f'Deployed {args.name}: {args.vm_size}, 1 instance. Set ML endpoint settings using scripts/configure_swa.py; keys are never printed.')
if __name__=='__main__':main()
