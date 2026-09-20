# Models: descrevem as tabelas e as colunas do banco de dados.
# Cada objeto dessas classes representa um registro da tabela.
from sqlalchemy import Boolean, String, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from backend.database import Base
from datetime import date


# Fornecedores: guarda o nome, o CNPJ e a situação do cadastro.
class Fornecedor(Base):
    __tablename__ = "fornecedores"

    # Chave primária: identifica cada registro da tabela.
    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    # O CNPJ é opcional, mas não pode se repetir quando for informado.
    cnpj: Mapped[str | None] = mapped_column(
        String(14),
        unique=True,
        nullable=True
    )

    # False indica que o cadastro foi inativado, sem apagar o registro.
    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


# Departamentos: guarda os departamentos usados nas despesas.
class Departamento(Base):
    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


# Naturezas financeiras: guarda as classificações das despesas.
class NaturezaFinanceira(Base):
    __tablename__ = "naturezas_financeiras"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


# Rateios: guarda os cadastros de rateio usados nas despesas.
class Rateio(Base):
    __tablename__ = "rateios"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


# Despesas recorrentes: guarda as despesas previstas e seus vínculos.
class DespesaRecorrente(Base):
    __tablename__ = "despesas_recorrentes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    # As chaves estrangeiras ligam a despesa aos outros cadastros.
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"),
        nullable=False
    )

    departamento_id: Mapped[int] = mapped_column(
        ForeignKey("departamentos.id"),
        nullable=False
    )

    natureza_financeira_id: Mapped[int] = mapped_column(
        ForeignKey("naturezas_financeiras.id"),
        nullable=False
    )

    rateio_id: Mapped[int] = mapped_column(
        ForeignKey("rateios.id"),
        nullable=False
    )

    descricao: Mapped[str] = mapped_column(
        String(350),
        nullable=False
    )

    # Período de vigência da despesa; a data final é opcional.
    data_inicio_vigencia: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    data_fim_vigencia: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    # Numeric e Decimal representam valores monetários com precisão decimal.
    valor_estimado: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


# Lançamentos: guarda os valores e as datas recebidos para cada despesa.
class LancamentoDespesa(Base):
    __tablename__ = "lancamentos_despesa"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    # Liga o lançamento à despesa recorrente cadastrada.
    despesa_recorrente_id: Mapped[int] = mapped_column(
        ForeignKey("despesas_recorrentes.id"),
        nullable=False
    )

    # A API preenche este campo com o primeiro dia do mês de recebimento.
    mes_referencia: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    valor_recebido: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    data_recebimento: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    observacao: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True
    )

    # Indica se a nota do lançamento está pendente.
    nota_pendente: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
