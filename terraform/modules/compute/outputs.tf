output "bastion_instance_id" {
  value       = aws_instance.bastion.id
  description = "Bastion instance ID"
}

output "bastion_public_ip" {
  value       = aws_instance.bastion.public_ip
  description = "Bastion public IP"
}

output "app_instance_ids" {
  value       = { for name, instance in aws_instance.app : name => instance.id }
  description = "Application instance IDs keyed by AZ label"
}
