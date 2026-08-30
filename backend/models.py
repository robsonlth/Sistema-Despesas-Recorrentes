from sqlalchemy import Boolean, String, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from backend.database import Base
from datetime import date


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    cnpj: Mapped[str | None] = mapped_column(
        String(14),
        unique=True,
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


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


class DespesaRecorrente(Base):
    __tablename__ = "despesas_recorrentes"

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

    rateio_id: Mapped[int] = mapped_column(
        ForeignKey("rateios.id"),
        nullable=False
    )

    descricao: Mapped[str] = mapped_column(
        String(350),
        nullable=False
    )

    data_inicio_vigencia: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    data_fim_vigencia: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    valor_estimado: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )