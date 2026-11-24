# Schemas: definem e validam os dados que entram e saem da API.
# Base reúne os campos comuns; Create valida o cadastro e a atualização.
# Response define a resposta da API, incluindo o ID salvo no banco.
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import date
from decimal import Decimal
from typing import Literal

from backend.validacoes import validar_cnpj, validar_nome_cadastro


# Fornecedores
class FornecedorBase(BaseModel):
    nome: str
    cnpj: str | None = None
    ativo: bool = True


# As regras de entrada ficam no Create para não impedir a leitura de dados antigos.
class FornecedorCreate(FornecedorBase):
    # Rejeita campos que não fazem parte do cadastro.
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


# Departamentos
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


# Naturezas financeiras
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


# Rateios
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


# Parcelas de rateio de cada despesa
class DespesaRateioBase(BaseModel):
    rateio_id: int
    percentual: Decimal | None = None
    valor: Decimal | None = None


class DespesaRateioCreate(DespesaRateioBase):
    model_config = ConfigDict(extra="forbid")

    rateio_id: int = Field(strict=True, gt=0, le=2147483647)
    percentual: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2, allow_inf_nan=False
    )
    valor: Decimal | None = Field(
        default=None, ge=0, max_digits=10, decimal_places=2, allow_inf_nan=False
    )

    @model_validator(mode="after")
    def validar_medida(self):
        if (self.percentual is None) == (self.valor is None):
            raise ValueError("Informe a porcentagem ou o valor de cada rateio, nunca os dois.")
        return self


class DespesaRateioResponse(DespesaRateioBase):
    model_config = ConfigDict(from_attributes=True)


# Despesas recorrentes
class DespesaRecorrenteBase(BaseModel):
    fornecedor_id: int
    departamento_id: int
    natureza_financeira_id: int
    rateios: list[DespesaRateioResponse]
    dia_vencimento: int | None = None
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
    rateios: list[DespesaRateioCreate] = Field(min_length=1)
    dia_vencimento: int | None = Field(default=None, strict=True, ge=1, le=31)

    # Numeric(10, 2) permite oito dígitos inteiros e duas casas decimais.
    # Zero é permitido; valores negativos e não finitos são rejeitados.
    valor_estimado: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        allow_inf_nan=False
    )

    @model_validator(mode="after")
    def validar_rateios(self):
        ids = [item.rateio_id for item in self.rateios]
        if len(ids) != len(set(ids)):
            raise ValueError("Não repita o mesmo rateio na despesa.")

        por_percentual = [item.percentual is not None for item in self.rateios]
        if all(por_percentual):
            if sum(item.percentual for item in self.rateios) != Decimal("100"):
                raise ValueError("As porcentagens dos rateios devem somar 100%.")
        elif any(por_percentual):
            raise ValueError("Use somente porcentagens ou somente valores nos rateios.")
        else:
            if self.valor_estimado is None:
                raise ValueError("Informe o valor estimado da despesa para ratear em reais.")
            if sum(item.valor for item in self.rateios) != self.valor_estimado:
                raise ValueError("A soma dos rateios deve ser igual ao valor estimado da despesa.")
        return self

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


# Lançamentos de despesas
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


# Resumo mensal
class ResumoMensalDespesaResponse(BaseModel):
    despesa_recorrente_id: int
    descricao: str
    # O total pode ultrapassar o limite de valor de um lançamento individual.
    total_recebido: Decimal
    # Zero identifica uma despesa que ainda não tem lançamento ativo no mês.
    quantidade_lancamentos: int

    model_config = ConfigDict(from_attributes=True)


# Análise por competência
class AnaliseDespesaResponse(BaseModel):
    despesa_recorrente_id: int
    descricao: str
    fornecedor: str
    departamento: str
    valor_estimado: Decimal
    origem_estimativa: Literal["cadastro", "media_historica"]
    meses_historico: int = Field(ge=0, le=3)
    valor_realizado: Decimal
    diferenca: Decimal
    variacao_percentual: Decimal | None
    quantidade_lancamentos: int
    quantidade_notas_pendentes: int
    # A lista permite mostrar, por exemplo, excesso e nota pendente juntos.
    situacoes: list[Literal[
        "sem_lancamento", "dentro_do_estimado", "acima_do_estimado", "nota_pendente"
    ]]


class AnaliseCompetenciaResponse(BaseModel):
    competencia: date
    total_estimado: Decimal
    total_realizado: Decimal
    diferenca: Decimal
    variacao_percentual: Decimal | None
    despesas_pendentes: int
    notas_pendentes: int
    despesas_excluidas: int
    despesas: list[AnaliseDespesaResponse]
