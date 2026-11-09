output "cloudtrail_bucket_name" {
  description = "CloudTrail S3 bucket name"
  value       = try(aws_s3_bucket.cloudtrail[0].bucket, null)
}

output "flow_logs_bucket_name" {
  description = "VPC Flow Logs S3 bucket name"
  value       = try(aws_s3_bucket.flow_logs[0].bucket, null)
}

output "cloudtrail_arn" {
  description = "Multi-Region CloudTrail ARN"
  value       = try(aws_cloudtrail.this[0].arn, null)
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = try(aws_cloudwatch_dashboard.this[0].dashboard_name, null)
}

output "security_hub_enabled" {
  description = "Whether the Security Hub account resource is enabled in this configuration"
  value       = var.enable_security_hub
}

output "cloudwatch_logs_integration" {
  description = "The intentionally unsupported CloudTrail to CloudWatch Logs integration"
  value       = "Not managed: Learner Lab may deny iam:CreateRole; CloudTrail is retained in S3 for Python parsing."
}
