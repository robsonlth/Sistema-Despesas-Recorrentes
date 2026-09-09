from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal

class FornecedorBase(BaseModel):
    nome: str
    cnpj: str | None = None
    ativo: bool = True


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorResponse(FornecedorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DepartamentoBase(BaseModel):
    nome: str
    ativo: bool = True


class DepartamentoCreate(DepartamentoBase):
    pass


class DepartamentoResponse(DepartamentoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class NaturezaFinanceiraBase(BaseModel):
    nome: str
    ativo: bool = True


class NaturezaFinanceiraCreate(NaturezaFinanceiraBase):
    pass


class NaturezaFinanceiraResponse(NaturezaFinanceiraBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class RateioBase(BaseModel):
    nome: str
    ativo: bool = True


class RateioCreate(RateioBase):
    pass


class RateioResponse(RateioBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DespesaRecorrenteBase(BaseModel):
    fornecedor_id: int
    departamento_id: int
    natureza_financeira_id: int
    rateio_id: int
    descricao: str
    data_inicio_vigencia: date
    data_fim_vigencia: date | None = None
    valor_estimado: Decimal | None = None
    ativo: bool = True


class DespesaRecorrenteCreate(DespesaRecorrenteBase):
    pass


class DespesaRecorrenteResponse(DespesaRecorrenteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LancamentoDespesaBase(BaseModel):
    despesa_recorrente_id: int
    valor_recebido: Decimal
    data_recebimento: date
    observacao: str | None = None
    nota_pendente: bool = False
    ativo: bool = True


class LancamentoDespesaCreate(LancamentoDespesaBase):
    pass


class LancamentoDespesaResponse(LancamentoDespesaBase):
    id: int
    mes_referencia: date

    model_config = ConfigDict(from_attributes=True)