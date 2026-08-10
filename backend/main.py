from fastapi import FastAPI
from sqlalchemy import text

from backend import models
from backend.database import Base, engine

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def inicio():
    return {
        "mensagem": "Sistema de despesas recorrentes funcionando!"
    }


@app.get("/teste-banco")
def teste_banco():
    with engine.connect() as connection:
        resultado = connection.execute(
            text("SELECT current_database()")
        )

        banco = resultado.scalar()

    return {
        "status": "conectado",
        "banco": banco
    }