from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


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