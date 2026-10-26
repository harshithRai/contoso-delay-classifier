"""Upsert real Azure results only; local reports are deliberately rejected."""
import json
import os
import subprocess
from pathlib import Path
from azure.cosmos import CosmosClient

path=Path(__file__).resolve().parents[1]/'artifacts/azure/model_runs.json'
runs=json.loads(path.read_text())
if len(runs)<2 or any(r.get('source')!='Azure-AutoML' for r in runs):raise ValueError('Need two actual Azure AutoML results.')
endpoint=os.environ.get('COSMOS_ENDPOINT');key=os.environ.get('COSMOS_KEY')
if not endpoint or not key:
    def az(*args):
        result=subprocess.run(['az',*args,'--only-show-errors','-o','json'],capture_output=True,text=True)
        if result.returncode:raise RuntimeError('Cannot access Cosmos settings; check your CLI login and resource permissions.')
        return json.loads(result.stdout)
    group=os.environ['AZURE_RESOURCE_GROUP'];account=os.environ['COSMOS_ACCOUNT']
    endpoint=az('cosmosdb','show','-g',group,'-n',account)['documentEndpoint']
    key=az('cosmosdb','keys','list','-g',group,'-n',account)['primaryMasterKey']
container=CosmosClient(endpoint,credential=key).get_database_client('contoso').get_container_client('model_runs')
for run in runs:
    container.upsert_item(run)
    print(f'Upserted {run["id"]}: {run["algorithm"]}; deployed={run["deployed"]}')
