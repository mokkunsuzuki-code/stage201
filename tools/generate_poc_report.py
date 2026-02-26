# MIT License © 2025 Motohiro Suzuki
"""
Stage201: Generate a human-readable PoC report from out/poc_logs/poc.jsonl.

- Input:  out/poc_logs/poc.jsonl (JSONL)
- Output: out/reports/poc_report.md

This is an internal document generator (PoC design stage).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "out" / "poc_logs" / "poc.jsonl"
OUT_MD = ROOT / "out" / "reports" / "poc_report.md"


@dataclass
class RunSummary:
    ts_start: str
    ts_end: str
    profile: str
    failure: str
    stage191_repo: str
    stage191_run_id: str
    jobs_count: int
    all_success: bool
    claims_total: int
    claims_passed: int
    claims_all_passed: bool
    claim_items: Dict[str, Any]
    metrics: Dict[str, Any]


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"missing log: {path}")
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _ts_to_dt(ts: str) -> datetime:
    # format like: 2026-02-26T19:11:45+0900
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")


def _extract_last_run(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Identify last "poc_start" index, then slice until last element.
    start_idx = None
    for i in range(len(events) - 1, -1, -1):
        if events[i].get("event") == "poc_start":
            start_idx = i
            break
    if start_idx is None:
        raise ValueError("no poc_start found in log")
    return events[start_idx:]


def _find_event(run_events: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for e in run_events:
        if e.get("event") == name:
            return e
    return None


def _fmt_bool(b: bool) -> str:
    return "PASS" if b else "FAIL"


def _mk_claim_table(items: Dict[str, Any]) -> str:
    # items: { "A2": {...}, ... }
    keys = sorted(items.keys())
    lines = []
    lines.append("| Claim | Passed | Required Jobs | Missing Jobs |")
    lines.append("|---|---:|---|---|")
    for k in keys:
        row = items.get(k, {})
        passed = bool(row.get("passed"))
        req = row.get("required_jobs") or []
        miss = row.get("missing_jobs") or []
        req_s = ", ".join(req) if req else "-"
        miss_s = ", ".join(miss) if miss else "-"
        lines.append(f"| `{k}` | **{_fmt_bool(passed)}** | {req_s} | {miss_s} |")
    return "\n".join(lines)


def main() -> None:
    events = _read_jsonl(LOG_PATH)
    run = _extract_last_run(events)

    e_start = run[0]
    e_end = None
    for e in reversed(run):
        if e.get("event") == "poc_end":
            e_end = e
            break

    if e_end is None:
        raise ValueError("no poc_end found after last poc_start")

    ts_start = e_start.get("ts", "")
    ts_end = e_end.get("ts", "")

    start_details = (e_start.get("details") or {})
    profile = str(start_details.get("profile", "unknown"))

    e_failure = _find_event(run, "failure_injected")
    failure = "unknown"
    if e_failure:
        failure = str((e_failure.get("details") or {}).get("requested", "unknown"))

    e_ci = _find_event(run, "stage191_ci_summary")
    if not e_ci:
        raise ValueError("missing stage191_ci_summary in last run")
    ci_d = e_ci.get("details") or {}
    stage191_repo = str(ci_d.get("repo", "unknown"))
    stage191_run_id = str(ci_d.get("run_id", "unknown"))
    jobs_count = int(ci_d.get("jobs_count", 0))
    all_success = bool(ci_d.get("all_success", False))

    e_claim = _find_event(run, "claim_required_jobs_eval")
    if not e_claim:
        raise ValueError("missing claim_required_jobs_eval in last run")
    claim_d = e_claim.get("details") or {}
    summary = claim_d.get("summary") or {}
    claims_total = int(summary.get("claims_total", 0))
    claims_passed = int(summary.get("claims_passed", 0))
    claims_all_passed = bool(summary.get("all_passed", False))
    claim_items = claim_d.get("items") or {}

    e_metrics = _find_event(run, "metrics_snapshot")
    metrics = (e_metrics.get("details") if e_metrics else {}) or {}

    rs = RunSummary(
        ts_start=ts_start,
        ts_end=ts_end,
        profile=profile,
        failure=failure,
        stage191_repo=stage191_repo,
        stage191_run_id=stage191_run_id,
        jobs_count=jobs_count,
        all_success=all_success,
        claims_total=claims_total,
        claims_passed=claims_passed,
        claims_all_passed=claims_all_passed,
        claim_items=claim_items,
        metrics=metrics,
    )

    dt0 = _ts_to_dt(rs.ts_start) if rs.ts_start else None
    dt1 = _ts_to_dt(rs.ts_end) if rs.ts_end else None
    dur_s = None
    if dt0 and dt1:
        dur_s = (dt1 - dt0).total_seconds()

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("# Stage201 PoC Report (Internal)")
    lines.append("")
    lines.append("> Generated from `out/poc_logs/poc.jsonl`")
    lines.append("")
    lines.append("## Run Summary")
    lines.append("")
    lines.append(f"- Start: `{rs.ts_start}`")
    lines.append(f"- End: `{rs.ts_end}`")
    if dur_s is not None:
        lines.append(f"- Duration: `{dur_s:.3f}s`")
    lines.append(f"- Profile: `{rs.profile}`")
    lines.append(f"- Failure: `{rs.failure}`")
    lines.append("")
    lines.append("## Stage191 CI Binding")
    lines.append("")
    lines.append(f"- Repo: `{rs.stage191_repo}`")
    lines.append(f"- Run ID: `{rs.stage191_run_id}`")
    lines.append(f"- Jobs count: `{rs.jobs_count}`")
    lines.append(f"- CI gate: **{_fmt_bool(rs.all_success)}**")
    lines.append("")
    lines.append("## Claim Gate (required_jobs)")
    lines.append("")
    lines.append(f"- Claims: `{rs.claims_passed}/{rs.claims_total}`")
    lines.append(f"- Claim gate: **{_fmt_bool(rs.claims_all_passed)}**")
    lines.append("")
    lines.append(_mk_claim_table(rs.claim_items))
    lines.append("")
    lines.append("## Metrics Snapshot (placeholders)")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(rs.metrics, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report is **internal** (PoC design stage).")
    lines.append("- Next step: convert placeholders into measured values (latency/availability) and attach evidence paths.")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] wrote: {OUT_MD}")


if __name__ == "__main__":
    main()
