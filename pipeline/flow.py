from tasks import api_to_csv
from prefect import Flow
from prefect.storage import GitHub

with Flow("brt-pipeline") as flow:
    api_to_csv()

flow.storage = GitHub(repo="jorgeasmendes/prefeitura-brt-pipeline",path="pipeline/flow.py")