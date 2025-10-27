from pipeline.tasks import api_to_csv
from prefect import Flow

with Flow("brt-pipeline") as flow:
    api_to_csv()