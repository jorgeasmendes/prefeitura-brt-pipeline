from prefect import Flow, task
from prefect.storage import GitHub
from prefect.run_configs import DockerRun
import requests
import pandas as pd
from datetime import datetime
import pytz
import time
import os
from google.cloud import storage

formated_timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y%m%d_%H%M%S")
CSV_FILENAME = f"brt-dados-{formated_timestamp}.csv"
BUCKET_NAME = "brt-pipeline-data"

#Task para baixar os dados da API e salvar em csv com função auxiliar
def download_data(i):
    try:
        response = requests.get("https://dados.mobilidade.rio/gps/brt")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao fazer download de número {i}, código: {e}")
        return None
    else:
        print(f"Download da iteração {i} realizado com sucesso")
        return response.json()
    
@task(log_stdout=True)
def api_to_csv():
    for i in range(1,5):
        print(f"Começando iteração {i}...")
        dict_data = download_data(i)
        df = pd.DataFrame(dict_data["veiculos"])
        df["datetime_registro"] = datetime.now(pytz.timezone('America/Sao_Paulo'))
        file_exists = os.path.exists(CSV_FILENAME)
        df.to_csv(CSV_FILENAME, mode='a', index=False, header=not file_exists)
        print(f"Iteração {i} concluída")
        time.sleep(10)

#Task para subir os dados para o Google Storage
@task(log_stdout=True)
def upload_csv(bucket_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    if bucket.exists():
        print("Bucket já existe")
    else: 
        print("O bucket ainda não existe. Criando bucket...")
        bucket = client.create_bucket(bucket_name, location="US")
        print("Bucket criado")
    
    print(f"Preparando upload de {CSV_FILENAME} para gs://{bucket.name}/")
    blob_str = f"{datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y/%m/%d')}/{CSV_FILENAME}"
    blob = bucket.blob(blob_str)
    try:
        blob.upload_from_filename(CSV_FILENAME)
        print(f"Upload concluído: gs://{bucket.name}/{blob_str}")
        return True
    except Exception as e:
        print(f"Erro ao fazer upload dos dados: {e}")
        return False


with Flow("brt-pipeline") as flow:
    download_data_from_api = api_to_csv()
    
    upload_data_togcp = upload_csv(BUCKET_NAME)
    upload_data_togcp.set_upstream(download_data_from_api)

flow.storage = GitHub(repo="jorgeasmendes/prefeitura-brt-pipeline",path="pipeline/flow.py")
flow.run_config = DockerRun(image="brt-job-run")