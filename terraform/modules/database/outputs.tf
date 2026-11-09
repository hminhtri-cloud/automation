output "db_instance_id" {
  description = "RDS DB instance ID"
  value       = aws_db_instance.this.id
}

output "db_endpoint" {
  description = "RDS endpoint without credentials"
  value       = aws_db_instance.this.address
}

output "db_port" {
  description = "RDS port"
  value       = aws_db_instance.this.port
}

output "master_user_secret_arn" {
  description = "Secrets Manager ARN managed by RDS for the master user"
  value       = try(aws_db_instance.this.master_user_secret[0].secret_arn, null)
}
