variable "aws_region" {
  description = "AWS region where the database infrastructure will be created."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as a prefix for AWS resources."
  type        = string
  default     = "oficina-dgcar"
}

variable "environment" {
  description = "Environment name for tagging and naming."
  type        = string
  default     = "academic"
}

variable "vpc_id" {
  description = "VPC ID produced by oficina-dgcar-infra-k8s."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs produced by oficina-dgcar-infra-k8s."
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs allowed to connect to PostgreSQL."
  type        = list(string)
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "oficina"
}

variable "db_username" {
  description = "PostgreSQL master username."
  type        = string
  default     = "oficina"
}

variable "db_password" {
  description = "PostgreSQL master password. Use terraform.tfvars locally or CI secrets; do not commit real values."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class for the academic environment."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Initial RDS storage in GiB."
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum RDS autoscaled storage in GiB."
  type        = number
  default     = 30
}
