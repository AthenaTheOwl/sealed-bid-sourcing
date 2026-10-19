# A modeled markup difference is a conditional result

Method update: October 18, 2026. Proposed experiments below are not reported as executed results.

The sealed/unsealed benchmark changes how supplier bids are constructed under its modeled disclosure assumptions. Its surplus difference answers a conditional simulator question. It does not identify the causal effect of disclosure on actual suppliers, and a receipt allowlist alone does not establish a cryptographic leakage proof.

The next proposed experiment should separate information exposure from behavior. Hold true costs, capacities, lots and random draws fixed. First compare identical bids under different receipt visibility to measure disclosure only. Then apply the stated behavioral markup rule and attribute the additional price difference to that rule. Report unallocated lots alongside spend and surplus so infeasibility cannot appear as buyer savings.

Vary the markup rule and include a zero-markup control. If the claimed gain disappears under that control, describe the gain as dependent on modeled supplier response. Production MPC and strategic guarantees remain outside the v0.1 result. Preserve scenario hash, rule version and both receipts so a behavior-rule change invalidates only the corresponding comparison. The v0.1 code cannot do this yet. The markup is stored per supplier inside the scenario (`defensive_markup_pct`), so changing it also changes the sealed receipt's `scenario_hash`, and `schemas/receipt.schema.json` has no rule-version field and rejects extra fields. The experiment first needs the markup rule moved out of the scenario, or hashed separately, and a rule-version receipt field added to the schema.

Update, October 19, 2026: the zero-markup control now runs with every surplus report (`reports/surplus_delta.md`, `reports/surplus_delta_v1.md`). The delta is 0.00 under it in both scenarios, so the reported gain depends entirely on the modeled markup.
