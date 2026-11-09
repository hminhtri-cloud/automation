variable "project_name" {
  description = "Name prefix for monitoring resources"
  type        = string
}

variable "vpc_id" {
  description = "VPC to monitor with VPC Flow Logs"
  type        = string
}

variable "app_instance_ids" {
  description = "Application instance IDs for operational alarms"
  type        = map(string)
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix used by CloudWatch dimensions"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix used by CloudWatch dimensions"
  type        = string
}

variable "db_identifier" {
  description = "RDS DB instance identifier used by CloudWatch dimensions"
  type        = string
}

variable "cloudtrail_kms_key_id" {
  description = "Optional KMS key for CloudTrail log encryption"
  type        = string
  default     = null
  nullable    = true
}

variable "enable_cloudtrail" {
  description = "Create a multi-Region CloudTrail trail writing to S3"
  type        = bool
  default     = true
}

variable "enable_vpc_flow_logs" {
  description = "Create VPC Flow Logs writing to S3"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable the Security Hub account integration"
  type        = bool
  default     = true
}

variable "enable_operational_monitoring" {
  description = "Create CloudWatch dashboard and operational alarms"
  type        = bool
  default     = true
}
