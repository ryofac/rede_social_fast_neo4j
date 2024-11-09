#!/bin/sh
set -e

# Rodar as migrações
# echo "Rodando migrações..."
# alembic upgrade head

# Iniciar o servidor FastAPI
echo "Iniciando o servidor FastAPI..."
exec fastapi dev social_network/main.py --port 8000 --host 0.0.0.0
