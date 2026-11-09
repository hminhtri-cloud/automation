module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  vpc_cidr     = var.vpc_cidr
  subnet_cidrs = var.subnet_cidrs
  az_names     = var.az_names
}

module "security" {
  source = "./modules/security"

  project_name = var.project_name
  vpc_id       = module.networking.vpc_id
  admin_cidr   = var.admin_cidr
}

module "compute" {
  source = "./modules/compute"

  project_name              = var.project_name
  bastion_subnet_id         = module.networking.subnet_ids["public_az1"]
  bastion_security_group_id = module.security.security_group_ids.bastion
  app_security_group_id     = module.security.security_group_ids.app
  app_subnet_ids = {
    az1 = module.networking.subnet_ids["app_az1"]
    az2 = module.networking.subnet_ids["app_az2"]
  }
  instance_type = var.instance_type
  key_name      = var.key_name
  architecture  = var.architecture
}

module "load_balancer" {
  source = "./modules/load-balancer"

  project_name          = var.project_name
  vpc_id                = module.networking.vpc_id
  alb_security_group_id = module.security.security_group_ids.alb
  public_subnet_ids = {
    az1 = module.networking.subnet_ids["public_az1"]
    az2 = module.networking.subnet_ids["public_az2"]
  }
  app_instance_ids = module.compute.app_instance_ids
}

module "database" {
  source = "./modules/database"

  project_name         = var.project_name
  db_security_group_id = module.security.security_group_ids.db
  db_subnet_ids = {
    az1 = module.networking.subnet_ids["db_az1"]
    az2 = module.networking.subnet_ids["db_az2"]
  }
  db_instance_class      = var.db_instance_class
  engine_version         = var.db_engine_version
  parameter_group_family = var.db_parameter_group_family
  enable_multi_az        = var.enable_multi_az
  deletion_protection    = var.deletion_protection
  rds_kms_key_id         = var.rds_kms_key_id
}

module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
}

module "monitoring" {
  source = "./modules/monitoring"

  project_name                  = var.project_name
  vpc_id                        = module.networking.vpc_id
  app_instance_ids              = module.compute.app_instance_ids
  alb_arn_suffix                = module.load_balancer.load_balancer_full_name
  target_group_arn_suffix       = module.load_balancer.target_group_full_name
  db_identifier                 = module.database.db_instance_id
  cloudtrail_kms_key_id         = var.cloudtrail_kms_key_id
  enable_cloudtrail             = var.enable_cloudtrail
  enable_vpc_flow_logs          = var.enable_vpc_flow_logs
  enable_security_hub           = var.manage_security_hub
  enable_operational_monitoring = var.enable_operational_monitoring
}

moved {
  from = module.monitoring.aws_cloudwatch_metric_alarm.ec2_cpu
  to   = module.monitoring.aws_cloudwatch_metric_alarm.app_cpu["az1"]
}

moved {
  from = module.monitoring.aws_cloudwatch_metric_alarm.alb_unhealthy_targets
  to   = module.monitoring.aws_cloudwatch_metric_alarm.alb_unhealthy[0]
}
