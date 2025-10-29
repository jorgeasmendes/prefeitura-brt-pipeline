# install_script.ps1
# Executar com: powershell -ExecutionPolicy Bypass -File .\install_script.ps1

# Ativar o modo de erro
$ErrorActionPreference = "Stop"

# --- Sempre execute a partir do diretório do script ---
$SCRIPT_DIR = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $SCRIPT_DIR

# --- Pegar dados do usuário ---
$GCP_PROJECT = Read-Host "Digite o ID do projeto GCP"
$GCS_BUCKET  = Read-Host "Digite o nome do seu bucket GCS ou um novo nome de bucket a ser criado"

# Validar entradas
if ([string]::IsNullOrWhiteSpace($GCP_PROJECT) -or [string]::IsNullOrWhiteSpace($GCS_BUCKET)) {
    Write-Error "Os campos são obrigatórios."
    exit 1
}

# --- Backup do Dockerfile ---
Copy-Item -Path "Dockerfile" -Destination "Dockerfile.bak" -Force

# --- Substituir placeholders no Dockerfile ---
(Get-Content Dockerfile) |
    ForEach-Object {
        $_ -replace 'ENV GCP_PROJECT=.*', "ENV GCP_PROJECT=`"$GCP_PROJECT`"" `
           -replace 'ENV GCS_BUCKET=.*', "ENV GCS_BUCKET=`"$GCS_BUCKET`""
    } | Set-Content Dockerfile

Write-Host "Dockerfile atualizado com sucesso!"
Select-String -Path Dockerfile -Pattern "ENV GCP_PROJECT|ENV GCS_BUCKET"

# Subir container do agent
Write-Host "Criando imagem do container para execução do flow"
docker build -t brt-job-run .
Write-Host "Container criado"

# Criar ambiente virtual
Write-Host "Criando ambiente virtual..."
python -m venv venv
Write-Host "Ativando ambiente virtual..."
& .\venv\Scripts\Activate.ps1
Write-Host "Ambiente virtual criado"

# Instalar dependências
Write-Host "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Dependências instaladas"

# Subir servidor Prefect
Write-Host "Subindo servidor Prefect..."
prefect backend server
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "prefect server start" -WindowStyle Hidden
Start-Sleep -Seconds 5

# Solicita que o usuário verifique se o servidor está no ar
Write-Host ""
Write-Host "Acesse http://localhost:8080 para verificar se o servidor Prefect está online."
Write-Host "Quando estiver pronto, pressione ENTER para continuar..."
Read-Host

# Criar projeto e registrar flow
Write-Host "Criando projeto e registrando o flow..."
prefect create project brt-pipeline
prefect register --project brt-pipeline -p pipeline/flow.py

# Ativar Docker agent
Write-Host "Ativando Docker agent..."
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "prefect agent docker start" -WindowStyle Normal
