variable "project_name" {
  type        = string
  description = "Name prefix for networking resources"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}

variable "subnet_cidrs" {
  type        = map(string)
  description = "CIDR blocks keyed by public_az1, public_az2, app_az1, app_az2, db_az1, db_az2"

  validation {
    condition = alltrue([
      for name in ["public_az1", "public_az2", "app_az1", "app_az2", "db_az1", "db_az2"] :
      contains(keys(var.subnet_cidrs), name)
    ])
    error_message = "subnet_cidrs must contain all six required subnet keys."
  }
}

variable "az_names" {
  type        = list(string)
  description = "Optional two AZ names; empty selects two available AZs dynamically"
  default     = []

  validation {
    condition     = length(var.az_names) == 0 || length(var.az_names) == 2
    error_message = "az_names must be empty or contain exactly two AZ names."
  }
}
