# Stage201: PoC Design Doc (Internal)

MIT License © 2025 Motohiro Suzuki

---

**Stage201** provides an internal PoC design document plus an executable runner that:

- models deployment environments (QKD / Hybrid)
- defines operational profiles
- specifies failure behavior and logging
- binds PoC outputs to **Stage191 CI evidence** and **Claim(required_jobs)**

> Internal document. Not intended as a public-facing implementation spec.

---

## Purpose

This stage is a design-level executable specification.

It validates:

1. Operational profile consistency
2. Failure injection intent logging
3. Fail-closed binding to Stage191 CI results
4. Claim(required_jobs) satisfaction

This PoC does **NOT** implement a production protocol.  
It ensures traceability and audit alignment.

---

## Fail-Closed Behavior

The runner exits with error if:

- Stage191 CI outputs are missing or unreadable
- any Stage191 CI job failed
- any claim’s `required_jobs` is not satisfied
- a profile invariant is violated
- failure injection is requested but the profile disallows it

No “green PoC log” can exist without green CI evidence.

---

## Repository Structure

- `poc_design.md`
- `environments/`
- `profiles/`
- `failure_models/`
- `logging/`
- `metrics/`
- `runtime/`
- `tools/`

Generated outputs (ignored by Git):

- `out/poc_logs/poc.jsonl`
- `out/reports/poc_report.md`

---

## Requirements

- Python 3.10+

Optional dependency (if needed by YAML parsing tools):

```bash
python3 -m pip install --user pyyaml
Run

Baseline (no failure):

python3 runtime/poc_runner.py --profile hybrid_balanced --failure none
tail -n 30 out/poc_logs/poc.jsonl

Inject failure (allowed only when profile enables it, e.g. resilience_test):

python3 runtime/poc_runner.py --profile resilience_test --failure downgrade
tail -n 50 out/poc_logs/poc.jsonl
Stage191 Binding Inputs

Default paths:

~/Desktop/test/stage191/out/ci

~/Desktop/test/stage191/claims/claims.yaml

Override example:

python3 runtime/poc_runner.py \
  --profile hybrid_balanced \
  --failure none \
  --stage191-ci-dir ~/Desktop/test/stage191/out/ci \
  --stage191-claims ~/Desktop/test/stage191/claims/claims.yaml
Logged Events

poc_start / poc_end

failure_injected

stage191_ci_summary

stage191_ci_gate_passed / stage191_ci_gate_failed

claim_required_jobs_eval

claim_gate_passed / claim_gate_failed

metrics_snapshot

PoC Report (Internal)

Generate a human-readable report from the latest PoC run log (out/poc_logs/poc.jsonl):

python3 tools/generate_poc_report.py
sed -n '1,200p' out/reports/poc_report.md

Notes:

This report is internal (PoC design stage).

Next step: convert placeholders into measured values (latency/availability) and attach evidence paths.

License

This project is licensed under the MIT License.

See LICENSE for details.
EOF