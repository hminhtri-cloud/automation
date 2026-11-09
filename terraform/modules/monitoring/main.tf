data "aws_caller_identity" "current" {}

# Preserve the existing operational log group without managing the
# restricted CloudTrail-to-CloudWatch Logs IAM integration.
resource "aws_cloudwatch_log_group" "security" {
  name              = "/cis/${var.project_name}/security"
  retention_in_days = 7
}

resource "aws_s3_bucket" "cloudtrail" {
  count               = var.enable_cloudtrail ? 1 : 0
  bucket_prefix       = "${var.project_name}-cloudtrail-"
  force_destroy       = true
  object_lock_enabled = false

  tags = { Name = "${var.project_name}-cloudtrail-logs" }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.cloudtrail_kms_key_id == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.cloudtrail_kms_key_id
    }
  }
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  count  = var.enable_cloudtrail ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AWSCloudTrailAclCheck"
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "s3:GetBucketAcl"
        Resource  = aws_s3_bucket.cloudtrail[0].arn
        Condition = { StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id } }
      },
      {
        Sid       = "AWSCloudTrailWrite"
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.cloudtrail[0].arn}/cloudtrail/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"      = "bucket-owner-full-control"
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_cloudtrail" "this" {
  count                         = var.enable_cloudtrail ? 1 : 0
  name                          = "${var.project_name}-multi-region-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail[0].id
  s3_key_prefix                 = "cloudtrail"
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = var.cloudtrail_kms_key_id

  depends_on = [aws_s3_bucket_policy.cloudtrail]

  tags = { Name = "${var.project_name}-multi-region-trail" }
}

resource "aws_s3_bucket" "flow_logs" {
  count               = var.enable_vpc_flow_logs ? 1 : 0
  bucket_prefix       = "${var.project_name}-vpc-flow-"
  force_destroy       = true
  object_lock_enabled = false

  tags = { Name = "${var.project_name}-vpc-flow-logs" }
}

resource "aws_s3_bucket_public_access_block" "flow_logs" {
  count  = var.enable_vpc_flow_logs ? 1 : 0
  bucket = aws_s3_bucket.flow_logs[0].id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "flow_logs" {
  count  = var.enable_vpc_flow_logs ? 1 : 0
  bucket = aws_s3_bucket.flow_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "flow_logs" {
  count  = var.enable_vpc_flow_logs ? 1 : 0
  bucket = aws_s3_bucket.flow_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "VpcFlowLogsBucketAcl"
        Effect    = "Allow"
        Principal = { Service = "delivery.logs.amazonaws.com" }
        Action    = "s3:GetBucketAcl"
        Resource  = aws_s3_bucket.flow_logs[0].arn
        Condition = { StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id } }
      },
      {
        Sid       = "VpcFlowLogsWrite"
        Effect    = "Allow"
        Principal = { Service = "delivery.logs.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.flow_logs[0].arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"      = "bucket-owner-full-control"
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_flow_log" "this" {
  count                = var.enable_vpc_flow_logs ? 1 : 0
  vpc_id               = var.vpc_id
  traffic_type         = "ALL"
  log_destination_type = "s3"
  log_destination      = aws_s3_bucket.flow_logs[0].arn

  depends_on = [aws_s3_bucket_policy.flow_logs]

  tags = { Name = "${var.project_name}-vpc-flow-log" }
}

resource "aws_securityhub_account" "this" {
  count = var.enable_security_hub ? 1 : 0
}

resource "aws_cloudwatch_dashboard" "this" {
  count          = var.enable_operational_monitoring ? 1 : 0
  dashboard_name = "${var.project_name}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title  = "Application CPU"
          region = data.aws_region.current.name
          stat   = "Average"
          period = 300
          metrics = [
            for name, id in var.app_instance_ids : ["AWS/EC2", "CPUUtilization", "InstanceId", id, { label = name }]
          ]
        }
      },
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title   = "ALB Unhealthy Hosts"
          region  = data.aws_region.current.name
          stat    = "Maximum"
          period  = 60
          metrics = [["AWS/ApplicationELB", "UnHealthyHostCount", "LoadBalancer", var.alb_arn_suffix, "TargetGroup", var.target_group_arn_suffix]]
        }
      }
    ]
  })
}

data "aws_region" "current" {}

resource "aws_cloudwatch_metric_alarm" "app_cpu" {
  for_each = var.enable_operational_monitoring ? var.app_instance_ids : {}

  alarm_name          = each.key == "az1" ? "${var.project_name}-ec2-cpu" : "${var.project_name}-${each.key}-ec2-cpu"
  alarm_description   = "EC2 CPU utilization is high"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  dimensions          = { InstanceId = each.value }
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy" {
  count = var.enable_operational_monitoring ? 1 : 0

  alarm_name        = "${var.project_name}-alb-unhealthy-targets"
  alarm_description = "ALB has unhealthy targets"
  namespace         = "AWS/ApplicationELB"
  metric_name       = "UnHealthyHostCount"
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 0
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  count = var.enable_operational_monitoring ? 1 : 0

  alarm_name          = "${var.project_name}-db-high-cpu"
  alarm_description   = "RDS CPU is high"
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  dimensions          = { DBInstanceIdentifier = var.db_identifier }
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"
}
