"""Runs on Azure compute in the AutoML model's own conda environment."""
import argparse
import json
import os
from pathlib import Path
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from common import FEATURES,evaluate

p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--test',required=True);p.add_argument('--out',required=True);args=p.parse_args()
model=mlflow.sklearn.load_model(args.model)
test=pd.read_csv(args.test)
steps=getattr(model,'steps',[])
algorithm=type(steps[-1][1]).__name__ if steps else type(model).__name__
report={'metrics':evaluate(model,test),'testRows':len(test),'source':'Azure-held-out-evaluation','algorithm':algorithm}
def positive_auc(estimator,features,labels):
    probabilities=np.asarray(estimator.predict_proba(features))[:,list(estimator.classes_).index(1)]
    return roc_auc_score(labels,probabilities)
importance=permutation_importance(model,test[FEATURES],test.delayed,scoring=positive_auc,n_repeats=5,random_state=42)
report['featureImportance']=dict(sorted(zip(FEATURES,importance.importances_mean.tolist()),key=lambda x:x[1],reverse=True))
out=Path(args.out);out.mkdir(parents=True,exist_ok=True);(out/'metrics.json').write_text(json.dumps(report,indent=2))
MlflowClient().log_artifact(os.environ['AZUREML_RUN_ID'],str(out/'metrics.json'),artifact_path='evaluation')
