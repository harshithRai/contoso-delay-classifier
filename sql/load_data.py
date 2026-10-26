import argparse
import csv
import json
import re
from pathlib import Path
from connection import connect

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--csv',default=str(ROOT/'data/contoso_delay_training.csv'));args=p.parse_args()
    with open(args.csv,newline='') as f:
        reader=csv.DictReader(f);columns=reader.fieldnames;rows=list(reader)
    expected=['carrier','distance_km','weight_kg','items','order_hour','is_sale_day','warehouse_backlog','weather_index','delayed']
    if columns!=expected or len(rows)!=10000: raise ValueError('Wrong dataset or schema.')
    with connect() as cn:
        cursor=cn.cursor()
        for filename in ['create_table.sql','view.sql']:
            for batch in re.split(r'^GO\s*$',(ROOT/'sql'/filename).read_text(),flags=re.M):
                if batch.strip():cursor.execute(batch)
        cursor.execute('SELECT COUNT(*) FROM dbo.OrderHistory');count=cursor.fetchone()[0]
        if count: raise RuntimeError(f'Table contains {count} rows. Import stopped to prevent duplicates; inspect it before retrying.')
        values=[(r['carrier'],int(r['distance_km']),float(r['weight_kg']),int(r['items']),int(r['order_hour']),int(r['is_sale_day']),int(r['warehouse_backlog']),float(r['weather_index']),int(r['delayed'])) for r in rows]
        if hasattr(cursor,'fast_executemany'):
            cursor.fast_executemany=True
            for start in range(0,len(values),1000):cursor.executemany(f"INSERT INTO dbo.OrderHistory ({','.join(expected)}) VALUES (?,?,?,?,?,?,?,?,?)",values[start:start+1000])
        else:
            # Parameterized OPENJSON batches avoid one network round trip per row.
            definitions="carrier NVARCHAR(20), distance_km INT, weight_kg DECIMAL(6,2), items INT, order_hour TINYINT, is_sale_day BIT, warehouse_backlog INT, weather_index DECIMAL(5,3), delayed BIT"
            statement=f"INSERT INTO dbo.OrderHistory ({','.join(expected)}) SELECT {','.join(expected)} FROM OPENJSON(%s) WITH ({definitions})"
            for start in range(0,len(values),1000):
                payload=json.dumps([dict(zip(expected,row)) for row in values[start:start+1000]])
                cursor.execute(statement,(payload,))
        cn.commit()
        queries=(ROOT/'sql/analysis.sql').read_text().split(';');results=[]
        for q in queries:
            if not q.strip():continue
            cursor.execute(q);names=[c[0] for c in cursor.description];results.append([dict(zip(names,row)) for row in cursor.fetchall()])
        (ROOT/'evidence/azure-sql-analysis.json').write_text(json.dumps({'source':'Azure SQL ml.DelayTraining','results':results},indent=2,default=str)+'\n')
        print('Imported 10,000 rows. Azure SQL query results saved in evidence/azure-sql-analysis.json.')
if __name__=='__main__':main()
