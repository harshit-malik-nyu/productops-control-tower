import multiprocessing as mp
import os
import tempfile
import unittest
from pathlib import Path
from tower.core import Tower,worker
from tower.demo import event,build

def die_after_claim(path):
    t=Tower(path);t.claim('crashed-process',now=0,lease_seconds=1);os._exit(7)

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=str(Path(self.temp.name)/'tower.db');self.t=Tower(self.path)
    def tearDown(self):self.t.close();self.temp.cleanup()
    def process(self,job,events,remediates=None):
        self.t.enqueue(job,events,remediates);return self.t.complete(self.t.claim('w',now=10),now=11)
    def test_job_replay(self):
        self.process('j',[event(1)]);self.assertEqual(self.t.enqueue('j',[event(1)]),'replay');self.assertIsNone(self.t.claim('w',now=20))
    def test_changed_job_id_rejected(self):
        self.t.enqueue('j',[event(1)])
        with self.assertRaises(ValueError):self.t.enqueue('j',[event(2)])
    def test_duplicate_events_across_jobs(self):
        self.process('a',[event(1)]);self.process('b',[event(1)]);self.assertEqual(self.t.metrics()[0]['events'],1)
    def test_conflict_rolls_back_entire_batch(self):
        self.process('a',[event(1)]);self.t.publish()
        self.assertEqual(self.process('b',[event(2),{**event(1),'account':'other'}])['status'],'failed');self.assertEqual(self.t.metrics()[0]['events'],1)
        with self.assertRaises(ValueError):self.t.publish()
        self.assertEqual(self.t.snapshot()['trusted_report']['version'],1)
    def test_unexpected_field_rejected(self):
        self.assertEqual(self.process('a',[{**event(1),'email':'x'}])['status'],'failed');self.assertEqual(self.t.metrics(),[])
    def test_bad_date_rejected(self):self.assertEqual(self.process('a',[event(1,day='not-a-date')])['status'],'failed')
    def test_pending_work_blocks_release(self):
        self.process('a',[event(1)]);self.t.enqueue('b',[event(2)])
        with self.assertRaises(ValueError):self.t.publish()
    def test_no_empty_release(self):
        with self.assertRaises(ValueError):self.t.publish()
    def test_lease_fences_stale_worker(self):
        self.t.enqueue('a',[event(1)]);old=self.t.claim('old',now=0,lease_seconds=1);new=self.t.claim('new',now=2)
        with self.assertRaises(ValueError):self.t.complete(old,now=2)
        self.assertEqual(self.t.complete(new,now=3)['status'],'done');self.assertEqual(self.t.snapshot()['incidents'],[])
    def test_expiry_exact_boundary(self):
        self.t.enqueue('a',[event(1)]);lease=self.t.claim('w',now=0,lease_seconds=1)
        with self.assertRaises(ValueError):self.t.complete(lease,now=1)
    def test_renewal(self):
        self.t.enqueue('a',[event(1)]);lease=self.t.claim('w',now=0,lease_seconds=2);self.t.renew(lease,now=1,lease_seconds=5);self.assertIsNone(self.t.claim('other',now=3));self.t.complete(lease,now=4)
    def test_incident_requires_linked_completed_replacement(self):
        self.process('bad',[{}]);self.process('unrelated',[event(1)])
        with self.assertRaises(ValueError):self.t.resolve('bad','unrelated')
        self.process('repair',[event(2)],remediates='bad');self.t.resolve('bad','repair');self.assertEqual(self.t.publish(),1)
    def test_publish_idempotent(self):
        self.process('a',[event(1)]);self.assertEqual(self.t.publish(),1);self.assertEqual(self.t.publish(),1)
    def test_late_event_retains_history(self):
        self.process('a',[event(1)]);self.t.publish();old=self.t.db.execute('SELECT payload FROM reports WHERE version=1').fetchone()[0]
        self.process('b',[event(2,'purchase')]);self.t.publish();self.assertEqual(old,self.t.db.execute('SELECT payload FROM reports WHERE version=1').fetchone()[0]);self.assertEqual(self.t.snapshot()['trusted_report']['version'],2)
    def test_actual_process_death_reclaim(self):
        self.t.enqueue('a',[event(1)]);p=mp.get_context('spawn').Process(target=die_after_claim,args=(self.path,));p.start();p.join(15)
        if p.is_alive():p.terminate();p.join();self.fail('Crash process hung')
        self.assertEqual(p.exitcode,7);lease=self.t.claim('recovery',now=2);self.assertEqual(lease['token'],2);self.t.complete(lease,now=3)
    def test_four_worker_processes(self):
        for i in range(20):self.t.enqueue(f'job-{i:02}',[event(i)])
        ps=[mp.get_context('spawn').Process(target=worker,args=(self.path,f'w{i}')) for i in range(4)]
        for p in ps:p.start()
        for p in ps:
            p.join(20)
            if p.is_alive():p.terminate();p.join();self.fail('Worker hung')
            self.assertEqual(p.exitcode,0)
        self.assertEqual(self.t.metrics()[0]['events'],20);self.assertTrue(all(j['attempts']==1 for j in self.t.snapshot()['jobs']));self.t.publish()
    def test_retry_budget_opens_incident(self):
        self.t.enqueue('a',[event(1)])
        for tick in (0,2,4):self.assertIsNotNone(self.t.claim('w',now=tick,lease_seconds=1))
        self.assertIsNone(self.t.claim('w',now=6));self.assertEqual(self.t.snapshot()['jobs'][0]['state'],'failed')
        self.assertEqual(self.t.snapshot()['incidents'][0]['reason'],'Lease retry budget exhausted')
    def test_no_nan_clock(self):
        with self.assertRaises(ValueError):self.t.claim('w',now=float('nan'))
    def test_demo_reproducible(self):self.assertEqual(build(),build())

if __name__=='__main__':unittest.main()
