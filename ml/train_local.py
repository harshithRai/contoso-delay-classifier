"""Honest local baseline. This does not satisfy the Azure training requirement."""
import argparse
from datetime import datetime, timezone
import hashlib
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.inspection import permutation_importance
from common import ROOT, FEATURES, load_data, split, evaluate, save_json

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',default=str(ROOT/'data/contoso_delay_training.csv'))
    args=parser.parse_args(); frame=load_data(args.data); train,test=split(frame)
    output=ROOT/'artifacts/local';output.mkdir(parents=True,exist_ok=True)
    models={
        'LogisticRegression':LogisticRegression(max_iter=1500,random_state=42),
        'RandomForest':RandomForestClassifier(n_estimators=200,min_samples_leaf=10,class_weight='balanced_subsample',random_state=42,n_jobs=-1)
    }
    runs=[]; trained={}; now=datetime.now(timezone.utc).isoformat()
    for name,estimator in models.items():
        preprocessing=ColumnTransformer([('carrier',OneHotEncoder(handle_unknown='ignore'),['carrier']),('numeric',StandardScaler(),FEATURES[1:])])
        model=Pipeline([('preprocess',preprocessing),('classifier',estimator)])
        cv=cross_val_score(model,train[FEATURES],train.delayed,cv=StratifiedKFold(3,shuffle=True,random_state=42),scoring='roc_auc')
        model.fit(train[FEATURES],train.delayed);trained[name]=model
        runs.append({'id':f'local-{name}-{now[:10]}','modelName':'delay-classifier','algorithm':name,'datasetRows':len(frame),'delayRate':float(frame.delayed.mean()),'metrics':evaluate(model,test),'crossValidationAuc':float(cv.mean()),'features':FEATURES,'endpointName':None,'deployed':False,'trainedAt':now,'source':'local-baseline','trainRows':len(train),'testRows':len(test),'randomSeed':42})
    # Select by training cross-validation, never by the untouched test set.
    runs.sort(key=lambda r:r['crossValidationAuc'],reverse=True)
    best=trained[runs[0]['algorithm']]
    importance=permutation_importance(best,test[FEATURES],test.delayed,scoring='roc_auc',n_repeats=5,random_state=42)
    joblib.dump(best,output/'model.joblib')
    save_json(output/'model_runs.json',runs)
    report={'source':'local-baseline','datasetSha256':hashlib.sha256(open(args.data,'rb').read()).hexdigest(),'selectedBy':'3-fold training CV AUC','best':runs[0],'runnerUp':runs[1],'featureImportance':dict(sorted(zip(FEATURES,importance.importances_mean.tolist()),key=lambda x:x[1],reverse=True))}
    save_json(ROOT/'evidence/local-training.json',report)
    groups={}
    for field in ['carrier','is_sale_day','backlog_bucket']:
        data=frame.assign(backlog_bucket=frame.warehouse_backlog.apply(lambda x:'under 30' if x<30 else '30–49' if x<50 else '50+'))
        groups[field]=data.groupby(field).delayed.agg(['count','sum','mean']).reset_index().to_dict(orient='records')
    save_json(ROOT/'evidence/local-analysis.json',{'source':'CSV analysis; Azure SQL evidence pending','rows':len(frame),'delayed':int(frame.delayed.sum()),'delayRate':float(frame.delayed.mean()),'groups':groups})
    print(f'Local baseline selected: {runs[0]["algorithm"]}')
    for r in runs: print(r['algorithm'],r['metrics'])
    print('Saved artifacts/local/model.joblib and evidence/local-training.json. These are LOCAL results.')

if __name__=='__main__':main()
