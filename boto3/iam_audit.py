"""Read-only IAM checks for CIS AWS Foundations Benchmark v7.0.0.

The checks intentionally do not create, disable, delete, or update any IAM
resource. Missing permissions are reported as ERROR rather than PASS.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Any
from urllib.parse import unquote

import boto3
from botocore.exceptions import BotoCoreError, ClientError


ROOT_USER = "<root_account>"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finding(
    control_id: str,
    title: str,
    status: str,
    evidence: dict[str, Any],
    message: str,
    *,
    region: str = "global",
    resource_id: str = "account",
    remediation: str | None = None,
    severity: str = "MEDIUM",
) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "title": title,
        "service": "IAM",
        "region": region,
        "resource_id": resource_id,
        "status": status,
        "severity": severity,
        "evidence": evidence,
        "message": message,
        "remediation": remediation,
        "checked_at": _now(),
    }


def _error(control_id: str, title: str, error: Exception, **kwargs: Any) -> dict[str, Any]:
    return _finding(
        control_id,
        title,
        "ERROR",
        {"error_type": type(error).__name__, "error": str(error)},
        "The control could not be checked.",
        **kwargs,
    )


def _parse_time(value: str | None) -> datetime | None:
    if not value or value in {"N/A", "no_information", "not_supported"}:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _credential_report(iam: Any) -> list[dict[str, str]]:
    iam.generate_credential_report()
    for _ in range(15):
        try:
            response = iam.get_credential_report()
            content = response["Content"]
            return list(csv.DictReader(StringIO(content.decode("utf-8"))))
        except iam.exceptions.CredentialReportNotReadyException:
            time.sleep(1)
    raise RuntimeError("Credential report was not ready after 15 seconds")


def check_root_access_key(report: list[dict[str, str]]) -> dict[str, Any]:
    root = next(row for row in report if row.get("user") == ROOT_USER)
    active_keys = [
        key for key in ("access_key_1_active", "access_key_2_active") if root.get(key) == "true"
    ]
    return _finding(
        "2.4",
        "Root account has no access key",
        "FAIL" if active_keys else "PASS",
        {"active_root_access_keys": active_keys},
        "Root has active access keys." if active_keys else "Root has no active access keys.",
        remediation="Remove root access keys manually after review." if active_keys else None,
        severity="HIGH" if active_keys else "MEDIUM",
    )


def check_root_mfa(report: list[dict[str, str]]) -> dict[str, Any]:
    root = next(row for row in report if row.get("user") == ROOT_USER)
    enabled = root.get("mfa_active") == "true"
    return _finding(
        "2.5",
        "Root account has MFA enabled",
        "PASS" if enabled else "FAIL",
        {"mfa_active": root.get("mfa_active")},
        "Root MFA is enabled." if enabled else "Root MFA is not enabled.",
        remediation="Enable MFA for the root account manually." if not enabled else None,
        severity="HIGH" if not enabled else "MEDIUM",
    )


def check_root_activity(session: boto3.Session, regions: list[str], lookback_days: int) -> list[dict[str, Any]]:
    title = "Root is not used for daily or administrative work"
    start = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    findings: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    try:
        for region in regions:
            cloudtrail = session.client("cloudtrail", region_name=region)
            paginator = cloudtrail.get_paginator("lookup_events")
            for page in paginator.paginate(
                LookupAttributes=[{"AttributeKey": "Username", "AttributeValue": "root"}],
                StartTime=start,
            ):
                events.extend(page.get("Events", []))
    except (ClientError, BotoCoreError) as error:
        return [_error("2.7", title, error)]

    # CloudTrail can show activity, but it cannot decide whether a root event
    # was an approved break-glass action. Leave the final judgement to a person.
    findings.append(
        _finding(
            "2.7",
            title,
            "MANUAL",
            {
                "lookback_days": lookback_days,
                "root_event_count": len(events),
                "event_names": [event.get("EventName") for event in events[:20]],
            },
            "Review CloudTrail root activity and decide whether each event was approved.",
            remediation="Stop routine root use and document any approved break-glass use.",
        )
    )
    return findings


def check_password_policy(iam: Any) -> list[dict[str, Any]]:
    title_length = "IAM password policy requires at least 14 characters"
    title_reuse = "IAM password policy prevents password reuse"
    try:
        policy = iam.get_account_password_policy().get("PasswordPolicy", {})
    except iam.exceptions.NoSuchEntityException:
        evidence = {"password_policy": "not_found"}
        return [
            _finding("2.8", title_length, "FAIL", evidence, "No IAM password policy exists."),
            _finding("2.9", title_reuse, "FAIL", evidence, "No IAM password policy exists."),
        ]
    except (ClientError, BotoCoreError) as error:
        return [_error("2.8", title_length, error), _error("2.9", title_reuse, error)]

    minimum = policy.get("MinimumPasswordLength", 0)
    reuse = policy.get("PasswordReusePrevention", 0)
    return [
        _finding(
            "2.8",
            title_length,
            "PASS" if minimum >= 14 else "FAIL",
            {"minimum_password_length": minimum},
            f"Minimum password length is {minimum}.",
            remediation="Set the minimum password length to at least 14." if minimum < 14 else None,
        ),
        _finding(
            "2.9",
            title_reuse,
            "PASS" if reuse >= 24 else "FAIL",
            {"password_reuse_prevention": reuse},
            f"Password reuse prevention remembers {reuse} password(s).",
            remediation="Set password reuse prevention to at least 24." if reuse < 24 else None,
        ),
    ]


def check_console_user_mfa(report: list[dict[str, str]]) -> dict[str, Any]:
    console_users = [row for row in report if row.get("user") != ROOT_USER and row.get("password_enabled") == "true"]
    missing_mfa = [row.get("user") for row in console_users if row.get("mfa_active") != "true"]
    if not console_users:
        return _finding(
            "2.10",
            "IAM console users have MFA",
            "NOT_APPLICABLE",
            {"console_user_count": 0},
            "No IAM users with console passwords were found.",
        )
    return _finding(
        "2.10",
        "IAM console users have MFA",
        "FAIL" if missing_mfa else "PASS",
        {"console_user_count": len(console_users), "users_missing_mfa": missing_mfa},
        "Some console users do not have MFA." if missing_mfa else "All console users have MFA.",
        remediation="Enable MFA for every listed console user." if missing_mfa else None,
    )


def check_unused_credentials(report: list[dict[str, str]], age_days: int = 45) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=age_days)
    violations: list[dict[str, Any]] = []
    for row in report:
        if row.get("user") == ROOT_USER:
            continue
        user = row.get("user", "unknown")
        if row.get("password_enabled") == "true":
            last_used = _parse_time(row.get("password_last_used"))
            created = _parse_time(row.get("user_creation_time"))
            if (last_used and last_used < cutoff) or (last_used is None and created and created < cutoff):
                violations.append({"user": user, "credential": "console_password", "last_used": row.get("password_last_used")})
        for number in ("1", "2"):
            if row.get(f"access_key_{number}_active") != "true":
                continue
            last_used = _parse_time(row.get(f"access_key_{number}_last_used_date"))
            rotated = _parse_time(row.get(f"access_key_{number}_last_rotated"))
            if (last_used and last_used < cutoff) or (last_used is None and rotated and rotated < cutoff):
                violations.append({"user": user, "credential": f"access_key_{number}", "last_used": row.get(f"access_key_{number}_last_used_date")})
    return _finding(
        "2.11",
        "Unused credentials are disabled after 45 days",
        "FAIL" if violations else "PASS",
        {"age_days": age_days, "violations": violations},
        "Credentials older than the allowed unused period were found." if violations else "No stale active credentials were found.",
        remediation="Disable stale credentials after owner approval." if violations else None,
    )


def check_access_key_rotation(report: list[dict[str, str]], max_age_days: int = 90) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    violations: list[dict[str, Any]] = []
    active_key_count = 0
    for row in report:
        for number in ("1", "2"):
            if row.get(f"access_key_{number}_active") != "true":
                continue
            active_key_count += 1
            rotated = _parse_time(row.get(f"access_key_{number}_last_rotated"))
            if rotated is None or rotated < cutoff:
                violations.append({"user": row.get("user"), "access_key": number, "last_rotated": row.get(f"access_key_{number}_last_rotated")})
    if active_key_count == 0:
        return _finding("2.12", "Access keys rotate within 90 days", "NOT_APPLICABLE", {"active_key_count": 0}, "No active IAM access keys were found.")
    return _finding(
        "2.12",
        "Access keys rotate within 90 days",
        "FAIL" if violations else "PASS",
        {"max_age_days": max_age_days, "violations": violations},
        "Some active access keys are older than 90 days." if violations else "All active access keys are within the rotation period.",
        remediation="Rotate stale access keys after owner approval." if violations else None,
    )


def _list_all(iam: Any, operation: str, result_key: str, **kwargs: Any) -> list[dict[str, Any]]:
    paginator = iam.get_paginator(operation)
    items: list[dict[str, Any]] = []
    for page in paginator.paginate(**kwargs):
        items.extend(page.get(result_key, []))
    return items


def check_user_group_permissions(iam: Any) -> dict[str, Any]:
    title = "IAM users receive permissions through groups"
    try:
        users = _list_all(iam, "list_users", "Users")
        violations = []
        for user in users:
            username = user["UserName"]
            groups = _list_all(iam, "get_groups_for_user", "Groups", UserName=username)
            direct_inline = _list_all(iam, "list_user_policies", "PolicyNames", UserName=username)
            direct_attached = _list_all(iam, "list_attached_user_policies", "AttachedPolicies", UserName=username)
            if direct_inline or direct_attached:
                violations.append({"user": username, "groups": [group["GroupName"] for group in groups], "direct_inline": direct_inline, "direct_attached": [policy["PolicyName"] for policy in direct_attached]})
    except (ClientError, BotoCoreError) as error:
        return _error("2.13", title, error)
    if not users:
        return _finding("2.13", title, "NOT_APPLICABLE", {"user_count": 0}, "No IAM users were found.")
    return _finding(
        "2.13",
        title,
        "FAIL" if violations else "PASS",
        {"user_count": len(users), "violations": violations},
        "Some IAM users have direct policies." if violations else "No direct IAM user policies were found.",
        remediation="Move permissions to groups after reviewing the effective access." if violations else None,
    )


def _document_has_full_admin(document: dict[str, Any]) -> bool:
    statements = document.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue
        actions = statement.get("Action", [])
        resources = statement.get("Resource", [])
        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]
        if any(action in {"*", "*:*"} for action in actions) and "*" in resources:
            return True
    return False


def _decode_policy_document(document: Any) -> dict[str, Any]:
    if isinstance(document, dict):
        return document
    return json.loads(unquote(document))


def check_unrestricted_policies(iam: Any) -> dict[str, Any]:
    title = "No IAM policy grants unrestricted *:* access"
    violations: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        policies = _list_all(iam, "list_policies", "Policies", Scope="All", OnlyAttached=True)
        for policy in policies:
            try:
                version = iam.get_policy_version(PolicyArn=policy["Arn"], VersionId=policy["DefaultVersionId"])
                if _document_has_full_admin(_decode_policy_document(version["PolicyVersion"]["Document"])):
                    violations.append({"policy_arn": policy["Arn"], "policy_name": policy["PolicyName"], "type": "managed"})
            except (ClientError, BotoCoreError) as error:
                errors.append(f"{policy['Arn']}: {error}")

        for identity_type, list_operation, result_key, policy_operation, name_key in [
            ("user", "list_users", "Users", "list_user_policies", "UserName"),
            ("group", "list_groups", "Groups", "list_group_policies", "GroupName"),
            ("role", "list_roles", "Roles", "list_role_policies", "RoleName"),
        ]:
            identities = _list_all(iam, list_operation, result_key)
            for identity in identities:
                identity_name = identity[name_key]
                policy_names = _list_all(iam, policy_operation, "PolicyNames", **{name_key: identity_name})
                get_operation = {
                    "user": "get_user_policy",
                    "group": "get_group_policy",
                    "role": "get_role_policy",
                }[identity_type]
                for policy_name in policy_names:
                    try:
                        response = getattr(iam, get_operation)(**{name_key: identity_name, "PolicyName": policy_name})
                        document = _decode_policy_document(response["PolicyDocument"])
                        if _document_has_full_admin(document):
                            violations.append({
                                "identity_type": identity_type,
                                "identity": identity_name,
                                "policy_name": policy_name,
                                "type": "inline",
                            })
                    except (ClientError, BotoCoreError) as error:
                        errors.append(f"{identity_type}/{identity_name}/{policy_name}: {error}")
    except (ClientError, BotoCoreError) as error:
        return _error("2.14", title, error)

    evidence = {"managed_policy_violations": violations, "policy_read_errors": errors}
    if errors:
        return _finding("2.14", title, "ERROR", evidence, "Some attached policies could not be read; compliance cannot be confirmed.")
    return _finding(
        "2.14",
        title,
        "FAIL" if violations else "PASS",
        evidence,
        "At least one attached policy grants unrestricted access." if violations else "No unrestricted attached managed policy was found.",
        remediation="Replace or narrow the unrestricted policy after reviewing effective permissions." if violations else None,
    )


def check_access_analyzer(session: boto3.Session) -> list[dict[str, Any]]:
    title = "IAM External Access Analyzer is active in every enabled Region"
    findings: list[dict[str, Any]] = []
    try:
        ec2 = session.client("ec2", region_name=session.region_name or "us-east-1")
        regions = [item["RegionName"] for item in ec2.describe_regions().get("Regions", [])]
    except (ClientError, BotoCoreError) as error:
        return [_error("2.18", title, error)]

    for region in regions:
        try:
            analyzers = session.client("accessanalyzer", region_name=region).list_analyzers().get("analyzers", [])
            active = [analyzer["name"] for analyzer in analyzers if analyzer.get("status") == "ACTIVE"]
            findings.append(
                _finding(
                    "2.18",
                    title,
                    "PASS" if active else "FAIL",
                    {"analyzers": active},
                    "An active Access Analyzer exists." if active else "No active Access Analyzer exists in this Region.",
                    region=region,
                    remediation="Create and activate an account Access Analyzer after approval." if not active else None,
                )
            )
        except (ClientError, BotoCoreError) as error:
            findings.append(_error("2.18", title, error, region=region))
    return findings


def audit_iam(session: boto3.Session, regions: list[str], root_activity_days: int = 90) -> list[dict[str, Any]]:
    iam = session.client("iam")
    findings: list[dict[str, Any]] = []
    try:
        report = _credential_report(iam)
        findings.extend([check_root_access_key(report), check_root_mfa(report)])
        findings.append(check_console_user_mfa(report))
        findings.append(check_unused_credentials(report))
        findings.append(check_access_key_rotation(report))
    except (ClientError, BotoCoreError, RuntimeError) as error:
        for control_id, title in [
            ("2.4", "Root account has no access key"),
            ("2.5", "Root account has MFA enabled"),
            ("2.10", "IAM console users have MFA"),
            ("2.11", "Unused credentials are disabled after 45 days"),
            ("2.12", "Access keys rotate within 90 days"),
        ]:
            findings.append(_error(control_id, title, error))

    findings.extend(check_password_policy(iam))
    findings.extend(check_root_activity(session, regions, root_activity_days))
    findings.append(check_user_group_permissions(iam))
    findings.append(check_unrestricted_policies(iam))
    findings.extend(check_access_analyzer(session))
    return findings
