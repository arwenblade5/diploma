#!/usr/bin/env python3
"""
Security Gateway for diploma DevSecOps pipeline.

The script aggregates JSON/SARIF reports from SAST, DAST, SCA, secret scanning
and image/config scanning. It produces a machine-readable decision and a
Markdown summary for pull requests. The release is blocked when thresholds are
exceeded.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SEVERITIES = ("critical", "high", "medium", "low", "info")

RECOMMENDATIONS = {
    "semgrep": "Review the source location, confirm exploitability, and fix the vulnerable data flow. Add a regression test for the same pattern.",
    "trivy-image": "Upgrade the affected OS package or base image. Rebuild the image and verify that the CVE disappears from the scan.",
    "trivy-fs": "Fix the insecure IaC/container configuration or dependency. Prefer least privilege and explicit versions.",
    "npm-audit": "Upgrade the vulnerable npm package, use npm audit fix only after reviewing breaking changes, and regenerate package-lock.json.",
    "gitleaks": "Rotate the leaked secret immediately, remove it from history if required, and replace hardcoded values with CI/CD secrets.",
    "zap": "Reproduce the finding against staging, fix the HTTP/application control, then rerun the baseline scan.",
    "generic": "Triage the finding, assign an owner, set SLA by severity, and retest after remediation.",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def add_count(counts: Dict[str, int], severity: str, amount: int = 1) -> None:
    severity = (severity or "info").lower()
    if severity not in counts:
        severity = "info"
    counts[severity] += amount


def count_sarif(path: Path) -> Tuple[Dict[str, int], List[str]]:
    counts = {s: 0 for s in SEVERITIES}
    examples: List[str] = []
    data = load_json(path)
    if not data:
        return counts, examples
    for run in data.get("runs", []):
        rules = {r.get("id"): r for r in run.get("tool", {}).get("driver", {}).get("rules", [])}
        for result in run.get("results", []):
            level = (result.get("level") or "warning").lower()
            severity = {"error": "high", "warning": "medium", "note": "low", "none": "info"}.get(level, "medium")
            rule_id = result.get("ruleId", "unknown-rule")
            rule = rules.get(rule_id, {})
            props = rule.get("properties", {}) if isinstance(rule, dict) else {}
            sec = props.get("security-severity") or props.get("precision")
            if isinstance(sec, str):
                try:
                    if float(sec) >= 9:
                        severity = "critical"
                    elif float(sec) >= 7:
                        severity = "high"
                    elif float(sec) >= 4:
                        severity = "medium"
                except ValueError:
                    pass
            add_count(counts, severity)
            if len(examples) < 10:
                msg = result.get("message", {}).get("text", "finding")
                examples.append(f"{rule_id}: {msg[:180]}")
    return counts, examples


def count_trivy(path: Path) -> Tuple[Dict[str, int], List[str]]:
    counts = {s: 0 for s in SEVERITIES}
    examples: List[str] = []
    data = load_json(path)
    if not data:
        return counts, examples
    for result in data.get("Results", []) or []:
        target = result.get("Target", "target")
        for vuln in result.get("Vulnerabilities", []) or []:
            severity = vuln.get("Severity", "UNKNOWN").lower()
            add_count(counts, severity)
            if len(examples) < 10:
                vid = vuln.get("VulnerabilityID", "CVE")
                pkg = vuln.get("PkgName", "package")
                fixed = vuln.get("FixedVersion") or "no fixed version in report"
                examples.append(f"{vid} in {pkg} on {target}; fixed: {fixed}")
        for mis in result.get("Misconfigurations", []) or []:
            severity = mis.get("Severity", "UNKNOWN").lower()
            add_count(counts, severity)
            if len(examples) < 10:
                examples.append(f"{mis.get('ID', 'misconfig')}: {mis.get('Title', 'configuration issue')}")
        for secret in result.get("Secrets", []) or []:
            add_count(counts, "high")
            if len(examples) < 10:
                examples.append(f"secret: {secret.get('RuleID', 'secret')} in {target}")
    return counts, examples


def count_npm_audit(path: Path) -> Tuple[Dict[str, int], List[str]]:
    counts = {s: 0 for s in SEVERITIES}
    examples: List[str] = []
    data = load_json(path)
    if not data:
        return counts, examples
    metadata = data.get("metadata", {})
    vulns = metadata.get("vulnerabilities") or {}
    for sev in SEVERITIES:
        add_count(counts, sev, int(vulns.get(sev, 0) or 0))
    for name, item in (data.get("vulnerabilities") or {}).items():
        if len(examples) >= 10:
            break
        via = item.get("via") or []
        via_text = via[0].get("title") if via and isinstance(via[0], dict) else "dependency advisory"
        examples.append(f"{name}: {item.get('severity', 'unknown')} - {via_text}")
    return counts, examples


def count_gitleaks(path: Path) -> Tuple[Dict[str, int], List[str]]:
    counts = {s: 0 for s in SEVERITIES}
    examples: List[str] = []
    data = load_json(path)
    if isinstance(data, list):
        for leak in data:
            add_count(counts, "critical")
            if len(examples) < 10:
                examples.append(f"{leak.get('RuleID', 'secret')} in {leak.get('File', 'file')}:{leak.get('StartLine', '?')}")
    return counts, examples


def count_zap(path: Path) -> Tuple[Dict[str, int], List[str]]:
    counts = {s: 0 for s in SEVERITIES}
    examples: List[str] = []
    data = load_json(path)
    if not data:
        return counts, examples
    risk_map = {"3": "high", "2": "medium", "1": "low", "0": "info"}
    for site in data.get("site", []) or []:
        for alert in site.get("alerts", []) or []:
            severity = risk_map.get(str(alert.get("riskcode", "0")), "info")
            add_count(counts, severity)
            if len(examples) < 10:
                name = alert.get("alert", "ZAP alert")
                url = ""
                instances = alert.get("instances") or []
                if instances:
                    url = instances[0].get("uri", "")
                examples.append(f"{name} {url}".strip())
    return counts, examples


def merge_counts(target: Dict[str, int], source: Dict[str, int]) -> None:
    for sev in SEVERITIES:
        target[sev] += int(source.get(sev, 0) or 0)


def discover_reports(root: Path) -> List[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def classify_report(path: Path) -> str | None:
    name = path.name.lower()
    if name.endswith(".sarif"):
        return "semgrep" if "semgrep" in name else "sarif"
    if name == "trivy-image.json":
        return "trivy-image"
    if name == "trivy-fs.json":
        return "trivy-fs"
    if name == "npm-audit.json":
        return "npm-audit"
    if name == "gitleaks.json":
        return "gitleaks"
    if name == "zap.json":
        return "zap"
    return None


def summarize(root: Path) -> Dict[str, Any]:
    tools: Dict[str, Dict[str, Any]] = {}
    totals = {s: 0 for s in SEVERITIES}

    for path in discover_reports(root):
        kind = classify_report(path)
        if not kind:
            continue
        if kind in ("semgrep", "sarif"):
            counts, examples = count_sarif(path)
        elif kind in ("trivy-image", "trivy-fs"):
            counts, examples = count_trivy(path)
        elif kind == "npm-audit":
            counts, examples = count_npm_audit(path)
        elif kind == "gitleaks":
            counts, examples = count_gitleaks(path)
        elif kind == "zap":
            counts, examples = count_zap(path)
        else:
            continue

        key = kind
        tools[key] = {
            "file": str(path),
            "counts": counts,
            "examples": examples,
            "recommendation": RECOMMENDATIONS.get(key, RECOMMENDATIONS["generic"]),
        }
        merge_counts(totals, counts)

    return {"totals": totals, "tools": tools}


def make_decision(summary: Dict[str, Any], thresholds: Dict[str, int]) -> Dict[str, Any]:
    totals = summary["totals"]
    violations = []
    for sev in ("critical", "high", "medium"):
        max_allowed = thresholds[sev]
        if totals.get(sev, 0) > max_allowed:
            violations.append({"severity": sev, "actual": totals[sev], "allowed": max_allowed})
    decision = "block" if violations else "allow"
    return {"decision": decision, "violations": violations, "thresholds": thresholds}


def render_markdown(summary: Dict[str, Any], decision: Dict[str, Any]) -> str:
    totals = summary["totals"]
    status = "BLOCKED" if decision["decision"] == "block" else "ALLOWED"
    lines = [
        f"## Security Gateway result: {status}",
        "",
        "### Aggregated findings",
        "",
        "| Severity | Count | Allowed |",
        "|---|---:|---:|",
    ]
    for sev in ("critical", "high", "medium", "low", "info"):
        allowed = decision["thresholds"].get(sev, "-")
        lines.append(f"| {sev.upper()} | {totals.get(sev, 0)} | {allowed} |")
    lines.extend(["", "### Tool details", ""])
    for tool, info in sorted(summary["tools"].items()):
        c = info["counts"]
        lines.append(f"#### {tool}")
        lines.append(f"Counts: critical={c['critical']}, high={c['high']}, medium={c['medium']}, low={c['low']}, info={c['info']}.")
        lines.append(f"Recommendation: {info['recommendation']}")
        if info["examples"]:
            lines.append("Examples:")
            for ex in info["examples"][:5]:
                lines.append(f"- {ex}")
        lines.append("")
    if decision["violations"]:
        lines.append("### Release gate violations")
        for v in decision["violations"]:
            lines.append(f"- {v['severity'].upper()}: {v['actual']} findings, allowed {v['allowed']}.")
    else:
        lines.append("No blocking violations detected.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory with downloaded artifacts")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--critical-max", type=int, default=0)
    parser.add_argument("--high-max", type=int, default=0)
    parser.add_argument("--medium-max", type=int, default=20)
    args = parser.parse_args()

    summary = summarize(Path(args.input))
    thresholds = {"critical": args.critical_max, "high": args.high_max, "medium": args.medium_max}
    decision = make_decision(summary, thresholds)
    result = {"summary": summary, "gate": decision}

    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(summary, decision), encoding="utf-8")

    print(render_markdown(summary, decision))
    return 1 if decision["decision"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
