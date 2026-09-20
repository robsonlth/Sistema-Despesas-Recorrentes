# Configuração da conexão e das sessões do banco de dados.
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Carrega as configurações do arquivo .env.
load_dotenv()

# Lê os dados de acesso sem colocar a senha diretamente no código.
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

# Cria sessões para consultar, cadastrar e atualizar os registros.
# As rotas confirmam as alterações com commit().
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Classe base usada pelos models para definir as tabelas.
class Base(DeclarativeBase):
    pass
