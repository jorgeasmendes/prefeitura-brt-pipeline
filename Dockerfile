FROM python:3.10-slim

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY pipeline/dbt_project /dbt_project

COPY gcp_key/key.json /gcp_key/key.json

ENV GOOGLE_APPLICATION_CREDENTIALS=/gcp_key/key.json

ENV BIGQUERY_DATASET="brt_dataset"

ENV GCP_PROJECT="estudo_elt"
