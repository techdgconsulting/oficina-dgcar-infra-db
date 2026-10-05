locals {
  name = "${var.project_name}-${var.environment}"
}

resource "aws_db_parameter_group" "postgres" {
  name        = "${local.name}-postgres-params"
  family      = var.db_parameter_group_family
  description = "Managed PostgreSQL parameters for DGCar ${var.environment}"

  parameter {
    name  = "log_min_duration_statement"
    value = var.log_min_duration_statement_ms
  }

  tags = {
    Name = "${local.name}-postgres-params"
  }
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds-sg"
  description = "Allow PostgreSQL access only from authorized workloads"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from authorized security groups"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name}-rds-sg"
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${local.name}-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier = "${local.name}-postgres"

  engine                     = "postgres"
  engine_version             = var.db_engine_version
  instance_class             = var.db_instance_class
  allocated_storage          = var.db_allocated_storage
  max_allocated_storage      = var.db_max_allocated_storage
  storage_type               = var.db_storage_type
  storage_encrypted          = true
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = var.db_password
  port                       = 5432
  publicly_accessible        = false
  multi_az                   = var.db_multi_az
  backup_retention_period    = var.backup_retention_period
  backup_window              = var.backup_window
  maintenance_window         = var.maintenance_window
  deletion_protection        = var.deletion_protection
  skip_final_snapshot        = var.skip_final_snapshot
  final_snapshot_identifier  = var.skip_final_snapshot ? null : "${local.name}-postgres-final"
  db_subnet_group_name       = aws_db_subnet_group.main.name
  vpc_security_group_ids     = [aws_security_group.rds.id]
  parameter_group_name       = aws_db_parameter_group.postgres.name
  apply_immediately          = true
  auto_minor_version_upgrade = true

  tags = {
    Name = "${local.name}-postgres"
  }
}
