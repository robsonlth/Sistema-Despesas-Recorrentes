# Rotas da API: recebem as requisições e acessam os dados pelo SQLAlchemy.
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy import text, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.database import Base, SessionLocal, engine

# Cria a aplicação FastAPI.
app = FastAPI()

# Cria as tabelas que ainda não existem no banco.
Base.metadata.create_all(bind=engine)


# Confere o CNPJ no cadastro e na atualização, incluindo fornecedores inativos.
def validar_cnpj_unico(cnpj: str | None, db: Session, fornecedor_id: int | None = None):
    if cnpj is None:
        return

    # Considera também CNPJs antigos que tenham sido salvos com letras minúsculas.
    consulta = db.query(models.Fornecedor).filter(func.upper(models.Fornecedor.cnpj) == cnpj)

    # Na atualização, o fornecedor pode manter o próprio CNPJ.
    if fornecedor_id is not None:
        consulta = consulta.filter(models.Fornecedor.id != fornecedor_id)

    if consulta.first() is not None:
        raise HTTPException(status_code=409, detail="Já existe um fornecedor com esse CNPJ.")


# Confere se os cadastros ligados à despesa existem antes de salvar.
def validar_relacionamentos_despesa(
    dados_despesa: schemas.DespesaRecorrenteCreate,
    db: Session
):

    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == dados_despesa.fornecedor_id
    ).first()

    if fornecedor is None:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado!"
        )

    natureza = db.query(models.NaturezaFinanceira).filter(
        models.NaturezaFinanceira.id == dados_despesa.natureza_financeira_id
    ).first()
        
    if natureza is None:
        raise HTTPException(
            status_code=404,
            detail="Natureza financeira não encontrada!"
        )
    
    departamento = db.query(models.Departamento).filter(
        models.Departamento.id == dados_despesa.departamento_id
    ).first()
        
    if departamento is None:
        raise HTTPException(
            status_code=404,
            detail="Departamento não encontrado!"
        )
        
    rateio = db.query(models.Rateio).filter(
        models.Rateio.id == dados_despesa.rateio_id
    ).first()
        
    if rateio is None:
        raise HTTPException(
            status_code=404,
            detail="Rateio não encontrado!"
        )


# Início: confirma que a API está funcionando.
@app.get("/")
def inicio():
    return {
        "mensagem": "Sistema de despesas recorrentes funcionando!"
    }


# Conexão: consulta o nome do banco para verificar o acesso ao PostgreSQL.
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


# Abre uma sessão para a requisição e a fecha ao terminar, mesmo se ocorrer um erro.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fornecedores
# POST: cadastra um fornecedor.
@app.post("/fornecedores", response_model=schemas.FornecedorResponse)
def criar_fornecedor(
    fornecedor: schemas.FornecedorCreate,
    db: Session = Depends(get_db)
):
    validar_cnpj_unico(fornecedor.cnpj, db)

    # Converte os dados validados pelo schema em um objeto do model.
    novo_fornecedor = models.Fornecedor(**fornecedor.model_dump())

    # Salva o fornecedor e carrega os dados gerados pelo banco.
    db.add(novo_fornecedor)
    try:
        db.commit()
    except IntegrityError:
        # Outro cadastro pode ter usado o CNPJ entre a consulta e o commit.
        db.rollback()
        validar_cnpj_unico(fornecedor.cnpj, db)
        # Se o erro não for CNPJ duplicado, preserva o erro original para investigação.
        raise
    db.refresh(novo_fornecedor)

    return novo_fornecedor


# GET: lista todos os fornecedores, incluindo os inativos.
@app.get("/fornecedores", response_model=list[schemas.FornecedorResponse])
def listar_fornecedores(db: Session = Depends(get_db)):
    fornecedores = db.query(models.Fornecedor).all()
    return fornecedores


# GET por ID: busca um fornecedor específico.
# Valida os limites do ID recebido na URL.
@app.get("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def buscar_fornecedor(
    fornecedor_id: Annotated[int, Path(gt=0, le=2147483647)],
    db: Session = Depends(get_db)
):
    # Procura o fornecedor pelo ID informado.
    fornecedor = db.query(models.Fornecedor).filter(
        models.Fornecedor.id == fornecedor_id
    ).first()

    # Retorna erro 404 quando o fornecedor não existe.
    if fornecedor is None:
        raise HTTPException(
            status_code=404,
            detail="Fornecedor não encontrado!"
        )

    return fornecedor


