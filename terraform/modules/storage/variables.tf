variable "project_name" {
  description = "Name prefix for storage resources"
  type        = string
}

variable "force_destroy" {
  description = "Allow Terraform to delete objects when destroying the lab bucket"
  type        = bool
  default     = true
}
