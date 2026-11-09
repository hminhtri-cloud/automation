variable "project_name" {
  type        = string
  description = "Name prefix for compute resources"
}

variable "bastion_subnet_id" {
  type        = string
  description = "Public subnet for the bastion"
}

variable "app_subnet_ids" {
  type        = map(string)
  description = "Private application subnet IDs keyed by az1 and az2"
}

variable "bastion_security_group_id" {
  type        = string
  description = "Bastion Security Group ID"
}

variable "app_security_group_id" {
  type        = string
  description = "Private app Security Group ID"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type supported by the lab"
}

variable "key_name" {
  type        = string
  description = "Existing EC2 key pair name for the bastion"
}

variable "architecture" {
  type        = string
  description = "Ubuntu AMI name architecture: amd64 or arm64"
  default     = "amd64"

  validation {
    condition     = contains(["amd64", "arm64"], var.architecture)
    error_message = "architecture must be amd64 or arm64."
  }
}
