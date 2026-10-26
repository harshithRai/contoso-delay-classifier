"""Copy keys directly between Azure services in memory, never stdout or git.
Run on macOS/Linux/Cloud Shell with Azure CLI signed in. The settings REST request
reads JSON from stdin through /dev/stdin; keys never become command arguments.
"""
import argparse
import json
import os
import re
import subprocess

def az(*args):
    result=subprocess.run(['az',*args,'--only-show-errors','-o','json'],capture_output=True,text=True)
    if result.returncode:raise RuntimeError('Azure command failed; check account permissions and resource names. No secret output was displayed.')
    return json.loads(result.stdout) if result.stdout.strip() else {}

def main():
    p=argparse.ArgumentParser();p.add_argument('--swa',required=True);p.add_argument('--cosmos',required=True);p.add_argument('--endpoint',required=True);p.add_argument('--failure-test',action='store_true');args=p.parse_args()
    group=os.environ['AZURE_RESOURCE_GROUP'];workspace=os.environ['AZURE_ML_WORKSPACE']
    account=az('account','show');subscription=account['id']
    cosmos=az('cosmosdb','show','-g',group,'-n',args.cosmos)
    keys=az('cosmosdb','keys','list','-g',group,'-n',args.cosmos)
    endpoint=az('ml','online-endpoint','show','-g',group,'-w',workspace,'-n',args.endpoint)
    deployment=az('ml','online-deployment','show','-g',group,'-w',workspace,'--endpoint-name',args.endpoint,'-n','blue')
    model=str(deployment.get('model',''))
    version=re.search(r'/models/([^/]+)/versions/([^/]+)',model)
    if version:model_version=f'{version.group(1)}:{version.group(2)}'
    elif model.startswith('azureml:') and '/' not in model:model_version=model.removeprefix('azureml:')
    else:raise RuntimeError('Could not identify the deployed model version; no settings changed.')
    mlkeys=az('ml','online-endpoint','get-credentials','-g',group,'-w',workspace,'-n',args.endpoint)
    # Preserve unrelated settings, including Application Insights configuration.
    current=az('staticwebapp','appsettings','list','-g',group,'-n',args.swa).get('properties',{})
    current.update({'APP_MODE':'azure','COSMOS_ENDPOINT':cosmos['documentEndpoint'],'COSMOS_KEY':keys['primaryMasterKey'],'COSMOS_DATABASE':'contoso','ML_ENDPOINT_URL':endpoint['scoring_uri'],'ML_ENDPOINT_KEY':'intentionally-invalid-for-failure-test' if args.failure_test else mlkeys['primaryKey'],'MODEL_VERSION':model_version,'ERROR_THRESHOLD_PERCENT':'5'})
    url=f'https://management.azure.com/subscriptions/{subscription}/resourceGroups/{group}/providers/Microsoft.Web/staticSites/{args.swa}/config/appsettings?api-version=2023-12-01'
    result=subprocess.run(['az','rest','--method','put','--url',url,'--body','@/dev/stdin','--only-show-errors','--output','none'],input=json.dumps({'properties':current}),capture_output=True,text=True)
    if result.returncode:raise RuntimeError('Could not update server-side settings; no secret output was displayed.')
    print('Server-side settings updated. '+('FAILURE TEST KEY ACTIVE: restore by rerunning without --failure-test.' if args.failure_test else 'Real model key active.'))

if __name__=='__main__':main()
