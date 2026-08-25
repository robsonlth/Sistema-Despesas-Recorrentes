from pydantic import BaseModel, ConfigDict


class FornecedorBase(BaseModel):
    nome: str
    cnpj: str | None = None
    ativo: bool = True


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorResponse(FornecedorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