# PUT: atualiza os dados de um fornecedor.
@app.put("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def atualizar_fornecedor(
    fornecedor_id: Annotated[int, Path(gt=0, le=2147483647)],
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

    validar_cnpj_unico(dados_fornecedor.cnpj, db, fornecedor_id)

    fornecedor.nome = dados_fornecedor.nome
    fornecedor.cnpj = dados_fornecedor.cnpj
    fornecedor.ativo = dados_fornecedor.ativo

    try:
        db.commit()
    except IntegrityError:
        # Desfaz a tentativa antes de consultar novamente o CNPJ.
        db.rollback()
        validar_cnpj_unico(dados_fornecedor.cnpj, db, fornecedor_id)
        raise
    db.refresh(fornecedor)

    return fornecedor


# DELETE: inativa o fornecedor e mantém o registro no banco.
@app.delete("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse)
def excluir_fornecedor(
    fornecedor_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# Departamentos
# POST: cadastra um departamento.
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


# GET: lista todos os departamentos, incluindo os inativos.
@app.get("/departamentos", response_model=list[schemas.DepartamentoResponse])
def listar_departamentos(db: Session = Depends(get_db)):
    departamentos = db.query(models.Departamento).all()
    return departamentos


# GET por ID: busca um departamento específico.
@app.get("/departamentos/{departamento_id}", response_model=schemas.DepartamentoResponse)
def buscar_departamento(
    departamento_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# PUT: atualiza os dados de um departamento.
@app.put("/departamentos/{departamento_id}", response_model=schemas.DepartamentoResponse)
def atualizar_departamento(
    departamento_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# DELETE: inativa o departamento e mantém o registro no banco.
@app.delete("/departamentos/{departamento_id}", response_model=schemas.DepartamentoResponse)
def excluir_departamento(
    departamento_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# Naturezas financeiras
# POST: cadastra uma natureza financeira.
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


# GET: lista todas as naturezas financeiras, incluindo as inativas.
@app.get(
    "/naturezas-financeiras",
    response_model=list[schemas.NaturezaFinanceiraResponse]
)
def listar_naturezas_financeiras(db: Session = Depends(get_db)):
    naturezas_financeiras = db.query(models.NaturezaFinanceira).all()
    return naturezas_financeiras


# GET por ID: busca uma natureza financeira específica.
@app.get(
    "/naturezas-financeiras/{natureza_financeira_id}",
    response_model=schemas.NaturezaFinanceiraResponse
)
def buscar_natureza_financeira(
    natureza_financeira_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# PUT: atualiza os dados de uma natureza financeira.
@app.put(
    "/naturezas-financeiras/{natureza_financeira_id}",
    response_model=schemas.NaturezaFinanceiraResponse
)
def atualizar_natureza_financeira(
    natureza_financeira_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# DELETE: inativa a natureza financeira e mantém o registro no banco.
@app.delete(
    "/naturezas-financeiras/{natureza_financeira_id}",
    response_model=schemas.NaturezaFinanceiraResponse
)
def excluir_natureza_financeira(
    natureza_financeira_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# Rateios
# POST: cadastra um rateio.
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


# GET: lista todos os rateios, incluindo os inativos.
@app.get("/rateios", response_model=list[schemas.RateioResponse])
def listar_rateios(db: Session = Depends(get_db)):
    rateios = db.query(models.Rateio).all()
    return rateios


# GET por ID: busca um rateio específico.
@app.get("/rateios/{rateio_id}", response_model=schemas.RateioResponse)
def buscar_rateio(
    rateio_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# PUT: atualiza os dados de um rateio.
@app.put("/rateios/{rateio_id}", response_model=schemas.RateioResponse)
def atualizar_rateio(
    rateio_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# DELETE: inativa o rateio e mantém o registro no banco.
@app.delete("/rateios/{rateio_id}", response_model=schemas.RateioResponse)
def excluir_rateio(
    rateio_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# Despesas recorrentes
# POST: cadastra uma despesa após conferir os cadastros ligados a ela.
@app.post("/despesas-recorrentes", response_model=schemas.DespesaRecorrenteResponse)
def criar_despesa(
    despesa: schemas.DespesaRecorrenteCreate,
    db: Session = Depends(get_db)
):

    validar_relacionamentos_despesa(despesa, db)
    
    nova_despesa = models.DespesaRecorrente(**despesa.model_dump())

    db.add(nova_despesa)
    db.commit()
    db.refresh(nova_despesa)

    return nova_despesa


# GET: lista todas as despesas recorrentes, incluindo as inativas.
@app.get("/despesas-recorrentes", response_model=list[schemas.DespesaRecorrenteResponse])
def listar_despesas_recorrentes(
    db: Session = Depends(get_db)
):
    despesas = db.query(models.DespesaRecorrente).all()

    return despesas


# GET por ID: busca uma despesa recorrente específica.
@app.get("/despesas-recorrentes/{despesa_id}", response_model=schemas.DespesaRecorrenteResponse)
def buscar_despesa_recorrente(
    despesa_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# PUT: atualiza a despesa e confere novamente os cadastros ligados a ela.
@app.put("/despesas-recorrentes/{despesa_id}", response_model=schemas.DespesaRecorrenteResponse)
def atualizar_despesa_recorrente(
    despesa_id: Annotated[int, Path(gt=0, le=2147483647)],
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

    validar_relacionamentos_despesa(dados_despesa, db)

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


# DELETE: inativa a despesa recorrente e mantém o registro no banco.
@app.delete("/despesas-recorrentes/{despesa_id}", response_model=schemas.DespesaRecorrenteResponse)
def excluir_despesa_recorrente(
    despesa_id: Annotated[int, Path(gt=0, le=2147483647)],
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


# Lançamentos de despesas
# POST: cadastra um lançamento ligado a uma despesa recorrente.
@app.post(
    "/lancamentos-despesa",
    response_model=schemas.LancamentoDespesaResponse
)
def criar_lancamento_despesa(
    dados_lancamento: schemas.LancamentoDespesaCreate,
    db: Session = Depends(get_db)
):
    # Usa o primeiro dia do mês de recebimento para representar o mês de referência.
    mes_referencia = dados_lancamento.data_recebimento.replace(day=1)

    # Confere se a despesa existe antes de vincular o lançamento a ela.
    despesa = db.query(models.DespesaRecorrente).filter(
        models.DespesaRecorrente.id == dados_lancamento.despesa_recorrente_id
    ).first()

    if despesa is None:
        raise HTTPException(
            status_code=404,
            detail="Despesa não encontrada!"
        )
    
    novo_lancamento = models.LancamentoDespesa(
        **dados_lancamento.model_dump(),
        mes_referencia=mes_referencia
    )

    db.add(novo_lancamento)
    db.commit()
    db.refresh(novo_lancamento)

    return novo_lancamento


# GET: lista todos os lançamentos, incluindo os inativos.
@app.get("/lancamentos-despesa", response_model=list[schemas.LancamentoDespesaResponse])
def listar_lancamentos_despesa(
    db: Session = Depends(get_db)
):
    lancamentos = db.query(models.LancamentoDespesa).all()

    return lancamentos


# GET por ID: busca um lançamento específico.
@app.get("/lancamentos-despesa/{lancamento_id}", response_model=schemas.LancamentoDespesaResponse)
def buscar_lancamento_id(
    lancamento_id: Annotated[int, Path(gt=0, le=2147483647)],
    db: Session = Depends(get_db)
):

    lancamento = db.query(models.LancamentoDespesa).filter(
        models.LancamentoDespesa.id == lancamento_id
    ).first()

    if lancamento is None:
        raise HTTPException(
            status_code=404,
            detail="Lançamento não encontrado!"
        )

    return lancamento


# PUT: atualiza os dados de um lançamento.
@app.put(
    "/lancamentos-despesa/{lancamento_id}",
    response_model=schemas.LancamentoDespesaResponse
)
def atualizar_lancamento_despesa(
    lancamento_id: Annotated[int, Path(gt=0, le=2147483647)],
    dados_lancamento: schemas.LancamentoDespesaCreate,
    db: Session = Depends(get_db)
):
    lancamento = db.query(models.LancamentoDespesa).filter(
        models.LancamentoDespesa.id == lancamento_id
    ).first()

    if lancamento is None:
        raise HTTPException(
            status_code=404,
            detail="Lançamento não encontrado!"
        )

    despesa = db.query(models.DespesaRecorrente).filter(
        models.DespesaRecorrente.id == dados_lancamento.despesa_recorrente_id
    ).first()

    if despesa is None:
        raise HTTPException(
            status_code=404,
            detail="Despesa não encontrada!"
        )

    lancamento.despesa_recorrente_id = dados_lancamento.despesa_recorrente_id
    lancamento.valor_recebido = dados_lancamento.valor_recebido
    lancamento.data_recebimento = dados_lancamento.data_recebimento
    # Recalcula o mês de referência para acompanhar a data de recebimento.
    lancamento.mes_referencia = dados_lancamento.data_recebimento.replace(day=1)
    lancamento.observacao = dados_lancamento.observacao
    lancamento.nota_pendente = dados_lancamento.nota_pendente
    lancamento.ativo = dados_lancamento.ativo

    db.commit()
    db.refresh(lancamento)

    return lancamento


# DELETE: inativa o lançamento e mantém o histórico no banco.
@app.delete(
    "/lancamentos-despesa/{lancamento_id}",
    response_model=schemas.LancamentoDespesaResponse
)
def excluir_lancamento_despesa(
    lancamento_id: Annotated[int, Path(gt=0, le=2147483647)],
    db: Session = Depends(get_db)
):
    # Busca o lançamento que será inativado.
    lancamento = db.query(models.LancamentoDespesa).filter(
        models.LancamentoDespesa.id == lancamento_id
    ).first()

    if lancamento is None:
        raise HTTPException(
            status_code=404,
            detail="Lançamento não encontrado!"
        )

    # A exclusão é lógica: o registro continua salvo, mas fica inativo.
    lancamento.ativo = False

    db.commit()
    db.refresh(lancamento)

    return lancamento
