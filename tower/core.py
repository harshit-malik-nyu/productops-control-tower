"""SQLite-backed work queue with expiring leases and fencing tokens."""
import hashlib
import json
import math
import sqlite3
import time
from contextlib import contextmanager

SCHEMA='''
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,payload TEXT NOT NULL,digest TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending',token INTEGER NOT NULL DEFAULT 0,
 worker TEXT,expires REAL,attempts INTEGER NOT NULL DEFAULT 0,remediates TEXT);
CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,account TEXT NOT NULL,kind TEXT NOT NULL,day TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS incidents(job_id TEXT PRIMARY KEY,reason TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'open',replacement TEXT);
CREATE TABLE IF NOT EXISTS reports(version INTEGER PRIMARY KEY,payload TEXT NOT NULL,digest TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT NOT NULL,detail TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS jobs_state_lease ON jobs(state,expires);
CREATE INDEX IF NOT EXISTS events_day_account ON events(day,account);
'''

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()

class Tower:
    def __init__(self,path):
        self.db=sqlite3.connect(path,timeout=20,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript(SCHEMA)
    def close(self):self.db.close()
    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:yield;self.db.execute('COMMIT')
        except BaseException:self.db.execute('ROLLBACK');raise
    def log(self,action,detail):
        self.db.execute('INSERT INTO audit(action,detail) VALUES (?,?)',(action,canonical(detail)))
    def enqueue(self,job_id,events,remediates=None):
        if not isinstance(job_id,str) or not job_id.strip():raise ValueError('Job ID required')
        if len(job_id)>128 or not isinstance(events,list) or len(events)>10000:raise ValueError('Job size limit exceeded')
        encoded=canonical(events);sha=digest(events)
        with self.transaction():
            old=self.db.execute('SELECT digest,remediates FROM jobs WHERE id=?',(job_id,)).fetchone()
            if old:
                if old['digest']!=sha or old['remediates']!=remediates:raise ValueError('Job identity reused with changed content')
                return 'replay'
            if remediates and not self.db.execute("SELECT 1 FROM incidents WHERE job_id=? AND state='open'",(remediates,)).fetchone():raise ValueError('Open incident required')
            self.db.execute('INSERT INTO jobs(id,payload,digest,remediates) VALUES (?,?,?,?)',(job_id,encoded,sha,remediates))
            self.log('queued',{'job':job_id,'digest':sha})
        return 'queued'
    def claim(self,worker,now=None,lease_seconds=30):
        now=time.time() if now is None else now
        if not math.isfinite(now):raise ValueError('Finite clock required')
        if not worker or not 0<lease_seconds<=300:raise ValueError('Worker and lease of 0..300 seconds required')
        with self.transaction():
            for exhausted in self.db.execute("SELECT id FROM jobs WHERE state='running' AND expires<=? AND attempts>=3",(now,)).fetchall():
                self.db.execute("UPDATE jobs SET state='failed' WHERE id=?",(exhausted['id'],))
                self.db.execute("INSERT INTO incidents(job_id,reason) VALUES (?,'Lease retry budget exhausted')",(exhausted['id'],))
                self.log('retry_exhausted',{'job':exhausted['id']})
            job=self.db.execute("SELECT * FROM jobs WHERE state='pending' OR (state='running' AND expires<=?) ORDER BY id LIMIT 1",(now,)).fetchone()
            if job is None:return None
            token=job['token']+1
            self.db.execute("UPDATE jobs SET state='running',token=?,worker=?,expires=?,attempts=attempts+1 WHERE id=?",(token,worker,now+lease_seconds,job['id']))
            self.log('claimed',{'job':job['id'],'worker':worker,'token':token})
            return {'id':job['id'],'token':token,'worker':worker}
    def owned(self,lease,now):
        if not math.isfinite(now):raise ValueError('Finite clock required')
        job=self.db.execute('SELECT * FROM jobs WHERE id=?',(lease['id'],)).fetchone()
        if not job or job['state']!='running' or job['token']!=lease['token'] or job['worker']!=lease['worker'] or job['expires']<=now:
            raise ValueError('Expired or superseded lease')
        return job
    def renew(self,lease,now=None,lease_seconds=30):
        now=time.time() if now is None else now
        if not 0<lease_seconds<=300:raise ValueError('Invalid lease duration')
        with self.transaction():
            self.owned(lease,now)
            self.db.execute('UPDATE jobs SET expires=? WHERE id=?',(now+lease_seconds,lease['id']))
    @staticmethod
    def validate(event):
        from datetime import date
        if not isinstance(event,dict) or set(event)!={'id','account','kind','day'}:raise ValueError('Event schema mismatch')
        if any(not isinstance(event[k],str) or not event[k].strip() for k in event):raise ValueError('Nonempty string fields required')
        if event['kind'] not in ('view','purchase'):raise ValueError('Unknown event kind')
        if date.fromisoformat(event['day']).isoformat()!=event['day']:raise ValueError('Canonical date required')
    def complete(self,lease,now=None):
        clock=now
        now=time.time() if now is None else now
        try:
            with self.transaction():
                if clock is None:now=time.time()
                job=self.owned(lease,now);events=json.loads(job['payload'])
                if not isinstance(events,list) or not events:raise ValueError('Nonempty event list required')
                inserted=duplicates=0
                for event in events:
                    self.validate(event);encoded=canonical(event)
                    old=self.db.execute('SELECT payload FROM events WHERE id=?',(event['id'],)).fetchone()
                    if old:
                        if old['payload']!=encoded:raise ValueError('Conflicting event identity')
                        duplicates+=1
                    else:
                        self.db.execute('INSERT INTO events VALUES (?,?,?,?,?)',(event['id'],event['account'],event['kind'],event['day'],encoded));inserted+=1
                if clock is None:self.owned(lease,time.time())
                self.db.execute("UPDATE jobs SET state='done' WHERE id=?",(lease['id'],))
                self.log('completed',{'job':lease['id'],'inserted':inserted,'duplicates':duplicates})
                return {'status':'done','inserted':inserted,'duplicates':duplicates}
        except ValueError as error:
            # Stale workers cannot fail the job or open an incident for its new owner.
            with self.transaction():
                self.owned(lease,time.time() if clock is None else now)
                self.db.execute("UPDATE jobs SET state='failed' WHERE id=?",(lease['id'],))
                self.db.execute('INSERT INTO incidents(job_id,reason) VALUES (?,?)',(lease['id'],str(error)))
                self.log('rejected',{'job':lease['id'],'reason':str(error)})
            return {'status':'failed','reason':str(error)}
    def resolve(self,incident,replacement):
        with self.transaction():
            old=self.db.execute("SELECT 1 FROM incidents WHERE job_id=? AND state='open'",(incident,)).fetchone()
            job=self.db.execute("SELECT 1 FROM jobs WHERE id=? AND state='done' AND remediates=?",(replacement,incident)).fetchone()
            if not old or not job:raise ValueError('A completed linked replacement is required')
            self.db.execute("UPDATE incidents SET state='resolved',replacement=? WHERE job_id=?",(replacement,incident))
            self.log('incident_resolved',{'incident':incident,'replacement':replacement})
    def metrics(self):
        return [dict(r) for r in self.db.execute("SELECT day,count(*) AS events,count(DISTINCT account) AS accounts,count(DISTINCT CASE WHEN kind='purchase' THEN account END) AS buyers FROM events GROUP BY day ORDER BY day")]
    def publish(self):
        with self.transaction():
            if self.db.execute("SELECT 1 FROM jobs WHERE state IN ('pending','running') LIMIT 1").fetchone():raise ValueError('Incomplete work blocks release')
            if self.db.execute("SELECT 1 FROM incidents WHERE state='open' LIMIT 1").fetchone():raise ValueError('Open incident blocks release')
            if not self.db.execute('SELECT 1 FROM events LIMIT 1').fetchone():raise ValueError('No data to publish')
            payload={'daily':self.metrics(),'metric':'daily distinct buyers / observed accounts; not a causal conversion estimate',
                     'source_digest':digest([dict(r) for r in self.db.execute('SELECT id,payload FROM events ORDER BY id')])}
            sha=digest(payload);old=self.db.execute('SELECT version FROM reports WHERE digest=?',(sha,)).fetchone()
            if old:return old['version']
            version=self.db.execute('SELECT coalesce(max(version),0)+1 FROM reports').fetchone()[0]
            self.db.execute('INSERT INTO reports VALUES (?,?,?)',(version,canonical(payload),sha))
            self.log('published',{'version':version,'digest':sha});return version
    def snapshot(self):
        r=self.db.execute('SELECT version,payload,digest FROM reports ORDER BY version DESC LIMIT 1').fetchone()
        return {'jobs':[dict(x) for x in self.db.execute('SELECT id,state,token,attempts,remediates FROM jobs ORDER BY id')],
                'incidents':[dict(x) for x in self.db.execute('SELECT * FROM incidents ORDER BY job_id')],
                'trusted_report':None if r is None else {'version':r['version'],'digest':r['digest'],**json.loads(r['payload'])},
                'audit':[dict(x) for x in self.db.execute('SELECT * FROM audit ORDER BY id')]}

def worker(path,name):
    tower=Tower(path)
    try:
        while lease:=tower.claim(name):tower.complete(lease)
    finally:tower.close()
