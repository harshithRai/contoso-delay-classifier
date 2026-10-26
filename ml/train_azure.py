"""Submit the required 30-minute, AUC-weighted AutoML job on SQL-exported data."""
import json
import os
from datetime import datetime,timezone
from azure.ai.ml import Input, automl
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data
from azure_client import client
from common import ROOT,save_json

def main():
    export=ROOT/'ml/export';provenance=json.loads((export/'provenance.json').read_text())
    if provenance['source']!='Azure SQL ml.DelayTraining' or provenance['rows']!=10000:raise ValueError('Export the Azure SQL view first.')
    ml=client();version=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S');assets={}
    for name in ['train','test']:
        asset=ml.data.create_or_update(Data(name=f'contoso-delay-{name}',version=version,type=AssetTypes.MLTABLE,path=str(export/name),description='Exported from Azure SQL ml.DelayTraining; stratified seed 42'))
        assets[name]=Input(type=AssetTypes.MLTABLE,path=f'azureml:{asset.name}:{asset.version}')
    job=automl.classification(compute=os.environ.get('AZURE_ML_COMPUTE','cpu-cluster'),experiment_name='contoso-delay',training_data=assets['train'],test_data=assets['test'],target_column_name='delayed',primary_metric='AUC_weighted',n_cross_validations=3,enable_model_explainability=True)
    job.set_limits(timeout_minutes=30,max_trials=10,max_concurrent_trials=1)
    submitted=ml.jobs.create_or_update(job)
    save_json(ROOT/'artifacts/azure/job.json',{'jobName':submitted.name,'datasetVersion':version,'provenance':provenance})
    print(f'AutoML submitted: {submitted.name}. Studio: {submitted.studio_url}')
    ml.jobs.stream(submitted.name)
if __name__=='__main__':main()
