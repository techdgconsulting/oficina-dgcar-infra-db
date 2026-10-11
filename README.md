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

## Documentacao Central

A documentacao arquitetural completa do Tech Challenge 3 esta centralizada em:

[oficina-dgcar-docs](https://github.com/techdgconsulting/oficina-dgcar-docs)

Este repositorio mantem apenas a documentacao especifica da infraestrutura de banco, incluindo Terraform, variaveis, state, outputs, backup, sizing e seguranca.

## Separacao De Responsabilidades

Este repositorio nao cria cluster Kubernetes, API Gateway, Lambda ou imagem Docker.

Entradas esperadas de `oficina-dgcar-infra-k8s`:

- `vpc_id`;
- `private_subnet_ids`;
- `eks_cluster_security_group_id`, informado em `allowed_security_group_ids` como texto separado por virgula.

Entrada esperada de `oficina-dgcar-auth-lambda`:

- `auth_lambda_security_group_id`, informado pelo secret `AUTH_LAMBDA_SECURITY_GROUP_ID`.

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

O backend remoto usa S3 com lockfile nativo:

```text
use_lockfile=true
```

Secrets esperados:

- `AWS_ACCESS_KEY_ID`;
- `AWS_SECRET_ACCESS_KEY`;
- `AWS_REGION`;
- `TF_STATE_BUCKET`;
- `TF_STATE_KEY`;
- `GH_AUTOMATION_TOKEN`;
- `VPC_ID`;
- `PRIVATE_SUBNET_IDS`;
- `ALLOWED_DB_SECURITY_GROUP_IDS`, em formato texto simples, exemplo `sg-xxxx` ou `sg-xxxx,sg-yyyy`;
- `AUTH_LAMBDA_SECURITY_GROUP_ID`;
- `DB_USERNAME`;
- `DB_PASSWORD`.

Chaves de state definidas:

- homologacao: `homolog/infra-db/terraform.tfstate`;
- producao: `prod/infra-db/terraform.tfstate`.

## Pipeline

Pull Requests executam:

- `terraform fmt -check -recursive`;
- `terraform init`;
- `terraform validate`;
- `terraform plan`.

Push em `homolog` ou `main` executa validacao, plan offline e apply do ambiente correspondente.

`workflow_dispatch` com `action=apply` permanece disponivel para reprocessamento operacional controlado. O environment `prod` esta sujeito a aprovacao no GitHub.

Depois do `terraform apply`, o workflow publica automaticamente os outputs do RDS no repo `oficina-dgcar-auth-lambda`.

Destroy real tambem e manual por `workflow_dispatch`, usando `action=destroy`, `confirm_destroy=DESTROY` e o environment desejado. Esse fluxo remove RDS PostgreSQL, subnet group, parameter group e security group do banco antes do destroy da Lambda e antes da destruicao final da VPC no repo `oficina-dgcar-infra-k8s`.

No teardown academico, o banco e destruido antes da Lambda porque o security group do RDS referencia o security group da Lambda como origem autorizada para PostgreSQL.

Em `homolog`, o destroy usa `deletion_protection=false` e `skip_final_snapshot=true` para permitir desligamento recorrente do ambiente academico sem bloqueio de delecao e sem colisao de nomes de snapshot final. Em `prod`, o apply usa `deletion_protection=true`; antes do destroy, o workflow desativa essa protecao e mantem `skip_final_snapshot=false` para preservar snapshot final antes da remocao do RDS.

Antes do `terraform destroy`, o workflow garante que `deletion_protection=false` esteja aplicado na instancia RDS ja existente. Em `prod`, ele tambem sincroniza no state o identificador unico do snapshot final antes da destruicao, evitando que um valor antigo do state tente reutilizar um snapshot ja existente. Esse preparo permite remover `prod` de forma orquestrada sem abrir o console, preservando o snapshot final quando `skip_final_snapshot=false`.

Em `prod`, o identificador do snapshot final inclui `github.run_id` e `github.run_attempt` para evitar colisao com snapshots finais de destroys anteriores.

O backend remoto usa lock nativo do S3 com `use_lockfile=true`.

Politica de backup aplicada por ambiente:

- `homolog`: `backup_retention_period=0`, compatibilizado com restricoes de contas AWS Free Tier usadas no laboratorio;
- `prod`: `backup_retention_period=0`, compatibilizado com a mesma conta AWS Free Tier usada no laboratorio.

Sizing aplicado por ambiente:

- `homolog`: `db_instance_class=db.t3.micro` e `db_storage_type=gp2`, combinacao adotada para reduzir falhas de capacidade em contas Free Tier;
- `prod`: `db_instance_class=db.t3.micro` e `db_storage_type=gp2`, combinacao adotada para executar producao demonstravel na conta Free Tier.

Configuracao efetiva por ambiente:

| Ambiente | Classe RDS | Storage | Retencao de backup | Finalidade |
|---|---|---|---|---|
| `homolog` | `db.t3.micro` | `gp2` | `0` dias | Compatibilidade com restricoes de laboratorio, Free Tier e disponibilidade regional. |
| `prod` | `db.t3.micro` | `gp2` | `0` dias | Configuracao de producao demonstravel compativel com a conta Free Tier. |

As configuracoes acima sao aplicadas pelo workflow via variaveis `TF_VAR_*`, mantendo o Terraform parametrizado e evitando arquivos `.tfvars` com valores reais versionados.

Conectividade Lambda -> RDS:

- `ALLOWED_DB_SECURITY_GROUP_IDS` mantem os security groups autorizados para workloads do Kubernetes em texto separado por virgula;
- `AUTH_LAMBDA_SECURITY_GROUP_ID` adiciona o security group da Lambda Auth CPF a regra de entrada PostgreSQL;
- Terraform consolida os valores em uma lista unica com remocao de duplicados;
- essa configuracao corrige o timeout da Lambda ao consultar o PostgreSQL privado em homologacao.

Secrets gravados em `oficina-dgcar-auth-lambda`:

- `DB_HOST`;
- `DB_PORT`;
- `DB_NAME`;
- `DB_USERNAME`;
- `DB_PASSWORD`;
- `DB_SSL`.

## Automacao Entre Repositorios

O workflow usa `GH_AUTOMATION_TOKEN` para gravar secrets no repo da Lambda via GitHub CLI. Esse token fica configurado nos environments `homolog` e `prod`.

Fluxo automatizado:

1. `oficina-dgcar-infra-db` executa `apply`.
2. Terraform publica `rds_endpoint`, `rds_port` e `db_name`.
3. O workflow grava os dados de conexao do banco no repo `oficina-dgcar-auth-lambda`.
4. O secret `AUTH_LAMBDA_SECURITY_GROUP_ID`, publicado por `oficina-dgcar-auth-lambda`, compoe a regra de entrada do RDS.
5. A Lambda passa a ter os secrets necessarios para o `apply-infra` e permissao de rede para consultar o PostgreSQL.

## Ajustes Operacionais Registrados

Durante o provisionamento de homologacao, a conta AWS retornou duas restricoes operacionais:

- `FreeTierRestrictionError`: a retencao de backup configurada inicialmente excedia o limite disponivel para a conta Free Tier;
- `InsufficientDBInstanceCapacity`: a combinacao `db.t4g.micro` com `gp3` nao possuia capacidade disponivel nas Availability Zones da VPC no momento do apply.

As correcoes implementadas foram:

- `backup_retention_period=0` para `homolog` e `prod`;
- `db_instance_class=db.t3.micro` para `homolog` e `prod`;
- `db_storage_type=gp2` para `homolog` e `prod`;
- `storage_type` parametrizado no Terraform por `var.db_storage_type`.

O state remoto preserva os recursos ja criados antes de uma falha parcial. Em uma nova execucao do workflow, Terraform retoma o apply a partir do estado salvo no S3 e tenta criar apenas os recursos pendentes, como a instancia RDS.

## Execucao Local

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init -backend=false -reconfigure
terraform fmt -recursive
terraform validate
terraform plan
```

Para executar `terraform plan` sem acesso ao backend remoto, renomeie temporariamente `backend.tf` antes do `terraform init`.

## Backup, Sizing E Seguranca

- Storage criptografado com `storage_encrypted = true`.
- Tipo de storage definido por ambiente com `db_storage_type`.
- Banco sem acesso publico.
- Acesso PostgreSQL restrito aos security groups autorizados.
- Backup automatico configurado por `backup_retention_period`, com valor por ambiente definido no workflow.
- Classe de instancia e tipo de storage definidos por ambiente no workflow.
- Janela de backup e manutencao configuraveis.
- Protecao contra exclusao habilitada por padrao.
- Snapshot final habilitado por padrao para remocoes controladas.

## Origem Historica

O commit de origem e a rastreabilidade da extracao estao registrados em [`ORIGEM_HISTORICA.md`](./ORIGEM_HISTORICA.md).
