output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint."
  value       = aws_db_instance.postgres.address
}

output "rds_port" {
  description = "RDS PostgreSQL port."
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "PostgreSQL database name."
  value       = var.db_name
}

output "rds_security_group_id" {
  description = "Security group ID attached to RDS."
  value       = aws_security_group.rds.id
}

output "spring_datasource_url" {
  description = "JDBC URL to use in Kubernetes ConfigMap."
  value       = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"
}
