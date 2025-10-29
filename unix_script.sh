#!/usr/bin/env bash
set -euo pipefail

# sempre execute a partir do diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Pegar dados de variáveis de ambiente
read -rp "Digite o ID do projeto GCP: " GCP_PROJECT
read -rp "Digite o nome do seu bucket GCS ou um nome de bucket inédito: " GCS_BUCKET

# Validar entradas
if [[ -z "$GCP_PROJECT" || -z "$GCS_BUCKET" ]]; then
  echo "Os campos são obrigatórios."
  exit 1
fi

# Criar backup de segurança do Dockerfile
cp Dockerfile Dockerfile.bak
echo "Backup criado: Dockerfile.bak"

# --- Substituir os placeholders no Dockerfile ---
sed -i "s|ENV GCP_PROJECT=.*|ENV GCP_PROJECT=\"${GCP_PROJECT}\"|g" Dockerfile
sed -i "s|ENV GCS_BUCKET=.*|ENV GCS_BUCKET=\"${GCS_BUCKET}\"|g" Dockerfile

echo "Dockerfile atualizado com sucesso!"
grep -E 'ENV GCP_PROJECT|ENV GCS_BUCKET' Dockerfile

echo "Criando imagem do container para execução do flow"
docker build -t brt-job-run .
echo "Container criado"

echo "Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate
echo "Ambiente virtual criado"

echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependências instaladas"

echo "Subindo o servidor Prefect..."
prefect backend server
prefect server start > server.log 2>&1 &
SERVER_PID=$!

sleep 5
echo ""
echo "Acesse http://localhost:8080 para verificar se o servidor Prefect está online."
read -rp "Quando estiver pronto, pressione ENTER para continuar..."

# Criar projeto e registrar o flow
echo "Criando projeto e registrando o flow..."
prefect create project brt-pipeline || true
prefect register --project brt-pipeline -p pipeline/flow.py

# Ativar Docker agent
echo "Ativando o Docker agent..."
prefect agent docker start