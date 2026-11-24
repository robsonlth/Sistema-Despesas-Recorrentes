import { prepararAcompanhamento } from './acompanhamento.js'
import { normalizarTexto } from './despesas.js'

export function prepararLancamentos(dados, filtros, hoje) {
  const { mes, busca, departamento, natureza, situacao, etapa } = filtros
  const acompanhamento = prepararAcompanhamento(dados, mes, '', hoje)
  const despesasPorId = new Map(
    acompanhamento.despesas.map((despesa) => [despesa.id, despesa]),
  )
  const termo = normalizarTexto(busca)

  function correspondeClassificacao(despesa) {
    return (!departamento || despesa?.departamento_id === Number(departamento))
      && (!natureza || despesa?.natureza_financeira_id === Number(natureza))
  }

  function correspondeBusca(despesa, lancamento) {
    return [despesa?.descricao, despesa?.fornecedor, lancamento?.observacao, lancamento?.id]
      .some((texto) => normalizarTexto(String(texto ?? '')).includes(termo))
  }

  const exibirPendentes = etapa === 'todos' || etapa === 'pendentes'
  const exibirRegistros = etapa !== 'pendentes'

  // O resumo da API considera apenas lançamentos ativos, inclusive os de valor zero.
  const pendentes = exibirPendentes && situacao !== 'inativos'
    ? acompanhamento.pendentes.filter((despesa) =>
      correspondeClassificacao(despesa) && correspondeBusca(despesa),
    )
    : []

  // O histórico continua visível mesmo se a despesa estiver inativa ou fora da vigência.
  const registros = exibirRegistros ? dados.lancamentos.map((lancamento) => ({
    ...lancamento,
    despesa: despesasPorId.get(lancamento.despesa_recorrente_id),
  })).filter((lancamento) => {
    const correspondeSituacao = situacao === 'todos'
      || lancamento.ativo === (situacao === 'ativos')
    const correspondeEtapa = etapa === 'todos'
      || (etapa === 'nota-pendente' && lancamento.nota_pendente)
      || (etapa === 'sem-nota-pendente' && !lancamento.nota_pendente)
    return lancamento.mes_referencia.slice(0, 7) === mes
      && correspondeSituacao && correspondeEtapa
      && correspondeClassificacao(lancamento.despesa)
      && correspondeBusca(lancamento.despesa, lancamento)
  }).sort((a, b) =>
    b.data_recebimento.localeCompare(a.data_recebimento) || b.id - a.id,
  ) : []

  return {
    despesas: acompanhamento.despesas,
    pendentes,
    registros,
    exibirPendentes,
    exibirRegistros,
  }
}
