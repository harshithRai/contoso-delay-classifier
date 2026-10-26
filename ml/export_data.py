"""Cloud training data must come from the SQL VIEW, never directly from the CSV."""
import hashlib
import os
import sys
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sql'))
from connection import connect
from common import ROOT, FEATURES, split, save_json

def main():
    with connect() as cn:
        cursor=cn.cursor();cursor.execute('SELECT '+','.join(FEATURES+['delayed'])+' FROM ml.DelayTraining ORDER BY carrier, distance_km, weight_kg, items, order_hour, is_sale_day, warehouse_backlog, weather_index, delayed')
        frame=pd.DataFrame.from_records(cursor.fetchall(),columns=FEATURES+['delayed'])
    frame=frame.astype({k:'float64' if k in ['weight_kg','weather_index'] else 'int64' for k in FEATURES[1:]+['delayed']})
    if len(frame)!=10000:raise ValueError('Expected 10,000 SQL rows.')
    out=ROOT/'ml/export';out.mkdir(parents=True,exist_ok=True);frame.to_csv(out/'full.csv',index=False)
    train,test=split(frame)
    for name,data in [('train',train),('test',test)]:
        folder=out/name;folder.mkdir(exist_ok=True);data.to_csv(folder/'data.csv',index=False)
        (folder/'MLTable').write_text((ROOT/'ml/MLTable').read_text())
    save_json(out/'provenance.json',{'source':'Azure SQL ml.DelayTraining','server':os.environ['SQL_SERVER'],'rows':len(frame),'delayRate':float(frame.delayed.mean()),'exportedAt':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256((out/'full.csv').read_bytes()).hexdigest(),'trainRows':len(train),'testRows':len(test),'randomSeed':42})
    print('Exported SQL view: 8,000 training rows, 2,000 untouched test rows. Both MLTable folders include their CSV.')
if __name__=='__main__':main()
