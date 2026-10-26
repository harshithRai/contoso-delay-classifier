"""Rank CV runs, register top two, and evaluate both on untouched SQL test data."""
import json
import os
import time
import yaml
from datetime import datetime,timezone
from pathlib import Path
import mlflow
from mlflow.tracking import MlflowClient
from azure.ai.ml import command,Input,Output
from azure.ai.ml.entities import Model,Environment,CommandJobLimits
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
    # Reuse the exact curated runtime that ran AutoML, when available.
    # Rebuilding its exported full conda environment is slower and can drift.
    jobs_path=ROOT/'artifacts/azure/evaluation-jobs.json'
    evaluation_jobs=json.loads(jobs_path.read_text()) if jobs_path.exists() else {}
    documents=[]
    for rank,run in enumerate(runs[:2]):
        model_folder=Path(mlflow.artifacts.download_artifacts(run_id=run.info.run_id,artifact_path='outputs/mlflow-model',dst_path=str(ROOT/'artifacts/azure/downloads'/run.info.run_id)))
        model=ml.models.create_or_update(Model(name='contoso-delay',version=f'{info["datasetVersion"]}{rank}',path=str(model_folder),type=AssetTypes.MLFLOW_MODEL))
        conda=model_folder/'conda.yaml'
        if not conda.exists():raise FileNotFoundError('AutoML model conda.yaml missing; inspect its MLflow artifact before evaluation.')
        metadata=yaml.safe_load((model_folder/'MLmodel').read_text()).get('metadata',{})
        training_image=metadata.get('azureml.base_image')
        if training_image and not training_image.startswith('mcr.microsoft.com/azureml/'):
            raise ValueError('Inspect the model base image before using a non-Azure runtime.')
        env=Environment(image=training_image) if training_image else Environment(image='mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest',conda_file=str(conda))
        cached=evaluation_jobs.get(run.info.run_id)
        evaluated=ml.jobs.get(cached) if cached else None
        if not evaluated or evaluated.status in ['Failed','Canceled','NotResponding']:
            evaluate=command(code=str(ROOT/'ml'),command='python evaluate_model.py --model ${{inputs.model}} --test ${{inputs.test}} --out ${{outputs.report}}',inputs={'model':Input(type=AssetTypes.MLFLOW_MODEL,path=f'azureml:{model.name}:{model.version}'),'test':Input(type=AssetTypes.URI_FILE,path=str(ROOT/'ml/export/test/data.csv'))},outputs={'report':Output(type=AssetTypes.URI_FOLDER)},environment=env,environment_variables={'MLFLOW_TRACKING_URI':workspace.mlflow_tracking_uri},compute=os.environ.get('AZURE_ML_EVALUATION_COMPUTE','cpu-cluster'),experiment_name='contoso-delay-evaluation',limits=CommandJobLimits(timeout=1800))
            evaluated=ml.jobs.create_or_update(evaluate)
            evaluation_jobs[run.info.run_id]=evaluated.name;save_json(jobs_path,evaluation_jobs)
        previous=None
        while True:
            evaluated=ml.jobs.get(evaluated.name)
            if evaluated.status!=previous:print(f'Evaluation {evaluated.name}: {evaluated.status}',flush=True);previous=evaluated.status
            if evaluated.status in ['Completed','Failed','Canceled','NotResponding']:break
            time.sleep(10)
        if evaluated.status!='Completed':raise RuntimeError(f'Evaluation {evaluated.name} ended {evaluated.status}; inspect its MLflow user_logs artifacts.')
        download=ROOT/'artifacts/azure/evaluation'/run.info.run_id
        mlflow.artifacts.download_artifacts(run_id=evaluated.name,artifact_path='evaluation/metrics.json',dst_path=str(download))
        files=list(download.rglob('metrics.json'))
        if len(files)!=1:raise RuntimeError('Evaluation did not produce one metrics.json. Inspect the job logs.')
        report=json.loads(files[0].read_text());provenance=info['provenance']
        documents.append({'id':run.info.run_id,'modelName':'delay-classifier','algorithm':report['algorithm'],'datasetRows':provenance['rows'],'delayRate':provenance['delayRate'],'metrics':report['metrics'],'crossValidationAuc':run.data.metrics['AUC_weighted'],'features':FEATURES,'featureImportance':report['featureImportance'],'endpointName':None,'deployed':False,'trainedAt':datetime.fromtimestamp(run.info.start_time/1000,timezone.utc).isoformat(),'source':'Azure-AutoML','registeredModel':f'azureml:{model.name}:{model.version}','evaluationJob':evaluated.name,'trainingImage':training_image})
        save_json(ROOT/'artifacts/azure/model_runs.partial.json',documents)
    save_json(ROOT/'artifacts/azure/model_runs.json',documents)
    save_json(ROOT/'evidence/azure-training.json',{'selectedBy':'AutoML training CV AUC_weighted; held-out metrics reported separately','runs':documents})
    print('Two Azure candidates evaluated. Review evidence/azure-training.json, then deploy the best candidate.')
if __name__=='__main__':main()
