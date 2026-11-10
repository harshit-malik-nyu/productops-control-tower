# Requirements and acceptance traceability

Proposed needs and owners for an independent sample; these are not interview findings or stakeholder sign-offs.

| ID | Need / decision | Executable evidence | Unverified requirement |
|---|---|---|---|
| D1 | Assigned accounts remain in denominator | `test_hand_calculated_totals` | Source identity and assignment audit |
| D2 | Unknown outcomes must be visible | `test_missing_bounds`, `test_missing_alone_blocks` | Collection design and acceptable completeness |
| D3 | Support harm overrides vanity growth | `test_harm_overrides_economics` | Support owner agreement to ceiling |
| D4 | Invalid comparisons block interpretation | `test_assignment_imbalance`, sparse and invalid count tests | Real randomization, maturity and interference |
| D5 | Passing analysis leads to review | `test_eligible_not_auto_shipped` | Approval, access control and release integration |
| D6 | Economics must expose assumptions | Generated economic scenarios | Actual costs and contribution estimates |
| D7 | Recovery cannot corrupt trusted reports | Core tests for conflicts, leases and immutable history | Distributed/network failure testing |

## Prioritization
P0: identity, assignment, fixed outcome window, data contract and harm/completeness gates. P1: support-reason taxonomy, consented research, then a new hypothesis. P2: convenience and polish. Do not invent reach/confidence scores to justify priorities.

## Hypothetical scope negotiation
A growth owner may want rollout because conversion and modeled returns improve. A support owner may oppose it because workload doubles. Proposed resolution: hold using a previously agreed harm ceiling, redesign, then independently test. No conversation, consensus, influence or adoption is claimed. This demonstrates a negotiation structure, not client experience.

## Change control
Changing the metric, threshold, eligibility or observation window requires a new policy version and rationale. Post-result changes are exploratory and require independent validation. Rebuild outputs; CI detects drift. Preserve prior report versions. Actual stakeholder approval is not implemented by this work sample.

## Research protocol — not conducted
Recruit consenting analysts, support operators and product owners who use the workflow. Ask them to locate the trusted report, explain the block, find supporting evidence and identify the next action. Record task completion, errors and comprehension with consent and without customer-sensitive data. Ask neutral questions before showing the solution. Code confusion, missing evidence and workflow barriers while preserving disagreement. Obtain actual observations before claiming usability improvement; no fabricated quotes or research results.

## UAT
1. Bad schema preserves prior report and opens an incident.
2. Successful replacement alone does not close the incident.
3. Positive conversion plus excess harm remains HOLD.
4. Removing harm but retaining uncertainty remains HOLD.
5. Complete beneficial evidence becomes ELIGIBLE_FOR_REVIEW, never auto-release.
6. Rebuild evidence from source and compare hashes.

See `tests/test_analysis.py` and `docs/delivery.md`. Client influence, organizational adoption and live support ownership remain unverified.
