"""Single-host multiprocessing measurement; no claim of distributed scaling."""
import argparse
import hashlib
import json
import multiprocessing as mp
import platform
import sqlite3
import tempfile
import time
from collections import Counter
from pathlib import Path
from .core import Tower,worker

def run(rows=100000,workers=4):
    if rows<1000 or rows%1000 or not 1<=workers<=8:raise ValueError('Use rows divisible by 1000 and 1..8 workers')
    with tempfile.TemporaryDirectory() as d:
        path=str(Path(d)/'load.db');t=Tower(path)
        try:
            begin=time.perf_counter()
            for start in range(0,rows,1000):
                t.enqueue(f'b{start:09}',[{'id':str(i),'account':f'a{i%10000}','kind':'purchase' if i%5==0 else 'view','day':'2026-01-01'} for i in range(start,start+1000)])
            queued=time.perf_counter()
            ps=[mp.get_context('spawn').Process(target=worker,args=(path,f'worker-{i}')) for i in range(workers)]
            for p in ps:p.start()
            for p in ps:
                p.join(120)
                if p.is_alive():p.terminate();p.join();raise RuntimeError('Worker exceeded 120 seconds')
                if p.exitcode!=0:raise RuntimeError('Worker failed')
            consumed=time.perf_counter();t.publish();done=time.perf_counter()
            observed=t.metrics()[0];expected={'day':'2026-01-01','events':rows,'accounts':min(rows,10000),'buyers':min(rows,10000)//5}
            if observed!=expected:raise AssertionError((observed,expected))
            snapshot=t.snapshot()
            if not all(j['state']=='done' and j['attempts']==1 for j in snapshot['jobs']):raise AssertionError('Queue did not complete exactly once in this run')
            ownership=Counter(r['worker'] for r in t.db.execute('SELECT worker FROM jobs'))
            return {'scope':'Synthetic single-host SQLite experiment. Four processes contend for one writer. No distributed throughput, multi-region reliability or production SLA claim.',
                    'rows':rows,'processes_started':workers,'jobs_by_worker':dict(ownership),'reconciled':True,'metrics':observed,
                    'seconds':{'enqueue':round(queued-begin,6),'consume':round(consumed-queued,6),'publish':round(done-consumed,6),'total':round(done-begin,6)},
                    'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'system':platform.system()},
                    'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}}
        finally:t.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rows',type=int,default=100000);p.add_argument('--output',default='evidence/load.json');a=p.parse_args()
    r=run(a.rows);Path(a.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
