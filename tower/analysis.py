"""Reproducible synthetic experiment decision; standard library only."""
import hashlib
import html
import json
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
Z = NormalDist().inv_cdf(.975)
POLICY = {'minimum_lift': .005, 'maximum_support_increase': .005, 'srm_alpha': .001}

def validate(rows):
    if not rows:
        raise ValueError('Empty experiment')
    seen = set()
    for r in rows:
        if set(r) != {'segment','arm','assigned','converted','support','missing'}:
            raise ValueError('Unexpected fields')
        key = (r['segment'], r['arm'])
        if not isinstance(r['segment'],str) or not r['segment'] or r['arm'] not in ('control','treatment') or key in seen:
            raise ValueError('Invalid or duplicate segment-arm')
        seen.add(key)
        for k in ('assigned','converted','support','missing'):
            if type(r[k]) is not int or r[k] < 0:
                raise ValueError('Counts must be nonnegative integers')
        if r['assigned'] == 0 or r['converted'] + r['missing'] > r['assigned'] or r['support'] > r['assigned']:
            raise ValueError('Impossible counts')
    for segment, _ in seen:
        if (segment,'control') not in seen or (segment,'treatment') not in seen:
            raise ValueError('Each segment needs both arms')

def difference(c, nc, t, nt):
    """Unpooled large-sample normal interval; sparse data is rejected, not approximated."""
    if any(type(x) is not int for x in (c,nc,t,nt)) or min(nc,nt)<=0 or not 0<=c<=nc or not 0<=t<=nt:
        raise ValueError('Invalid binomial counts')
    if min(c,nc-c,t,nt-t)<10:
        raise ValueError('Sparse counts require a different interval method')
    pc,pt=c/nc,t/nt
    se=math.sqrt(pc*(1-pc)/nc+pt*(1-pt)/nt)
    return {'control_rate':pc,'treatment_rate':pt,'difference':pt-pc,
            'lower_95':pt-pc-Z*se,'upper_95':pt-pc+Z*se}

def analyze(rows):
    validate(rows)
    totals={arm:{k:sum(r[k] for r in rows if r['arm']==arm) for k in ('assigned','converted','support','missing')} for arm in ('control','treatment')}
    c,t=totals['control'],totals['treatment']
    def metric(key):return difference(c[key],c['assigned'],t[key],t['assigned'])
    primary,support=metric('converted'),metric('support')
    expected=(c['assigned']+t['assigned'])/2
    chi=sum((x['assigned']-expected)**2/expected for x in (c,t))
    srm_p=math.erfc(math.sqrt(chi/2)) # chi-square survival, one degree of freedom
    bounds={'lower':t['converted']/t['assigned']-(c['converted']+c['missing'])/c['assigned'],
            'upper':(t['converted']+t['missing'])/t['assigned']-c['converted']/c['assigned']}
    reasons=[]
    if srm_p<POLICY['srm_alpha']:reasons.append('Assignment imbalance: investigate randomization before interpretation')
    if primary['lower_95']<=POLICY['minimum_lift']:reasons.append('Primary lift lower bound does not clear minimum practical benefit')
    if support['upper_95']>POLICY['maximum_support_increase']:reasons.append('Support harm upper bound exceeds the allowed increase')
    if bounds['lower']<=POLICY['minimum_lift']:reasons.append('Missing-outcome sensitivity does not preserve the decision')
    segments=[]
    for segment in sorted({r['segment'] for r in rows}):
        a={r['arm']:r for r in rows if r['segment']==segment}
        segments.append({'segment':segment,**difference(a['control']['converted'],a['control']['assigned'],a['treatment']['converted'],a['treatment']['assigned'])})
    # Economic scenarios use declared assumptions, not causal ROI or a joint confidence region.
    cases=[]
    for name,lift,burden in [('downside',primary['lower_95'],support['upper_95']),('point',primary['difference'],support['difference']),('upside',primary['upper_95'],support['lower_95'])]:
        net=100000*(lift*40-burden*15)-5000
        cases.append({'scenario':name,'monthly_net_assumption':net,'payback_months_assumption':30000/net if net>0 else None})
    return {'scope':'Synthetic policy stress test; no real randomized trial or customer outcome.',
            'policy':POLICY,'totals':totals,'primary':primary,'support':support,'srm_p':srm_p,
            'missing_outcome_bounds':bounds,'segments_exploratory':segments,
            'decision':'HOLD' if reasons else 'ELIGIBLE_FOR_REVIEW','reasons':reasons,'economics_scenarios':cases}

def section(r):
    p,g=r['primary'],r['support']
    pp=lambda x:f'{100*x:.2f} pp'
    reasons=''.join('<li>'+html.escape(s)+'</li>' for s in r['reasons'])
    return f'''<section class="section" id="experiment"><p class="eyebrow">New / Data + business + product decision</p><h2>Conversion improved. Should we ship?</h2><p>Synthetic 20,000-account policy stress test. These are generated case inputs, not a real experiment or customer result.</p><div class="grid"><article class="card"><h3>Primary lift</h3><div class="number">+{pp(p['difference'])}</div><p>Approximate 95% interval: {pp(p['lower_95'])} to {pp(p['upper_95'])}.</p></article><article class="card"><h3>Support burden</h3><div class="number">+{pp(g['difference'])}</div><p>Upper bound {pp(g['upper_95'])}; allowed increase 0.50 pp.</p></article><article class="card"><h3>Recommendation</h3><div class="number">{r['decision']}</div><p>Positive conversion and positive modeled economics cannot override a failed guardrail.</p></article></div><ul>{reasons}</ul><p>Missing-outcome identification bounds: {pp(r['missing_outcome_bounds']['lower'])} to {pp(r['missing_outcome_bounds']['upper'])}; these are not confidence intervals. Segment results are exploratory.</p><p><a href="https://github.com/harshit-malik-nyu/productops-control-tower/blob/main/docs/experiment-decision.md">Read the analysis and decision protocol →</a> · <a href="https://github.com/harshit-malik-nyu/productops-control-tower/blob/main/evidence/experiment.json">Inspect calculated evidence →</a> · <a href="https://github.com/harshit-malik-nyu/productops-control-tower/blob/main/docs/requirements.md">Trace requirements to tests →</a></p></section>'''

def build():
    source=ROOT/'fixtures/experiment.json'
    r=analyze(json.loads(source.read_text())['rows'])
    r['input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    r['analysis_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (ROOT/'evidence/experiment.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    return r

if __name__=='__main__':
    print(json.dumps(build(),indent=2))
