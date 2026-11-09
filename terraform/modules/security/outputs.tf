output "security_group_ids" {
  value = {
    bastion = aws_security_group.bastion.id
    alb     = aws_security_group.alb.id
    app     = aws_security_group.app.id
    db      = aws_security_group.db.id
  }
  description = "Security Group IDs keyed by role"
}
