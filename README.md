# prefeitura-brt-pipeline
Desafio técnico do processo seletivo para o cargo de Engenheiro de Dados na Central de Inteligência Vigilância e Tecnologia em Apoio à Segurança Pública - CIVITAS

## Descrição
Construção de um pipeline de dados ELT, orquestrado com Prefect, que:
1. Captura dados de uma API com informações de GPS dos veículos do BRT do Rio de Janeiro por 10 minutos em intervalos de 1 minuto;
2. Sobe os dados para um bucket no Google Coud Storage;
3. Roda job DBT que materializa uma tabela externa no BigQuery referenciando os dados do Storage (Camada Bronze), além de criar uma view de limpeza e transformação dos dados (Camada Silver) que, por sua vez, é utilizada para materializar uma tabela particionada pronta para análises (Camada Gold).

## Entregas
- Pipeline Prefect: `pipeline/flow.py`
- Projeto DBT: `pipeline/dbt_project/`
- CSV de exemplo + capturas de tela das tabelas: `examples/`

## Instruções de execução
1. **Clonar este repositório**
Executar os comandos:
git clone https://github.com/usuario/prefeitura-brt-pipeline.git
cd prefeitura-brt-pipeline

2. **Adicionar chave GCP**
- Gere uma chave JSON da sua conta de serviço no GCP
- Permissões necessárias: Storage Admin e BigQuery Admin
- Mude o nome do arquivo para key.json e coloque na pasta gcp_key/

3. **Configurar o Docker**
Abra o Dockerfile e altere a variável de ambiente GCP_PROJECT para o ID do seu projeto. 

4. **Instalar dependências e rodar servidor Prefect**
- Em um terminal na pasta raiz, rodar os seguintes comandos:
pip install marshmallow>=3,<4 prefect[github]==1.4.1
docker build -t brt-job-run .
prefect backend server
prefect server start

5. **Registrar o pipeline e ativar o agent**
- Aguarde o servidor iniciar, abra outro terminal na pasta raiz e rode os comandos:
prefect create project brt-pipeline
prefect register --project brt-pipeline -p pipeline/flow.py
prefect agent docker start

6. **Acessar a UI do Prefect e rodar o pipeline**
- Abra o seu navegador e digite o endereço http://localhost:8080/
- Vá em Flows → selecione brt-pipeline → clique em Quick Run
- Acompanhe a execução do pipeline e verifique:
    - Criação do bucket com o arquivo CSV;
    - Tabelas no BigQuery no dataset definido (brt_dataset).