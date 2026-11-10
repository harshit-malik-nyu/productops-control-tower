# Product delivery and support playbook

## Backlog and acceptance

| Priority | User story | Acceptance | Executable evidence |
|---|---|---|---|
| P0 | As a consumer I need partial bad deliveries excluded | A later conflicting row rejects all rows in that job and retains report | `test_conflict_rolls_back_entire_batch` |
| P0 | As an operator I need crashed workers recoverable | A new owner reclaims expired work; stale token cannot commit | `test_actual_process_death_reclaim`, `test_lease_fences_stale_worker` |
| P0 | As a reviewer I need explicit incident closure | An unrelated or incomplete job cannot resolve the incident | `test_incident_requires_linked_completed_replacement` |
| P1 | As an analyst I need replay and late events separated | Exact duplicates do not inflate counts; late data gets a new report | `test_duplicate_events_across_jobs`, `test_late_event_retains_history` |
| P1 | As an operator I need bounded retry loops | Three expired claims open an incident | `test_retry_budget_opens_incident` |

## Incident drill

Detection: a schema violation or identity conflict changes a job to failed and opens an incident. Containment: dataset publication is blocked while the prior report remains unchanged. Triage: inspect the reason and source contract locally; do not paste real records into public issues. Remediation: enqueue a corrected batch with `remediates` set to the failed job. Verification: confirm completion and correct metrics, then explicitly resolve the linked incident. Release: publish a new version and verify its source digest and changed counts.

Example stakeholder update: “The refresh is blocked by an input-contract violation. The previous report remains unchanged. The source owner must provide a corrected batch; publication will remain blocked until verification and incident closure.” This is a sample, not a sent message or actual client communication.

## UAT and release checklist

Run the tests and regenerate the public evidence. Verify each of the six replay stages, the saved report version and the incident count. Review the metric denominator and late-event restatement. Inspect the cost model's assumptions. Record unresolved privacy, auth and completeness requirements. Production approval cannot be inferred from local CI success.

## Research protocol — not conducted

Ask reporting consumers to identify the trusted report after a failed delivery, explain why a completed replacement still needs incident closure, and distinguish late-data restatement from product uplift. Record observed behavior, interpretation and contradictory evidence separately. Do not fabricate participants, quotations or usability improvements. Critical misunderstanding of report status should block launch pending redesign and retest.

## v0.1 release notes

Implemented local worker leases, fencing, bounded retries, atomic event validation, incident linkage, immutable reports, executed replay generation and a four-process load experiment. The UI is a recorded evidence explorer with a scenario calculator. No production control API, external notifications, AI inference or enterprise approvals are included.
