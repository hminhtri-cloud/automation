variable "aws_region" {
  type        = string
  description = "AWS Region for the new deployment"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Name prefix for all resources"
  default     = "cis-security"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR for the new deployment VPC"
  default     = "10.0.0.0/16"
}

variable "subnet_cidrs" {
  type        = map(string)
  description = "Six subnet CIDRs keyed by tier and AZ"
  default = {
    public_az1 = "10.0.1.0/24"
    public_az2 = "10.0.2.0/24"
    app_az1    = "10.0.11.0/24"
    app_az2    = "10.0.12.0/24"
    db_az1     = "10.0.21.0/24"
    db_az2     = "10.0.22.0/24"
  }
}

variable "az_names" {
  type        = list(string)
  description = "Optional two AZ names; empty selects available AZs dynamically"
  default     = []
}

variable "admin_cidr" {
  type        = string
  description = "Administrator public IPv4 CIDR, normally x.x.x.x/32"
}

variable "key_name" {
  type        = string
  description = "Existing EC2 key pair name for the bastion"
}

variable "instance_type" {
  type        = string
  description = "EC2 class supported by Learner Lab"
  default     = "t3.micro"
}

variable "architecture" {
  type        = string
  description = "Ubuntu AMI architecture name"
  default     = "amd64"

  validation {
    condition     = contains(["amd64", "arm64"], var.architecture)
    error_message = "architecture must be amd64 or arm64."
  }
}

variable "db_instance_class" {
  type        = string
  description = "RDS class supported by Learner Lab"
  default     = "db.t3.micro"
}

variable "db_engine_version" {
  type        = string
  description = "Optional AWS-supported MySQL version"
  default     = null
  nullable    = true
}

variable "db_parameter_group_family" {
  type        = string
  description = "RDS parameter group family matching the MySQL engine"
  default     = "mysql8.4"
}

variable "enable_multi_az" {
  type        = bool
  description = "Enable the full RDS Multi-AZ architecture"
  default     = true
}

variable "deletion_protection" {
  type        = bool
  description = "Whether RDS deletion protection is enabled"
  default     = false
}

variable "rds_kms_key_id" {
  type        = string
  description = "Optional KMS key ID/ARN; null uses AWS-managed RDS encryption key"
  default     = null
  nullable    = true
}

variable "cloudtrail_kms_key_id" {
  type        = string
  description = "Optional KMS key ID or ARN for CloudTrail log encryption"
  default     = null
  nullable    = true
}

variable "enable_cloudtrail" {
  type        = bool
  description = "Create a multi-Region CloudTrail trail writing to S3"
  default     = true
}

variable "enable_vpc_flow_logs" {
  type        = bool
  description = "Create VPC Flow Logs writing to S3"
  default     = true
}

variable "manage_security_hub" {
  type        = bool
  description = "Manage Security Hub with Terraform; false avoids conflict with an already-enabled manual account"
  default     = false
}

variable "enable_operational_monitoring" {
  type        = bool
  description = "Create CloudWatch dashboard and operational alarms"
  default     = true
}
