import requests
import pandas as pd

#Funções para baixar os dados da API e salvar em csv
def download_data():
    try:
        response = requests.get("https://dados.mobilidade.rio/gps/brt")
        response.raise_for_status()
    except response.status_code() as e:
        print(f"Erro ao fazer download, código: {e}")
        return None
    else:
        print("Download realizado com sucesso")
        return response.json()

def to_csv(json_data):
    df = pd.DataFrame(json_data["veiculos"])
    print(df.head())

to_csv(download_data())
