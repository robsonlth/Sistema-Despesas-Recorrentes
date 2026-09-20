# Schemas: definem e validam os dados que entram e saem da API.
# Base reúne os campos comuns; Create valida o cadastro e a atualização.
# Response define a resposta da API, incluindo o ID salvo no banco.
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import date
from decimal import Decimal

from backend.validacoes import validar_cnpj, validar_nome_cadastro


# Dados de fornecedores.
class FornecedorBase(BaseModel):
    nome: str
    cnpj: str | None = None
    ativo: bool = True


# As regras de entrada ficam no Create para não impedir a leitura de dados antigos.
class FornecedorCreate(FornecedorBase):
    # Rejeita campos desconhecidos, como um nome de campo digitado errado.
    model_config = ConfigDict(extra="forbid")

    # Remove os espaços das pontas e valida o tamanho do nome.
    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        nome_limpo = nome.strip()

        if len(nome_limpo) > 150 or len(nome_limpo) == 0:
            raise ValueError("O nome deve ter entre 1 e 150 caracteres.")

        return nome_limpo

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj_fornecedor(cls, cnpj: str | None) -> str | None:
        return validar_cnpj(cnpj)


class FornecedorResponse(FornecedorBase):
    id: int

    # Permite montar a resposta usando os atributos do objeto do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)


# Dados de departamentos.
class DepartamentoBase(BaseModel):
    nome: str
    ativo: bool = True


class DepartamentoCreate(DepartamentoBase):
    model_config = ConfigDict(extra="forbid")

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        return validar_nome_cadastro(nome)


class DepartamentoResponse(DepartamentoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Dados de naturezas financeiras.
class NaturezaFinanceiraBase(BaseModel):
    nome: str
    ativo: bool = True


class NaturezaFinanceiraCreate(NaturezaFinanceiraBase):
    model_config = ConfigDict(extra="forbid")

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        return validar_nome_cadastro(nome)


class NaturezaFinanceiraResponse(NaturezaFinanceiraBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Dados de rateios.
class RateioBase(BaseModel):
    nome: str
    ativo: bool = True


class RateioCreate(RateioBase):
    model_config = ConfigDict(extra="forbid")

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str) -> str:
        return validar_nome_cadastro(nome)


class RateioResponse(RateioBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Dados de despesas recorrentes e dos cadastros ligados a elas.
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
    model_config = ConfigDict(extra="forbid")

    # Os IDs devem ser inteiros positivos dentro do limite da coluna Integer.
    fornecedor_id: int = Field(strict=True, gt=0, le=2147483647)
    departamento_id: int = Field(strict=True, gt=0, le=2147483647)
    natureza_financeira_id: int = Field(strict=True, gt=0, le=2147483647)
    rateio_id: int = Field(strict=True, gt=0, le=2147483647)

    # Numeric(10, 2) permite oito dígitos inteiros e duas casas decimais.
    # Zero é permitido; valores negativos e não finitos são rejeitados.
    valor_estimado: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        allow_inf_nan=False
    )

    @field_validator("descricao")
    @classmethod
    def validar_descricao(cls, descricao: str) -> str:
        descricao_limpa = descricao.strip()

        if len(descricao_limpa) == 0 or len(descricao_limpa) > 350:
            raise ValueError("A descrição deve ter entre 1 e 350 caracteres.")

        return descricao_limpa

    # Confere se a data final da vigência é igual ou posterior à data inicial.
    @model_validator(mode="after")
    def validar_vigencia(self):
        if (
            self.data_fim_vigencia is not None
            and self.data_fim_vigencia < self.data_inicio_vigencia
        ):
            raise ValueError("A data final da vigência não pode ser anterior à data inicial.")

        return self


class DespesaRecorrenteResponse(DespesaRecorrenteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Dados de lançamentos de despesas.
class LancamentoDespesaBase(BaseModel):
    despesa_recorrente_id: int
    valor_recebido: Decimal
    data_recebimento: date
    observacao: str | None = None
    nota_pendente: bool = False
    ativo: bool = True


class LancamentoDespesaCreate(LancamentoDespesaBase):
    model_config = ConfigDict(extra="forbid")

    despesa_recorrente_id: int = Field(strict=True, gt=0, le=2147483647)
    valor_recebido: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
        allow_inf_nan=False
    )

    @field_validator("observacao")
    @classmethod
    def validar_observacao(cls, observacao: str | None) -> str | None:
        if observacao is None:
            return None

        observacao_limpa = observacao.strip()

        if len(observacao_limpa) > 320:
            raise ValueError("A observação deve ter no máximo 320 caracteres.")

        # Uma observação vazia é tratada como não informada.
        if len(observacao_limpa) == 0:
            return None

        return observacao_limpa


class LancamentoDespesaResponse(LancamentoDespesaBase):
    id: int
    # O mês de referência é calculado pela API e aparece apenas na resposta.
    mes_referencia: date

    model_config = ConfigDict(from_attributes=True)
