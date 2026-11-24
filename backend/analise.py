# Cálculos da análise de despesas por competência.

from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def calcular_variacao(estimado: Decimal | None, realizado: Decimal) -> Decimal | None:
    if estimado is None or estimado == 0:
        return None
    return ((realizado - estimado) / estimado * 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calcular_analise(mes_referencia: date, resumos, historico=()):
    # A consulta do histórico já soma os lançamentos por despesa e mês.
    totais_por_despesa = {}
    for registro in historico:
        totais_por_despesa.setdefault(registro.despesa_recorrente_id, []).append(
            registro.total_recebido
        )

    total_estimado = Decimal("0.00")
    total_realizado = Decimal("0.00")
    despesas_pendentes = 0
    notas_pendentes = 0
    despesas_excluidas = 0
    despesas = []

    for resumo in resumos:
        estimado = resumo.valor_estimado
        origem_estimativa = "cadastro"
        meses_historico = 0
        # A estimativa cadastrada tem prioridade, inclusive quando o valor é zero.
        if estimado is None:
            totais_mensais = totais_por_despesa.get(resumo.despesa_recorrente_id, [])
            # Sem estimativa e sem histórico, a despesa fica fora da análise.
            if not totais_mensais:
                despesas_excluidas += 1
                continue
            meses_historico = len(totais_mensais)
            # A média considera apenas os meses com lançamentos ativos.
            estimado = (sum(totais_mensais, Decimal("0.00")) / meses_historico).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            origem_estimativa = "media_historica"

        realizado = resumo.total_recebido
        diferenca = realizado - estimado
        situacoes = []

        # Um lançamento de valor zero também conta como realizado.
        if resumo.quantidade_lancamentos == 0:
            despesas_pendentes += 1
            situacoes.append("sem_lancamento")
        else:
            situacoes.append("acima_do_estimado" if diferenca > 0 else "dentro_do_estimado")

        if resumo.quantidade_notas_pendentes > 0:
            situacoes.append("nota_pendente")
        notas_pendentes += resumo.quantidade_notas_pendentes

        total_estimado += estimado
        total_realizado += realizado

        despesas.append({
            "despesa_recorrente_id": resumo.despesa_recorrente_id,
            "descricao": resumo.descricao,
            "fornecedor": resumo.fornecedor,
            "departamento": resumo.departamento,
            "valor_estimado": estimado,
            "origem_estimativa": origem_estimativa,
            "meses_historico": meses_historico,
            "valor_realizado": realizado,
            "diferenca": diferenca,
            "variacao_percentual": calcular_variacao(estimado, realizado),
            "quantidade_lancamentos": resumo.quantidade_lancamentos,
            "quantidade_notas_pendentes": resumo.quantidade_notas_pendentes,
            "situacoes": situacoes,
        })

    return {
        "competencia": mes_referencia.replace(day=1),
        "total_estimado": total_estimado,
        "total_realizado": total_realizado,
        "diferenca": total_realizado - total_estimado,
        "variacao_percentual": calcular_variacao(total_estimado, total_realizado),
        "despesas_pendentes": despesas_pendentes,
        "notas_pendentes": notas_pendentes,
        # A contagem informa quantas despesas ficaram fora da análise.
        "despesas_excluidas": despesas_excluidas,
        "despesas": despesas,
    }
