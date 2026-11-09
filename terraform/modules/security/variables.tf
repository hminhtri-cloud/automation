variable "project_name" {
  type        = string
  description = "Name prefix for Security Groups"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "admin_cidr" {
  type        = string
  description = "Trusted administrator IPv4 CIDR for bastion SSH"

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0))
    error_message = "admin_cidr must be a valid IPv4 CIDR block."
  }
}
