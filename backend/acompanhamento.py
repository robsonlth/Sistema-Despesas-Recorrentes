# Consultas usadas no acompanhamento mensal e na análise de despesas.

from calendar import monthrange
from datetime import date

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from backend import models


def consultar_resumo_mensal(db: Session, mes_referencia: date):
    # Inclui despesas previstas e despesas com lançamentos fora da vigência.
    mes_referencia = mes_referencia.replace(day=1)
    ultimo_dia = monthrange(mes_referencia.year, mes_referencia.month)[1]
    fim_do_mes = mes_referencia.replace(day=ultimo_dia)

    # Os rateios ficam fora da consulta para não duplicar os valores dos lançamentos.
    consulta = db.query(
        models.DespesaRecorrente.id.label("despesa_recorrente_id"),
        models.DespesaRecorrente.descricao,
        models.DespesaRecorrente.valor_estimado,
        models.Fornecedor.nome.label("fornecedor"),
        models.Departamento.nome.label("departamento"),
        func.coalesce(func.sum(models.LancamentoDespesa.valor_recebido), 0).label("total_recebido"),
        func.count(models.LancamentoDespesa.id).label("quantidade_lancamentos"),
        func.count(case(
            (models.LancamentoDespesa.nota_pendente.is_(True), models.LancamentoDespesa.id)
        )).label("quantidade_notas_pendentes"),
    ).join(
        models.Fornecedor,
        models.Fornecedor.id == models.DespesaRecorrente.fornecedor_id,
    ).join(
        models.Departamento,
        models.Departamento.id == models.DespesaRecorrente.departamento_id,
    ).outerjoin(
        models.LancamentoDespesa,
        # O filtro no JOIN mantém as despesas sem lançamento ativo no mês.
        and_(
            models.LancamentoDespesa.despesa_recorrente_id == models.DespesaRecorrente.id,
            models.LancamentoDespesa.ativo.is_(True),
            models.LancamentoDespesa.mes_referencia == mes_referencia,
        ),
    )

    consulta = consulta.filter(
        or_(
            and_(
                models.DespesaRecorrente.ativo.is_(True),
                models.DespesaRecorrente.data_inicio_vigencia <= fim_do_mes,
                or_(
                    models.DespesaRecorrente.data_fim_vigencia.is_(None),
                    models.DespesaRecorrente.data_fim_vigencia >= mes_referencia,
                ),
            ),
            # Preserva lançamentos de despesas inativas ou fora da vigência.
            models.LancamentoDespesa.id.is_not(None),
        )
    )

    return consulta.group_by(
        models.DespesaRecorrente.id,
        models.DespesaRecorrente.descricao,
        models.DespesaRecorrente.valor_estimado,
        models.Fornecedor.nome,
        models.Departamento.nome,
    ).order_by(models.DespesaRecorrente.id).all()


def consultar_historico_mensal(db: Session, mes_referencia: date, despesas_ids: list[int]):
    # Soma os lançamentos ativos por despesa e mês nos três meses anteriores.
    if not despesas_ids:
        return []

    mes_referencia = mes_referencia.replace(day=1)
    indice_mes = (mes_referencia.year - 1) * 12 + mes_referencia.month - 1
    if indice_mes == 0:
        return []
    # A contagem em meses permite voltar três meses mesmo na virada do ano.
    indice_inicio = max(0, indice_mes - 3)
    inicio = date(indice_inicio // 12 + 1, indice_inicio % 12 + 1, 1)

    return db.query(
        models.LancamentoDespesa.despesa_recorrente_id,
        models.LancamentoDespesa.mes_referencia,
        func.sum(models.LancamentoDespesa.valor_recebido).label("total_recebido"),
    ).filter(
        models.LancamentoDespesa.despesa_recorrente_id.in_(despesas_ids),
        models.LancamentoDespesa.ativo.is_(True),
        models.LancamentoDespesa.mes_referencia >= inicio,
        models.LancamentoDespesa.mes_referencia < mes_referencia,
    ).group_by(
        models.LancamentoDespesa.despesa_recorrente_id,
        models.LancamentoDespesa.mes_referencia,
    ).order_by(
        models.LancamentoDespesa.despesa_recorrente_id,
        models.LancamentoDespesa.mes_referencia,
    ).all()
