# Compasso

Sistema de controle de despesas recorrentes que permite cadastrar despesas e rateios, acompanhar lançamentos e vencimentos e comparar os valores estimados e realizados por competência.

Tecnologias: Python, FastAPI, SQLAlchemy, PostgreSQL, React e Vite.

## Executar localmente

No PowerShell, a partir da raiz do projeto, inicie o backend:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Em outro terminal, também a partir da raiz, inicie o frontend:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```
