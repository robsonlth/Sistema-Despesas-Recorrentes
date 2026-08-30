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


@app.post("/departamentos", response_model=schemas.DepartamentoResponse)
def criar_departamento(
    departamento: schemas.DepartamentoCreate,
    db: Session = Depends(get_db)
):
    novo_departamento = models.Departamento(**departamento.model_dump())

    db.add(novo_departamento)
    db.commit()
    db.refresh(novo_departamento)

    return novo_departamento


@app.get("/departamentos", response_model=list[schemas.DepartamentoResponse])
def listar_departamentos(db: Session = Depends(get_db)):
    departamentos = db.query(models.Departamento).all()
    return departamentos


@app.get("/departamentos/{departamento_id}", response_model=schemas.DepartamentoResponse)
def buscar_departamento(
    departamento_id: int,
    db: Session = Depends(get_db)
):
    departamento = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id
    ).first()

    if departamento is None:
        raise HTTPException(
            status_code=404,
            detail="Departamento não encontrado!"
        )

    return departamento


@app.put("/departamentos/{departamento_id}", response_model=schemas.DepartamentoResponse)
def atualizar_departamento(
    departamento_id: int,
    dados_departamento: schemas.DepartamentoCreate,
    db: Session = Depends(get_db)
):
    departamento = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id
    ).first()

    if departamento is None:
        raise HTTPException(
            status_code=404,
            detail="Departamento não encontrado!"
        )

    departamento.nome = dados_departamento.nome
    departamento.ativo = dados_departamento.ativo

    db.commit()
    db.refresh(departamento)

    return departamento


@app.delete("/departamentos/{departamento_id}", response_model=schemas.DepartamentoResponse)
def excluir_departamento(
    departamento_id: int,
    db: Session = Depends(get_db)
):
    departamento = db.query(models.Departamento).filter(
        models.Departamento.id == departamento_id
    ).first()

    if departamento is None:
        raise HTTPException(
            status_code=404,
            detail="Departamento não encontrado!"
        )

    departamento.ativo = False

    db.commit()
    db.refresh(departamento)

    return departamento


@app.post("/naturezas-financeiras", response_model=schemas.NaturezaFinanceiraResponse)
def criar_natureza_financeira(
    natureza_financeira: schemas.NaturezaFinanceiraCreate,
    db: Session = Depends(get_db)
):
    nova_natureza_financeira = models.NaturezaFinanceira(
        **natureza_financeira.model_dump()
    )

    db.add(nova_natureza_financeira)
    db.commit()
    db.refresh(nova_natureza_financeira)

    return nova_natureza_financeira


@app.get(
    "/naturezas-financeiras",
    response_model=list[schemas.NaturezaFinanceiraResponse]
)
def listar_naturezas_financeiras(db: Session = Depends(get_db)):
    naturezas_financeiras = db.query(models.NaturezaFinanceira).all()
    return naturezas_financeiras


@app.get(
    "/naturezas-financeiras/{natureza_financeira_id}",
    response_model=schemas.NaturezaFinanceiraResponse
)
def buscar_natureza_financeira(
    natureza_financeira_id: int,
    db: Session = Depends(get_db)
):
    natureza_financeira = db.query(models.NaturezaFinanceira).filter(
        models.NaturezaFinanceira.id == natureza_financeira_id
    ).first()

    if natureza_financeira is None:
        raise HTTPException(
            status_code=404,
            detail="Natureza financeira não encontrada!"
        )

    return natureza_financeira


@app.put(
    "/naturezas-financeiras/{natureza_financeira_id}",
    response_model=schemas.NaturezaFinanceiraResponse
)
def atualizar_natureza_financeira(
    natureza_financeira_id: int,
    dados_natureza_financeira: schemas.NaturezaFinanceiraCreate,
    db: Session = Depends(get_db)
):
    natureza_financeira = db.query(models.NaturezaFinanceira).filter(
        models.NaturezaFinanceira.id == natureza_financeira_id
    ).first()

    if natureza_financeira is None:
        raise HTTPException(
            status_code=404,
            detail="Natureza financeira não encontrada!"
        )

    natureza_financeira.nome = dados_natureza_financeira.nome
    natureza_financeira.ativo = dados_natureza_financeira.ativo

    db.commit()
    db.refresh(natureza_financeira)

    return natureza_financeira


@app.delete(
    "/naturezas-financeiras/{natureza_financeira_id}",
    response_model=schemas.NaturezaFinanceiraResponse
)
def excluir_natureza_financeira(
    natureza_financeira_id: int,
    db: Session = Depends(get_db)
):
    natureza_financeira = db.query(models.NaturezaFinanceira).filter(
        models.NaturezaFinanceira.id == natureza_financeira_id
    ).first()

    if natureza_financeira is None:
        raise HTTPException(
            status_code=404,
            detail="Natureza financeira não encontrada!"
        )

    natureza_financeira.ativo = False

    db.commit()
    db.refresh(natureza_financeira)

    return natureza_financeira


