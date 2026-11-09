output "vpc_id" {
  value       = module.networking.vpc_id
  description = "New deployment VPC ID"
}

output "availability_zones" {
  value       = module.networking.availability_zones
  description = "AZs selected dynamically for this account"
}

output "subnet_ids" {
  value       = module.networking.subnet_ids
  description = "Six subnet IDs keyed by logical name"
}

output "bastion_public_ip" {
  value       = module.compute.bastion_public_ip
  description = "Bastion public IP"
}

output "app_instance_ids" {
  value       = module.compute.app_instance_ids
  description = "Private app EC2 IDs"
}

output "alb_dns_name" {
  value       = module.load_balancer.dns_name
  description = "Application Load Balancer DNS name"
}

output "rds_endpoint" {
  value       = module.database.db_endpoint
  description = "RDS endpoint without credentials"
}

output "rds_master_user_secret_arn" {
  value       = module.database.master_user_secret_arn
  description = "RDS-managed master user secret ARN"
}

output "security_log_bucket" {
  value       = module.storage.bucket_name
  description = "Versioned private bucket for security logs"
}

output "cloudtrail_arn" {
  value       = module.monitoring.cloudtrail_arn
  description = "Multi-Region CloudTrail ARN"
}

output "flow_logs_bucket_name" {
  value       = module.monitoring.flow_logs_bucket_name
  description = "VPC Flow Logs S3 bucket name"
}

output "cloudwatch_logs_integration" {
  value       = module.monitoring.cloudwatch_logs_integration
  description = "Learner Lab CloudTrail-to-CloudWatch Logs limitation"
}
