# CIS Security Baseline Terraform

This directory describes a **new, reproducible deployment** of the lab architecture. It does not represent the existing manually-created resources unless those resources are separately imported, which this project intentionally does not do.

## Modules

- `modules/networking`: VPC `10.20.0.0/16`, six subnets, IGW, one NAT Gateway, and four route tables.
- `modules/security`: bastion, ALB, private app, and database Security Groups. No IAM roles are created.
- `modules/compute`: one Ubuntu bastion and two Ubuntu Nginx app instances. AMIs are discovered from Canonical-owned images; IDs are not hardcoded.
- `modules/load-balancer`: internet-facing ALB, HTTP listener, target group, and two targets.
- `modules/database`: private MySQL RDS Single-AZ by default, encrypted storage, TLS enforcement parameter, and RDS-managed master password.
- `modules/monitoring`: versioned S3 log bucket integration, multi-Region CloudTrail, VPC Flow Logs to S3, three CloudWatch alarms, and a dashboard.

## Important Lab Notes

- One NAT Gateway is used to reduce cost. It is a single point of failure and is not a highly available production design.
- `enable_multi_az` defaults to `false` to reduce cost. Set it to `true` only when the lab supports it and the cost is acceptable.
- RDS uses `manage_master_user_password = true`; no database password is hardcoded or exported. The secret is managed by RDS in Secrets Manager. Terraform state still contains sensitive infrastructure metadata and must be protected.
- `admin_cidr` must be a narrow administrator CIDR, normally your current public IP with `/32`.
- The configuration does not create IAM users, policies, or roles. CloudTrail and VPC Flow Logs are configured without an application-created IAM role.
- CloudFormation/Terraform resource configuration is not the same as CIS Benchmark compliance. Boto3 must audit the resulting AWS account and Region configuration separately.
- This code is a new deployment using `10.20.0.0/16`; it is not an import or state reconstruction of the manually-created deployment.

## Safe Workflow

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and set `admin_cidr` and an existing `key_name`.
2. Run `terraform fmt -recursive`.
3. Run `terraform init`.
4. Run `terraform validate`.
5. Review `terraform plan` carefully. NAT Gateway, EC2, ALB, and RDS can incur charges.
6. Apply only after review and explicit approval.

This repository does not run `terraform apply`, `terraform destroy`, or `terraform import` automatically.
