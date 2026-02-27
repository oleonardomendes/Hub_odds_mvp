# Odds MVP (manual odds) — FastAPI + SQLite

Este projeto é um MVP local para:
- navegar por jogos (dataset local)
- ver estatísticas pré-jogo (últimos N)
- **informar odds manualmente**
- receber **probabilidade estimada**, **probabilidade implícita**, **EV**, e um **score de risco**.

## Requisitos
- Docker + Docker Compose **ou** Python 3.11+

## Rodar com Docker
```bash
docker compose up --build
```
Acesse:
- UI: http://localhost:8000
- Docs: http://localhost:8000/docs

## Rodar sem Docker
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
export DB_PATH=./data/app.db   # Windows: set DB_PATH=./data/app.db
uvicorn app.main:app --reload
```

## Como usar (fluxo MVP)
1. Abra a UI em `/` e selecione um jogo.
2. Escolha mercado (OU2.5 ou BTTS).
3. Informe a odd decimal (ex.: 1.95) e clique em **Calcular**.

## Dataset
- O banco SQLite vem pré-populado em `data/app.db`.
- Você pode trocar/expandir criando suas próprias partidas e resultados.

## Nota importante
Este MVP não busca odds automaticamente (você digita), e o modelo é **estatístico explicável**:
- OU2.5 e BTTS via **Poisson** com lambdas estimados por médias móveis (home/away + geral).
