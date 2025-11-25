import prefect
from prefect.utilities.logging import get_logger
from prefect import Flow, task, Parameter
from prefect.storage import GitHub
from prefect.run_configs import DockerRun
import requests
import pandas as pd
from datetime import datetime
import pytz
import time
import os
import subprocess
from google.cloud import storage, bigquery


formated_timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y%m%d_%H%M%S")
CSV_FILENAME = f"brt-dados-{formated_timestamp}.csv"
BUCKET_NAME = os.getenv("GCS_BUCKET")
DATASET_NAME = os.getenv("BIGQUERY_DATASET")

#Task para baixar os dados da API e salvar em csv com função auxiliar
def download_data(i):
    logger = get_logger()
    try:
        response = requests.get("https://dados.mobilidade.rio/gps/brt")
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Erro ao fazer download de número {i}, código: {e}")
        return None
    else:
        logger.info(f"Download da iteração {i} realizado com sucesso")
        return response.json()
    
@task
def api_to_csv(iterations, interval):
    logger = prefect.context.get("logger")
    for i in range(1,iterations+1):
        logger.info(f"Começando iteração {i}...")
        dict_data = download_data(i)
        if(dict_data):
            df = pd.DataFrame(dict_data["veiculos"])
            df["datetime_registro"] = datetime.now(pytz.timezone('America/Sao_Paulo'))
            file_exists = os.path.exists(CSV_FILENAME)
            df.to_csv(CSV_FILENAME, mode='a', index=False, header=not file_exists)
            logger.info(f"Iteração {i} concluída")
            if i<iterations:
                logger.info(f"Aguardando o tempo para a próxima iteração...")
                time.sleep(interval)

#Task para subir os dados para o Google Storage
@task
def upload_csv(bucket_name):
    logger = prefect.context.get("logger")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    if bucket.exists():
        logger.info("Bucket já existe")
    else: 
        logger.info("O bucket ainda não existe. Criando bucket...")
        bucket = client.create_bucket(bucket_name, location="US")
        logger.info("Bucket criado")
    
    logger.info(f"Preparando upload de {CSV_FILENAME} para gs://{bucket.name}/")
    blob_str = f"date={datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y-%m-%d')}/{CSV_FILENAME}"
    blob = bucket.blob(blob_str)
    try:
        blob.upload_from_filename(CSV_FILENAME)
        logger.info(f"Upload concluído: gs://{bucket.name}/{blob_str}")
        return True
    except Exception as e:
        logger.error(f"Erro ao fazer upload dos dados: {e}")
        return False

#Funções para rodar DBT materializando dados do bucket no BigQuery
def create_dataset():
    logger = get_logger()
    try:
        client = bigquery.Client()
        dataset_ref = client.dataset(DATASET_NAME)
        dataset = bigquery.Dataset(dataset_ref)
        client.create_dataset(dataset, exists_ok=True)
        logger.info("Dataset OK")
        return True
    except Exception as e:
        logger.error(f"Erro ao acessar ou criar dataset: {e}")
        return False
@task(log_stdout=True)
def dbt_run(dbt_filter):
    logger = prefect.context.get("logger")
    if create_dataset():
        logger.info("Rodando DBT...")
        os.chdir("/dbt_project")
        try:
            commands = [["dbt", "deps"], 
                        ["dbt", "run-operation", "stage_external_sources"], 
                        ["dbt", "build", "--vars", f"{{dias_historico_brt_silver: {dbt_filter}}}"]]
            for cmd in commands:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                if result.stdout:
                    logger.info(result.stdout)
                if result.stderr:
                    logger.error(result.stderr)
            logger.info("Execução do DBT concluída com sucesso")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao rodar DBT: {e}")
    else:
        logger.info("Execução do DBT abortada")


with Flow("brt-pipeline") as flow:
    iterations = Parameter("Iterações na API", default = 10)
    interval = Parameter("Intervalo entre iterações (em segundos)", default = 60)
    dbt_filter = Parameter("Janela de dias para atualização da tabela", default = 1)

    download_data_from_api = api_to_csv(iterations, interval)
    
    upload_data_togcp = upload_csv(BUCKET_NAME)
    upload_data_togcp.set_upstream(download_data_from_api)

    run_dbt = dbt_run(dbt_filter)
    run_dbt.set_upstream(upload_data_togcp)

flow.storage = GitHub(repo="jorgeasmendes/prefeitura-brt-pipeline",path="pipeline/flow.py")
flow.run_config = DockerRun(image="brt-job-run")