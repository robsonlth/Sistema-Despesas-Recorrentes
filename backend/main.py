from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import Base, SessionLocal, engine

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/fornecedores", response_model=schemas.FornecedorResponse)
def criar_fornecedor(
    fornecedor: schemas.FornecedorCreate,
    db: Session = Depends(get_db)
):
    novo_fornecedor = models.Fornecedor(**fornecedor.model_dump())

    db.add(novo_fornecedor)
    db.commit()
    db.refresh(novo_fornecedor)

    return novo_fornecedor


@app.get("/fornecedores", response_model=list[schemas.FornecedorResponse])
def listar_fornecedores(db: Session = Depends(get_db)):
    fornecedores = db.query(models.Fornecedor).all()
    return fornecedores


@app.get("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def buscar_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db)
):
    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == fornecedor_id
    ).first()

    if fornecedor is None:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado!"
        )

    return fornecedor


@app.put("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def atualizar_fornecedor(
    fornecedor_id: int,
    dados_fornecedor: schemas.FornecedorCreate,
    db: Session = Depends(get_db)
):
    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == fornecedor_id
    ).first()

    if fornecedor is None:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado!"
        )

    fornecedor.nome = dados_fornecedor.nome
    fornecedor.cnpj = dados_fornecedor.cnpj
    fornecedor.ativo = dados_fornecedor.ativo

    db.commit()
    db.refresh(fornecedor)

    return fornecedor


@app.delete("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def excluir_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db)
):
    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == fornecedor_id
    ).first()

    if fornecedor is None:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado!"
        )

    fornecedor.ativo = False

    db.commit()
    db.refresh(fornecedor)

    return fornecedor
