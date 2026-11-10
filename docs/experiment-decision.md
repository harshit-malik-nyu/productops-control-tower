# Conversion is insufficient to authorize rollout

**Decision: HOLD.** Captured conversion improves, but support burden breaches the policy and unknown conversion outcomes can reverse the sign. Resolve measurement completeness and investigate support friction before evaluating a new iteration. Positive modeled returns cannot override these gates.

This is a deliberately designed synthetic policy stress test, not a real randomized experiment, preregistration or customer result. Thresholds are illustrative design choices, not validated stakeholder preferences.

## Measurement contract
Hypothetical assignment is 50:50 at the account level with an immutable arm and a fixed 14-day outcome window. Include every assigned eligible account in the denominator. Repeated sessions are not independent experimental units. Exclude bots/employees before assignment; do not filter on post-assignment behavior. Support is binary per account, not ticket count.

The aggregate fixture cannot verify randomization, identity deduplication, observation maturity, exposure compliance or lack of interference. Those require upstream evidence. Unknown outcomes are not actual nonconverters. The displayed metric is captured conversions / assigned accounts. Causal conversion inference additionally requires complete or justifiably modeled measurement.

## Reproduce
Run `python -m tower.analysis` and `python -m unittest discover -s tests -v`. Inspect `evidence/experiment.json`: it records the fixture and analysis SHA-256 hashes. Alter fixture counts to challenge the policy; never relabel this exercise as real measured impact.

Control: 1,200 / 10,000 (12%); treatment: 1,350 / 10,000 (13.5%). Difference: +1.5 percentage points, or 12.5% relative. Support affects 1% versus 2%, a +1 pp harm increase. Balanced assignment totals do not prove correct randomization.

## Statistical method and gates
An approximate unpooled normal 95% interval is difference ± z × sqrt[pC(1−pC)/nC + pT(1−pT)/nT], using the standard-normal 97.5th percentile. Code rejects cells with fewer than ten successes or failures. This assumes independent Bernoulli outcomes and is a marginal large-sample approximation, not an exact or simultaneous interval. Clustering, sparse data, repeated looks and interference require other methods.

Primary lower bound must exceed +0.5 pp; support upper bound must not exceed +0.5 pp. A 50:50 sample-ratio chi-square check (one degree of freedom) must have p ≥ .001. Missing-outcome bounds must preserve the minimum benefit. Passing means ELIGIBLE_FOR_REVIEW, never automatic shipment. Gates do not create a joint 95% guarantee. A real test needs prospectively fixed hypotheses, multiplicity handling, power analysis, duration covering business cycles and no optional stopping.

Each arm has 200 unknown conversion outcomes. Assigning all unknown control outcomes to conversion and unknown treatment outcomes to nonconversion gives −0.5 pp; reversing gives +3.5 pp. These are worst-case identification bounds, not confidence intervals, and exclude sampling uncertainty. Even before sampling uncertainty, measurement incompleteness makes rollout fragile.

## Alternative explanations and segments
New-account observed lift is +2 pp; returning-account lift is +1 pp. These are exploratory; different estimates do not prove a segment interaction. Do not launch to a favorable subgroup without a fresh hypothesis and validation. Segment weights are balanced by construction. Acquisition mix, logging changes, seasonality, concurrent releases and support capture can explain real-world differences. Assignment integrity and instrumentation audits are required to distinguish them.

## Economics and recommendation-changing assumptions
Assume 100,000 eligible accounts/month, $40 contribution per incremental conversion, $15 per incremental account needing support, $5,000 monthly incremental operation, and $30,000 implementation. Point-case net is $40,000/month with 0.75-month payback. This is hypothetical run-rate arithmetic, not realized ROI. It assumes stable effects and excludes tax, churn, discounting and downstream value.

Generated downside/point/upside cases combine marginal interval endpoints. They are sensitivities, not a joint confidence region or probability forecast. Missing-outcome downside at −0.5 pp is a loss even before most costs. The hold therefore supersedes favorable point economics.

## Next decision
Audit capture and complete outcomes; investigate support friction through consented research; redesign a smaller change; register a fresh experiment and sample-size plan; then review efficacy, harm, quality and economics together. No interviews, stakeholder agreements or production results are claimed here.
