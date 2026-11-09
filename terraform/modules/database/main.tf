resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = values(var.db_subnet_ids)

  tags = { Name = "${var.project_name}-db-subnet-group" }
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-mysql84-params"
  family = var.parameter_group_family

  parameter {
    name         = "require_secure_transport"
    value        = "ON"
    apply_method = "pending-reboot"
  }

  tags = { Name = "${var.project_name}-mysql84-params" }
}

resource "aws_db_instance" "this" {
  identifier                  = "${var.project_name}-mysql-db"
  engine                      = "mysql"
  engine_version              = var.engine_version
  instance_class              = var.db_instance_class
  allocated_storage           = 20
  max_allocated_storage       = 50
  storage_type                = "gp3"
  storage_encrypted           = true
  kms_key_id                  = var.rds_kms_key_id
  db_name                     = var.db_name
  username                    = var.db_username
  manage_master_user_password = true
  port                        = 3306
  publicly_accessible         = false
  multi_az                    = var.enable_multi_az
  db_subnet_group_name        = aws_db_subnet_group.this.name
  parameter_group_name        = aws_db_parameter_group.this.name
  vpc_security_group_ids      = [var.db_security_group_id]
  auto_minor_version_upgrade  = true
  backup_retention_period     = var.backup_retention_period
  deletion_protection         = var.deletion_protection
  apply_immediately           = true
  skip_final_snapshot         = true
  copy_tags_to_snapshot       = true

  tags = { Name = "${var.project_name}-mysql-db" }
}
