"""Generate replay through actual queue execution, not manually authored results."""
import json
import tempfile
from pathlib import Path
from .core import Tower

def event(i,kind='view',day='2026-01-01'):return {'id':str(i),'account':'a'+str(i),'kind':kind,'day':day}
def build():
    with tempfile.TemporaryDirectory() as d:
        t=Tower(str(Path(d)/'demo.db'));frames=[]
        def record(title,explanation):frames.append({'title':title,'explanation':explanation,**t.snapshot()})
        def process(job,events,remediates=None):
            t.enqueue(job,events,remediates);return t.complete(t.claim('worker',now=100),now=101)
        try:
            process('baseline',[event(1),event(2,'purchase')]);t.publish()
            record('Trusted baseline','Two accounts, one buyer. Report version 1 is published after all work completes.')
            process('duplicate-delivery',[event(1),event(2,'purchase')]);assert t.publish()==1
            record('Duplicate delivery','A different job redelivers identical events. No extra rows or report version appear.')
            process('bad-schema',[event(3),{**event(4),'email':'not-allowed@example.invalid'}])
            try:t.publish()
            except ValueError:pass
            record('Incident opened; release blocked','An unexpected email field fails the allowlist. The entire batch rolls back; the last trusted report remains version 1.')
            process('corrected-batch',[event(3),event(4)],remediates='bad-schema')
            record('Replacement verified','Corrected data commits, but the incident is still open. A successful job alone does not authorize publication.')
            t.resolve('bad-schema','corrected-batch');t.publish()
            record('Controlled release','The linked replacement is complete, the incident is resolved, and report version 2 is published.')
            t.enqueue('late-purchase',[event(5,'purchase')]);stale=t.claim('lost-worker',now=200,lease_seconds=1)
            recovered=t.claim('recovery-worker',now=202)
            try:t.complete(stale,now=202)
            except ValueError:pass
            t.complete(recovered,now=203);t.publish()
            record('Lease recovery and restatement','An expired worker is fenced out. A replacement worker completes the late purchase; historical counts are restated in version 3.')
            return {'scope':'Executed synthetic local demonstration. Replay only; no customer incident, user study or production SLA claim.','frames':frames}
        finally:t.close()
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];data=build()
    (root/'evidence/demo.json').write_text(json.dumps(data,indent=2)+'\n')
    (root/'site/index.html').write_text((root/'site/template.html').read_text().replace('__DATA__',json.dumps(data,separators=(',',':')).replace('<','\\u003c')))
    print('Six executed incident-to-release frames generated.')
