# Atualização de bancos existentes. Executar com: python -m backend.migracoes.

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import MetaData, inspect, select, text

from backend import models
from backend.database import Base, engine


def migrar_vencimento_e_rateios(conexao):
    if conexao.dialect.name != "postgresql":
        raise ValueError("Esta migração foi preparada para PostgreSQL.")

    # create_all cria tabelas novas, mas não acrescenta colunas às já existentes.
    Base.metadata.create_all(conexao)
    colunas = {item["name"] for item in inspect(conexao).get_columns("despesas_recorrentes")}
    if "dia_vencimento" not in colunas:
        conexao.execute(text(
            "ALTER TABLE despesas_recorrentes ADD COLUMN dia_vencimento INTEGER "
            "CONSTRAINT ck_despesa_vencimento CHECK (dia_vencimento BETWEEN 1 AND 31)"
        ))

    if "rateio_id" in colunas:
        conexao.execute(text("""
            INSERT INTO despesa_rateios (despesa_recorrente_id, rateio_id, percentual)
            SELECT d.id, d.rateio_id, 100
            FROM despesas_recorrentes d
            WHERE NOT EXISTS (
                SELECT 1 FROM despesa_rateios r WHERE r.despesa_recorrente_id = d.id
            )
        """))
        sem_rateio = conexao.execute(text("""
            SELECT COUNT(*) FROM despesas_recorrentes d
            WHERE NOT EXISTS (
                SELECT 1 FROM despesa_rateios r WHERE r.despesa_recorrente_id = d.id
            )
        """)).scalar_one()
        if sem_rateio:
            raise ValueError("Há despesas sem rateio. A migração foi cancelada.")
        conexao.execute(text("ALTER TABLE despesas_recorrentes DROP COLUMN rateio_id"))


def salvar_backup(conexao):
    metadados = MetaData()
    metadados.reflect(bind=conexao)
    dados = {
        tabela.name: [dict(linha) for linha in conexao.execute(select(tabela)).mappings()]
        for tabela in metadados.sorted_tables
    }
    pasta = Path(__file__).resolve().parents[1] / "docs" / "backups"
    pasta.mkdir(parents=True, exist_ok=True)
    instante = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    arquivo = pasta / f"antes-vencimento-rateios-{instante}.json"
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    return arquivo


if __name__ == "__main__":
    with engine.begin() as conexao:
        backup = salvar_backup(conexao)
        migrar_vencimento_e_rateios(conexao)
    print(f"Migração concluída. Backup local: {backup}")