@app.post("/rateios", response_model=schemas.RateioResponse)
def criar_rateio(
    rateio: schemas.RateioCreate,
    db: Session = Depends(get_db)
):
    novo_rateio = models.Rateio(**rateio.model_dump())

    db.add(novo_rateio)
    db.commit()
    db.refresh(novo_rateio)

    return novo_rateio


@app.get("/rateios", response_model=list[schemas.RateioResponse])
def listar_rateios(db: Session = Depends(get_db)):
    rateios = db.query(models.Rateio).all()
    return rateios


@app.get("/rateios/{rateio_id}", response_model=schemas.RateioResponse)
def buscar_rateio(
    rateio_id: int,
    db: Session = Depends(get_db)
):
    rateio = db.query(models.Rateio).filter(
        models.Rateio.id == rateio_id
    ).first()

    if rateio is None:
        raise HTTPException(
            status_code=404,
            detail="Rateio não encontrado!"
        )

    return rateio


@app.put("/rateios/{rateio_id}", response_model=schemas.RateioResponse)
def atualizar_rateio(
    rateio_id: int,
    dados_rateio: schemas.RateioCreate,
    db: Session = Depends(get_db)
):
    rateio = db.query(models.Rateio).filter(
        models.Rateio.id == rateio_id
    ).first()

    if rateio is None:
        raise HTTPException(
            status_code=404,
            detail="Rateio não encontrado!"
        )

    rateio.nome = dados_rateio.nome
    rateio.ativo = dados_rateio.ativo

    db.commit()
    db.refresh(rateio)

    return rateio


@app.delete("/rateios/{rateio_id}", response_model=schemas.RateioResponse)
def excluir_rateio(
    rateio_id: int,
    db: Session = Depends(get_db)
):
    rateio = db.query(models.Rateio).filter(
        models.Rateio.id == rateio_id
    ).first()

    if rateio is None:
        raise HTTPException(
            status_code=404,
            detail="Rateio não encontrado!"
        )

    rateio.ativo = False

    db.commit()
    db.refresh(rateio)

    return rateio


@app.post("/despesas-recorrentes", response_model=schemas.DespesaRecorrenteResponse)
def criar_despesa(
    despesa: schemas.DespesaRecorrenteCreate,
    db: Session = Depends(get_db)
):
    nova_despesa = models.DespesaRecorrente(**despesa.model_dump())

    db.add(nova_despesa)
    db.commit()
    db.refresh(nova_despesa)

    return nova_despesa


@app.get("/despesas-recorrentes", response_model=list[schemas.DespesaRecorrenteResponse])
def listar_despesas_recorrentes(
    db: Session = Depends(get_db)
):
    despesas = db.query(models.DespesaRecorrente).all()

    return despesas


@app.get("/despesas-recorrentes/{despesa_id}", response_model=schemas.DespesaRecorrenteResponse)
def buscar_despesa_recorrente(
    despesa_id: int,
    db: Session = Depends(get_db)
):
    despesa = db.query(models.DespesaRecorrente).filter(
        models.DespesaRecorrente.id == despesa_id
    ).first()

    if despesa is None:
        raise HTTPException(
            status_code=404,
            detail="Despesa não encontrada!"
        )

    return despesa


@app.put("/despesas-recorrentes/{despesa_id}", response_model=schemas.DespesaRecorrenteResponse)
def atualizar_despesa_recorrente(
    despesa_id: int,
    dados_despesa: schemas.DespesaRecorrenteCreate,
    db: Session = Depends(get_db)
):
    despesa = db.query(models.DespesaRecorrente).filter(
        models.DespesaRecorrente.id == despesa_id
    ).first()

    if despesa is None:
        raise HTTPException(
            status_code=404,
            detail="Despesa não encontrada!"
        )

    despesa.fornecedor_id = dados_despesa.fornecedor_id
    despesa.departamento_id = dados_despesa.departamento_id
    despesa.natureza_financeira_id = dados_despesa.natureza_financeira_id
    despesa.rateio_id = dados_despesa.rateio_id
    despesa.descricao = dados_despesa.descricao
    despesa.data_inicio_vigencia = dados_despesa.data_inicio_vigencia
    despesa.data_fim_vigencia = dados_despesa.data_fim_vigencia
    despesa.valor_estimado = dados_despesa.valor_estimado
    despesa.ativo = dados_despesa.ativo

    db.commit()
    db.refresh(despesa)

    return despesa


@app.delete("/despesas-recorrentes/{despesa_id}", response_model=schemas.DespesaRecorrenteResponse)
def excluir_despesa_recorrente(
    despesa_id: int,
    db: Session = Depends(get_db)
):
    despesa = db.query(models.DespesaRecorrente).filter(
        models.DespesaRecorrente.id == despesa_id
    ).first()

    if despesa is None:
        raise HTTPException(
            status_code=404,
            detail="Despesa não encontrada!"
        )

    despesa.ativo = False

    db.commit()
    db.refresh(despesa)

    return despesa
