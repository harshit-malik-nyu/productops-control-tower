# Decision brief: reliable metrics before reactive spending

## Recommendation
Adopt a guarded publication workflow for a pilot, with operational ownership and representative workload tests before production. A visible report is not necessarily current or trustworthy. Preserve the previous version during investigation, label its age in a real deployment, and treat ingestion errors separately from changes in customer behavior.

## Alternatives

| Option | Strength | Cost / failure mode | Decision |
|---|---|---|---|
| Manual spreadsheets and ad hoc refresh | Low setup effort | Inconsistent identity rules; weak repeatability | Retain only as a reconciliation reference |
| Guarded local queue and immutable reports | Reproducible contracts and cheap failure experiments | One host; serialized writes; no production auth | Chosen work-sample pilot |
| Managed warehouse and durable broker | Potential isolation and operational scale | More services, cost and failure surfaces | Evaluate after workload and service objectives are measured |

## Economics: assumptions, not results

At 8 incidents/month × 2 hours saved × $60/hour, gross assumed labor benefit is $960/month. At $200 assumed monthly operating cost, net benefit is $760/month before implementation. A hypothetical $3,000 implementation costs about 3.95 months of that benefit. At only 2 incidents/month, net benefit drops to $40/month and payback becomes 75 months. At zero incidents, the assumed net is negative $200/month. This sensitivity argues for validating baseline effort before funding infrastructure.

No avoided revenue loss is monetized: no empirical basis exists. The demo's corrected counts are not conversion uplift. Hardware and labor are resources even when no paid API is used.

## Workstream

1. Establish decision owner, metric grain, source contract and completeness definition.
2. Measure current manual effort, error frequency and acceptable reporting age.
3. Implement and test identity, lease, incident and publication gates.
4. Conduct representative load/failure tests and user task review.
5. Agree on operating ownership, escalation, retention and rollback before production use.

All roles are proposed; no stakeholder interviews or business adoption are claimed. Evidence that changes the recommendation includes lower incident cost, higher integration cost, multi-writer contention, privacy requirements or stricter freshness needs.
