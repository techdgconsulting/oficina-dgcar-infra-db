# oficina-dgcar-infra-db

Repositório da infraestrutura de banco de dados gerenciado da Oficina Mecânica DGCar no Tech Challenge 3.

## Propósito

- Provisionar Amazon RDS PostgreSQL.
- Configurar subnet group.
- Configurar security groups do banco.
- Configurar parâmetros, backup, sizing e segurança.
- Expor outputs necessários para aplicação, Lambda e infraestrutura Kubernetes.

## Tecnologia Alvo

- Terraform
- Amazon RDS PostgreSQL
- AWS VPC/Subnets/Security Groups
- GitHub Actions

## Branches E Ambientes

- `main`: produção, protegida e sem commits diretos.
- `homolog`: homologação, com deploy automático quando configurado.
- GitHub Environments esperados: `homolog` e `prod`.

## Secrets Esperados

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `TF_STATE_BUCKET`
- `TF_STATE_KEY`
- `TF_LOCK_TABLE`, se aplicável
- `DB_USERNAME`
- `DB_PASSWORD`

## Relação Com Os Demais Repositórios

- Produz outputs consumidos por `oficina-dgcar-api`.
- Produz outputs consumidos por `oficina-dgcar-auth-lambda`.
- Produz outputs consumidos por `oficina-dgcar-infra-k8s`.

## Status

Extração inicial realizada a partir do repositório histórico.

Artefatos extraídos:

- Terraform inicial de RDS PostgreSQL em `terraform/**`
- Workflow Terraform em `.github/workflows/terraform.yml`

O commit de origem está registrado em [`ORIGEM_HISTORICA.md`](./ORIGEM_HISTORICA.md).

## Dependências De Entrada

Este repositório depende dos seguintes valores produzidos por `oficina-dgcar-infra-k8s`:

- `vpc_id`
- `private_subnet_ids`
- `eks_cluster_security_group_id`

Esses valores devem ser informados por `terraform.tfvars`, pipeline ou mecanismo de remote state definido na etapa de infraestrutura.
