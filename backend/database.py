# Configuração da conexão e das sessões do banco de dados.
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Carrega as configurações do arquivo .env.
load_dotenv()

# Os dados de conexão ficam nas variáveis de ambiente.
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Monta o endereço de conexão com o PostgreSQL usando o driver psycopg.
DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# O engine gerencia as conexões com o banco.
engine = create_engine(DATABASE_URL)

# Cada requisição usa uma sessão, e as rotas confirmam as alterações com commit().
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Classe base usada pelos models para definir as tabelas.
class Base(DeclarativeBase):
    pass
