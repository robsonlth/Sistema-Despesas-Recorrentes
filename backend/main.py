from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def inicio():
    return {
        "mensagem": "Sistema de despesas recorrentes funcionando!"
    }