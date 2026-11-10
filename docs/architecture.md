# Architecture and contracts

## Execution

Producers enqueue immutable job IDs and payload hashes. Independent Python worker processes acquire leases using `BEGIN IMMEDIATE`. A monotonically increasing token fences prior owners. Completion validates ownership again inside the write transaction, inserts or deduplicates events, and changes job state atomically. A rejected job rolls back every event and opens an incident in a separate fenced transaction. Expired leases can be reclaimed; three exhausted attempts create an incident.

SQLite WAL permits readers with a serialized writer. This is a single-machine concurrency design, not a distributed database. Worker count does not imply write-speed improvement.

## Grains

- Job: immutable `id` plus canonical payload hash and optional remediation link. Same ID/content is replay; changed content is rejected.
- Event: immutable `id`; account, kind and canonical date. Only `view` and `purchase` are accepted. There is no monetary transaction processing.
- Metric: per-day distinct accounts and distinct purchasing accounts. Do not sum daily distinct accounts into period uniques.
- Report: immutable version, source digest, daily metrics and explicit metric definition. Equivalent input state does not generate another version.
- Incident: rejected job, machine-readable reason and a completed replacement job linked explicitly to the failure.

## Release gate

No pending/running job and no open incident may exist. Empty datasets are rejected. A replacement job completing does not itself resolve the incident. The local operator must call `resolve`, which checks its link and completion. Publication then records a new report only if the source state differs. Failed refreshes never mutate the preceding report. This is a dataset publication gate, not an authenticated software-release approval service.

## Recovery and data limits

A worker process can exit after claim; another worker reclaims after expiry with a higher token. Old workers cannot complete or fail the new owner's job. The test kills a process; it does not simulate a power outage, corrupted disk or multi-region partition. Arbitrary malformed events are rejected; unknown fields, including an email field, cannot enter the event table. Raw queued payloads remain local and require a production retention policy. This demonstration must use synthetic data.

No external completeness or freshness is inferred from an empty queue. Future source integration needs explicit producer watermarks and clock assumptions. Late events restate historical days in a new version, without rewriting old reports. Deletion/correction, backpressure, fair scheduling, retry backoff, durable notifications and migration tooling remain production work.

## Evolution options

To move to PostgreSQL, preserve transaction/fencing semantics and use row-level work claiming with a tested isolation strategy. Introduce a durable broker only when workload evidence justifies operational complexity. Partition by an explicit key with a global identity reconciliation strategy; do not sum partition-local distinct counts blindly. Test failover, skew, duplicates, reordering, network partition and deletion propagation before claiming distributed reliability.
