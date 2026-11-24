# Models: definem as tabelas e os relacionamentos do banco de dados.
from sqlalchemy import Boolean, String, Date, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from backend.database import Base
from datetime import date


# Fornecedores
class Fornecedor(Base):
    __tablename__ = "fornecedores"

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


# Departamentos
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


# Naturezas financeiras
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


# Rateios
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


# Despesas recorrentes
class DespesaRecorrente(Base):
    __tablename__ = "despesas_recorrentes"
    __table_args__ = (
        CheckConstraint("dia_vencimento BETWEEN 1 AND 31", name="ck_despesa_vencimento"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

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

    rateios: Mapped[list["DespesaRateio"]] = relationship(
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DespesaRateio.rateio_id"
    )

    dia_vencimento: Mapped[int | None] = mapped_column(nullable=True)

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


# Parcelas de rateio de cada despesa
class DespesaRateio(Base):
    __tablename__ = "despesa_rateios"
    __table_args__ = (
        CheckConstraint(
            "(percentual IS NOT NULL AND valor IS NULL) OR "
            "(percentual IS NULL AND valor IS NOT NULL)",
            name="ck_rateio_medida"
        ),
        CheckConstraint("percentual BETWEEN 0 AND 100", name="ck_rateio_percentual"),
        CheckConstraint("valor >= 0 AND valor < 100000000", name="ck_rateio_valor"),
    )

    # A chave composta impede repetir o mesmo rateio em uma despesa.
    despesa_recorrente_id: Mapped[int] = mapped_column(
        ForeignKey("despesas_recorrentes.id", ondelete="CASCADE"), primary_key=True
    )
    rateio_id: Mapped[int] = mapped_column(ForeignKey("rateios.id"), primary_key=True)
    percentual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)


# Lançamentos de despesas
class LancamentoDespesa(Base):
    __tablename__ = "lancamentos_despesa"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

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
