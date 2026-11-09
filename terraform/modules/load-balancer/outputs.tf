output "dns_name" {
  value       = aws_lb.this.dns_name
  description = "ALB DNS name"
}

output "load_balancer_arn" {
  value       = aws_lb.this.arn
  description = "ALB ARN"
}

output "load_balancer_full_name" {
  value       = aws_lb.this.arn_suffix
  description = "ALB CloudWatch dimension value"
}

output "target_group_arn" {
  value       = aws_lb_target_group.app.arn
  description = "Target Group ARN"
}

output "target_group_full_name" {
  value       = aws_lb_target_group.app.arn_suffix
  description = "Target Group CloudWatch dimension value"
}
