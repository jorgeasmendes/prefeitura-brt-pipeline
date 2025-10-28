FROM python:3.10-slim

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY gcp_key/key.json .

ENV GOOGLE_APPLICATION_CREDENTIALS=key.json
