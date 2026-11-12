"""Command line interface for the orphan volume detector."""

import argparse
import json
import sys

from .orphan import SEVERITY_ORDER, analyze_inventory

EXIT_HIGH_FINDINGS = 2
EXIT_INPUT_ERROR = 1
EXIT_OK = 0


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def _render(findings, n_volumes):
    lines = []
    counts = {level: 0 for level in SEVERITY_ORDER}
    for finding in findings:
        counts[finding.severity] += 1
        lines.append(f"[{finding.severity:<6}] {finding.rule_id} {finding.subject}: {finding.message}")
    lines.append(
        "summary: {high} high, {medium} medium, {low} low finding(s) across {n} volume(s)".format(
            high=counts["HIGH"], medium=counts["MEDIUM"], low=counts["LOW"], n=n_volumes
        )
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="oci-block-volume-orphan-detector",
        description="Offline orphan/hygiene detection for OCI Block Volume inventories.",
    )
    parser.add_argument("path", help="volume inventory JSON")
    args = parser.parse_args(argv)

    try:
        document = _load(args.path)
        findings = analyze_inventory(document)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    print(_render(findings, len(document.get("volumes", []))))
    if any(f.severity == "HIGH" for f in findings):
        return EXIT_HIGH_FINDINGS
    return EXIT_OK
