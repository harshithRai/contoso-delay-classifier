"""Rank CV runs, register top two, and evaluate both on untouched SQL test data."""
import json
from datetime import datetime,timezone
from pathlib import Path
import mlflow
from mlflow.tracking import MlflowClient
from azure.ai.ml import command,Input,Output
from azure.ai.ml.entities import Model,Environment
from azure.ai.ml.constants import AssetTypes
from azure_client import client
from common import ROOT,FEATURES,save_json

def main():
    ml=client();info=json.loads((ROOT/'artifacts/azure/job.json').read_text());job=info['jobName']
    workspace=ml.workspaces.get(ml.workspace_name);mlflow.set_tracking_uri(workspace.mlflow_tracking_uri);tracking=MlflowClient()
    runs=[]
    for child in ml.jobs.list(parent_job_name=job):
        run=tracking.get_run(child.name)
        if run.info.status=='FINISHED' and 'AUC_weighted' in run.data.metrics:runs.append(run)
    runs.sort(key=lambda r:r.data.metrics['AUC_weighted'],reverse=True)
    if len(runs)<2:raise RuntimeError('Need two completed AutoML candidates. Check the job leaderboard.')
    documents=[]
    for rank,run in enumerate(runs[:2]):
        model_folder=Path(mlflow.artifacts.download_artifacts(run_id=run.info.run_id,artifact_path='outputs/mlflow-model',dst_path=str(ROOT/'artifacts/azure/downloads'/run.info.run_id)))
        model=ml.models.create_or_update(Model(name='contoso-delay',version=f'{info["datasetVersion"]}{rank}',path=str(model_folder),type=AssetTypes.MLFLOW_MODEL))
        conda=model_folder/'conda.yaml'
        if not conda.exists():raise FileNotFoundError('AutoML model conda.yaml missing; inspect its MLflow artifact before evaluation.')
        env=Environment(image='mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest',conda_file=str(conda))
        evaluate=command(code=str(ROOT/'ml'),command='python evaluate_model.py --model ${{inputs.model}} --test ${{inputs.test}} --out ${{outputs.report}}',inputs={'model':Input(type=AssetTypes.MLFLOW_MODEL,path=f'azureml:{model.name}:{model.version}'),'test':Input(type=AssetTypes.URI_FILE,path=str(ROOT/'ml/export/test/data.csv'))},outputs={'report':Output(type=AssetTypes.URI_FOLDER)},environment=env,compute='cpu-cluster',experiment_name='contoso-delay-evaluation')
        evaluated=ml.jobs.create_or_update(evaluate);ml.jobs.stream(evaluated.name)
        download=ROOT/'artifacts/azure/evaluation'/run.info.run_id;ml.jobs.download(evaluated.name,download_path=str(download),output_name='report')
        files=list(download.rglob('metrics.json'))
        if len(files)!=1:raise RuntimeError('Evaluation did not produce one metrics.json. Inspect the job logs.')
        report=json.loads(files[0].read_text());provenance=info['provenance']
        documents.append({'id':run.info.run_id,'modelName':'delay-classifier','algorithm':run.data.params.get('algorithm',run.data.tags.get('model_name','AutoML candidate')),'datasetRows':provenance['rows'],'delayRate':provenance['delayRate'],'metrics':report['metrics'],'crossValidationAuc':run.data.metrics['AUC_weighted'],'features':FEATURES,'featureImportance':report['featureImportance'],'endpointName':None,'deployed':False,'trainedAt':datetime.fromtimestamp(run.info.start_time/1000,timezone.utc).isoformat(),'source':'Azure-AutoML','registeredModel':f'azureml:{model.name}:{model.version}','evaluationJob':evaluated.name})
    save_json(ROOT/'artifacts/azure/model_runs.json',documents)
    save_json(ROOT/'evidence/azure-training.json',{'selectedBy':'AutoML training CV AUC_weighted; held-out metrics reported separately','runs':documents})
    print('Two Azure candidates evaluated. Review evidence/azure-training.json, then deploy the best candidate.')
if __name__=='__main__':main()
