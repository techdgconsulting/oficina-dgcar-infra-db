# Operacao Da Infraestrutura De Banco

## Conexao

A aplicacao deve consumir o output `spring_datasource_url` como URL JDBC e armazenar usuario/senha em secret do ambiente de execucao.

## Ambientes

- `homolog`: usado para validacao integrada antes de producao.
- `prod`: protegido por aprovacao no GitHub Environment.

## Backup

O RDS usa backup automatico. A retencao padrao e de 7 dias, ajustavel por `backup_retention_period`.

## Sizing

Configuracao academica inicial:

- instancia: `db.t4g.micro`;
- storage inicial: 20 GiB;
- autoscaling de storage: 30 GiB;
- Multi-AZ desativado por padrao para controle de custo.

Para producao real, recomenda-se habilitar Multi-AZ, elevar a classe da instancia e aumentar a retencao de backup.

## Seguranca

- O banco nao e publico.
- O acesso e limitado por security groups.
- A senha nao deve ser versionada.
- O state remoto deve estar criptografado e com lock ativo.
