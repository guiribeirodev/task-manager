#!/bin/sh

# Executa as migrações do banco de dados
uv run --no-sync alembic upgrade head

# Inicia a aplicação
uv run --no-sync uvicorn --host 0.0.0.0 --port 8000 fast_zero.app:app
