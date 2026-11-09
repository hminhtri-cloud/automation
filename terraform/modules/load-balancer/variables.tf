variable "project_name" {
  type        = string
  description = "Name prefix for load balancer resources"
}

variable "vpc_id" {
  type        = string
  description = "VPC containing the ALB"
}

variable "public_subnet_ids" {
  type        = map(string)
  description = "Two public subnet IDs keyed by AZ label"
}

variable "alb_security_group_id" {
  type        = string
  description = "ALB Security Group ID"
}

variable "app_instance_ids" {
  type        = map(string)
  description = "App instance IDs keyed by AZ label"
}
