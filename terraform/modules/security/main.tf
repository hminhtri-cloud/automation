resource "aws_security_group" "bastion" {
  name        = "${var.project_name}-bastion-sg"
  description = "SSH from the configured administrator CIDR"
  vpc_id      = var.vpc_id

  ingress {
    description = "Administrator SSH"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    description = "Outbound traffic"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-bastion-sg" }
}

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Public HTTP access to the ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP demo listener"
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound traffic"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-alb-sg" }
}

resource "aws_security_group" "app" {
  name        = "${var.project_name}-private-app-sg"
  description = "Private application traffic from bastion and ALB"
  vpc_id      = var.vpc_id

  egress {
    description = "Outbound traffic through the NAT Gateway"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-private-app-sg" }
}

resource "aws_security_group" "db" {
  name        = "${var.project_name}-db-sg"
  description = "MySQL access from private application instances"
  vpc_id      = var.vpc_id

  egress {
    description = "Outbound traffic"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-db-sg" }
}

resource "aws_security_group_rule" "app_from_bastion" {
  type                     = "ingress"
  security_group_id        = aws_security_group.app.id
  source_security_group_id = aws_security_group.bastion.id
  protocol                 = "tcp"
  from_port                = 22
  to_port                  = 22
  description              = "SSH from bastion"
}

resource "aws_security_group_rule" "app_from_alb" {
  type                     = "ingress"
  security_group_id        = aws_security_group.app.id
  source_security_group_id = aws_security_group.alb.id
  protocol                 = "tcp"
  from_port                = 80
  to_port                  = 80
  description              = "HTTP from ALB"
}

resource "aws_security_group_rule" "db_from_app" {
  type                     = "ingress"
  security_group_id        = aws_security_group.db.id
  source_security_group_id = aws_security_group.app.id
  protocol                 = "tcp"
  from_port                = 3306
  to_port                  = 3306
  description              = "MySQL from private app"
}
