import requests
import pandas as pd
from datetime import datetime
import pytz
import time
import os
from prefect import task


#Task para baixar os dados da API e salvar em csv com função auxiliar
def download_data(i):
    try:
        response = requests.get("https://dados.mobilidade.rio/gps/brt")
        response.raise_for_status()
    except response.status_code() as e:
        print(f"Erro ao fazer download de número {i}, código: {e}")
        return None
    else:
        print(f"Download da iteração {i} realizado com sucesso")
        return response.json()
@task
def api_to_csv():
    for i in range(1,5):
        print(f"Começando iteração {i}...")
        dict_data = download_data(i)
        df = pd.DataFrame(dict_data["veiculos"])
        df["datetime_registro"] = datetime.now(pytz.timezone('America/Sao_Paulo'))
        file_exists = os.path.exists("brt-dados.csv")
        df.to_csv("brt-dados.csv", mode='a', index=False, header=not file_exists)
        print(f"Iteração {i} concluída")
        time.sleep(10)
