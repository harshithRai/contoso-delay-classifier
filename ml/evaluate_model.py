"""Runs on Azure compute in the AutoML model's own conda environment."""
import argparse
import json
from pathlib import Path
import mlflow.sklearn
import pandas as pd
from sklearn.inspection import permutation_importance
from common import FEATURES,evaluate

p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--test',required=True);p.add_argument('--out',required=True);args=p.parse_args()
model=mlflow.sklearn.load_model(args.model)
test=pd.read_csv(args.test)
report={'metrics':evaluate(model,test),'testRows':len(test),'source':'Azure-held-out-evaluation'}
importance=permutation_importance(model,test[FEATURES],test.delayed,scoring='roc_auc',n_repeats=5,random_state=42)
report['featureImportance']=dict(sorted(zip(FEATURES,importance.importances_mean.tolist()),key=lambda x:x[1],reverse=True))
out=Path(args.out);out.mkdir(parents=True,exist_ok=True);(out/'metrics.json').write_text(json.dumps(report,indent=2))
