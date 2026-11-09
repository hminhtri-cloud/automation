# IAM Boto3 Auditor

This folder contains read-only checks for IAM controls 2.4, 2.5, 2.7, 2.8,
2.9, 2.10, 2.11, 2.12, 2.13, 2.14, and 2.18.

The code does not create, update, disable, delete, or attach any IAM resource.
Permission failures are reported as `ERROR`, not as `PASS`.

## Run

From this folder, with valid AWS Academy credentials:

```bash
python main.py --region us-east-1 --regions us-east-1 --output reports/iam.json
```

The report contains one finding per control, except control 2.18, which returns
one finding per enabled Region.

## Required read permissions

Depending on the account policy, the audit may need permission for:

- IAM credential report, password policy, users, groups, roles, and policy metadata.
- `iam:GetPolicyVersion` for control 2.14.
- CloudTrail `LookupEvents` for control 2.7.
- EC2 `DescribeRegions` and Access Analyzer `ListAnalyzers` for control 2.18.

If AWS Academy denies `iam:GetPolicyVersion`, control 2.14 is intentionally
reported as `ERROR` because the policy contents cannot be verified.

Control 2.7 is always `MANUAL` after collecting CloudTrail evidence because an
automated check cannot decide whether a root event was an approved break-glass
operation.  The default CloudTrail lookback is 90 days.
# automation
