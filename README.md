# oficina-dgcar-infra-db

Infraestrutura Terraform do banco de dados gerenciado da Oficina Mecanica DGCar.

## Proposito

Este repositorio provisiona e documenta exclusivamente a camada de dados gerenciada:

- Amazon RDS PostgreSQL;
- DB subnet group;
- security group do banco;
- parameter group PostgreSQL;
- politicas de backup, janela de manutencao, sizing e protecao contra exclusao;
- outputs consumidos pela API, pela Lambda de autenticacao e pela infraestrutura Kubernetes.

## Tecnologias

- Terraform;
- AWS RDS PostgreSQL;
- AWS VPC/Subnets/Security Groups;
- GitHub Actions.

## Separacao De Responsabilidades

Este repositorio nao cria cluster Kubernetes, API Gateway, Lambda ou imagem Docker.

Entradas esperadas de `oficina-dgcar-infra-k8s`:

- `vpc_id`;
- `private_subnet_ids`;
- `eks_cluster_security_group_id`, informado em `allowed_security_group_ids`.

Outputs publicados:

- `rds_endpoint`;
- `rds_port`;
- `db_name`;
- `spring_datasource_url`;
- `rds_security_group_id`;
- `rds_instance_identifier`;
- `db_subnet_group_name`;
- `db_parameter_group_name`.

## State Terraform

O backend remoto usa S3 com lock em DynamoDB.

Secrets esperados:

- `AWS_ACCESS_KEY_ID`;
- `AWS_SECRET_ACCESS_KEY`;
- `AWS_REGION`;
- `TF_STATE_BUCKET`;
- `TF_STATE_KEY`;
- `TF_LOCK_TABLE`;
- `VPC_ID`;
- `PRIVATE_SUBNET_IDS`;
- `ALLOWED_DB_SECURITY_GROUP_IDS`;
- `DB_USERNAME`;
- `DB_PASSWORD`.

Recomendacao de chaves de state:

- homologacao: `oficina-dgcar/infra-db/homolog/terraform.tfstate`;
- producao: `oficina-dgcar/infra-db/prod/terraform.tfstate`.

## Pipeline

Pull Requests executam:

- `terraform fmt -check -recursive`;
- `terraform init`;
- `terraform validate`;
- `terraform plan`.

Push em `homolog` aplica no environment `homolog`.

Push em `main` aplica no environment `prod`, sujeito a aprovacao do environment no GitHub.

## Execucao Local

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init -backend=false -reconfigure
terraform fmt -recursive
terraform validate
terraform plan
```

## Backup, Sizing E Seguranca

- Storage criptografado com `storage_encrypted = true`.
- Banco sem acesso publico.
- Acesso PostgreSQL restrito aos security groups autorizados.
- Backup automatico configurado por `backup_retention_period`.
- Janela de backup e manutencao configuraveis.
- Protecao contra exclusao habilitada por padrao.
- Snapshot final habilitado por padrao para remocoes controladas.

## Origem Historica

O commit de origem e a rastreabilidade da extracao estao registrados em [`ORIGEM_HISTORICA.md`](./ORIGEM_HISTORICA.md).
