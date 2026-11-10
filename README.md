# ProductOps Control Tower

**A runnable product reliability work sample linking data engineering, business decisions and product delivery.** It is an independent synthetic demonstration—not a client deployment, a user study, an AI agent, or a production SLA claim.

[Interactive replay](https://portfolio-lac-five-10.vercel.app/projects/productops-control-tower/) · [Architecture](docs/architecture.md) · [Decision brief](docs/decision-brief.md) · [Delivery playbook](docs/delivery.md)

## The decision

Can a team publish its behavioral metrics after a failed delivery? The system retains immutable reports, fences expired workers, rejects conflicting events atomically, opens incidents, and blocks publication until queued work and incident remediation are complete. Replayed events do not inflate counts.

## Run it

Python 3.11–3.13; standard library only. No account, database service or paid API is needed.

```sh
python -m unittest discover -s tests -v
python -m tower.demo
python -m tower.load --rows 100000 --output /tmp/control-tower-load.json
python -m http.server 8000 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:8000` for the recorded viewer. The backend is the `tower.core.Tower` Python API, exercised directly by tests and demo generation. The website is not a live control-plane API and cannot submit approvals.

```python
from tower.core import Tower
with_path = Tower('/tmp/control-tower.sqlite')
try:
    with_path.enqueue('batch-1', [{'id':'e1','account':'synthetic-1','kind':'view','day':'2026-01-01'}])
    lease = with_path.claim('worker-1')
    with_path.complete(lease)
    version = with_path.publish()
    print(with_path.snapshot())
finally:
    with_path.close()
```

## Evidence

- 19 regression tests include an actual process exit, concurrent worker processes, lease fencing, retry exhaustion, atomic rollback, incident linkage, late events and immutable history.
- `evidence/demo.json` is rebuilt by executing six stages, not manually inventing success states. CI requires byte-identical regeneration.
- `evidence/load.json` preserves one local 100,000-event measurement with environment and source hashes. Timings vary; CI uploads its own measurement rather than pretending it is identical.
- Events reconcile to an independent expected count. Worker distribution is reported, including workers that claimed no jobs. Four started processes do not establish parallel write throughput.

## Responsibilities demonstrated

| Data engineering | Business analysis | Product operations |
|---|---|---|
| SQL constraints and event grain | Alternatives and explicit economics | Incident-to-replacement linkage |
| Leases, fencing and bounded retries | Recommendation-changing conditions | Acceptance tests and release gates |
| Idempotent ingestion and history | Assumptions and limitations | Triage, handover and post-release checks |

## Important boundaries

SQLite on one host serializes writes. There is no PostgreSQL cluster, distributed broker, production identity provider, network failover, authenticated operator interface, measured uptime, external-user feedback or independently verified business impact. Deliberate record correction and privacy deletion propagation are not implemented. A field allowlist is not a compliance certification. Queued/rejected payloads remain in the local database; use synthetic inputs only. The public replay excludes job payloads.

Publish requires queue completion and resolved incidents; it cannot prove an external source is complete or fresh. Timestamps and source watermarks, multi-tenant authorization, real approvals and recovery-point objectives require a separate production design. `resolve` validates a linked completed replacement; it does not prove a person approved it or that the business cause was fixed.

The work is designed to be inspected and challenged, not to substitute for experience claims.
