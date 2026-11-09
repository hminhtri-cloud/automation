variable "project_name" {
  description = "Name prefix for database resources"
  type        = string
}

variable "db_subnet_ids" {
  description = "Two private database subnet IDs"
  type        = map(string)
}

variable "db_security_group_id" {
  description = "Database Security Group ID"
  type        = string
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "cisapp"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "cisadmin"
}

variable "db_instance_class" {
  description = "RDS instance class supported by the lab"
  type        = string
}

variable "engine_version" {
  description = "Optional AWS-supported MySQL engine version; null uses the current default"
  type        = string
  default     = null
  nullable    = true
}

variable "parameter_group_family" {
  description = "RDS parameter group family matching the selected MySQL engine"
  type        = string
  default     = "mysql8.4"
}

variable "enable_multi_az" {
  description = "Enable RDS Multi-AZ; costs more and is disabled for the default lab"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Protect the RDS instance from deletion"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 1
}

variable "rds_kms_key_id" {
  description = "Optional KMS key ID or ARN for RDS storage encryption"
  type        = string
  default     = null
  nullable    = true
}
