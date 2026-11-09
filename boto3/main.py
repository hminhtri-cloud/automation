from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from iam_audit import audit_iam


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only IAM CIS control auditor")
    parser.add_argument("--region", default="us-east-1", help="Base Region used for regional IAM checks")
    parser.add_argument("--regions", nargs="+", default=None, help="Regions to inspect for Root CloudTrail activity")
    parser.add_argument("--root-activity-days", type=int, default=90)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path")
    args = parser.parse_args()

    try:
        session = boto3.Session(region_name=args.region)
        regions = args.regions or [args.region]
        findings = audit_iam(session, regions, args.root_activity_days)
    except (ClientError, BotoCoreError) as error:
        print(f"AWS audit failed: {error}", file=sys.stderr)
        return 1

    report = json.dumps(findings, indent=2, ensure_ascii=False)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
