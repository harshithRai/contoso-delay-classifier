"""Loopback scorer with Azure ML's input_data shape; local testing only."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import joblib
import pandas as pd
from common import ROOT, FEATURES

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=7072);args=parser.parse_args()
    model=joblib.load(ROOT/'artifacts/local/model.joblib')
    class Handler(BaseHTTPRequestHandler):
        def respond(self,code,body):
            data=json.dumps(body).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
        def do_GET(self):self.respond(200,{'mode':'local'})
        def do_POST(self):
            if self.path!='/score':return self.respond(404,{'error':'Not found'})
            if self.headers.get('Authorization')!='Bearer '+os.environ.get('LOCAL_MODEL_KEY','local-development-only'):return self.respond(401,{'error':'Unauthorized'})
            try:
                raw=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))['input_data']
                frame=pd.DataFrame(raw['data'],columns=raw['columns'])[FEATURES]
                self.respond(200,{'prediction':model.predict(frame).astype(int).tolist()})
            except Exception:self.respond(400,{'error':'Invalid scoring input'})
        def log_message(self,*args):pass
    print(f'Local trained-model scorer: http://127.0.0.1:{args.port}/score',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

if __name__=='__main__':main()
