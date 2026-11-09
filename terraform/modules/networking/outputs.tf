output "vpc_id" {
  value       = aws_vpc.this.id
  description = "VPC ID"
}

output "subnet_ids" {
  value       = { for name, subnet in aws_subnet.this : name => subnet.id }
  description = "Subnet IDs keyed by logical name"
}

output "availability_zones" {
  value       = local.azs
  description = "AZs selected for the deployment"
}

output "nat_gateway_id" {
  value       = aws_nat_gateway.this.id
  description = "Single NAT Gateway ID"
}
