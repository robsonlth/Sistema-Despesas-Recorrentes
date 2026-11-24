import { relacionarDespesas } from './despesas.js'
import { calcularVencimento, compararVencimentos } from './vencimentos.js'
import { dataLocalHoje } from './formatacao.js'

function valorEmCentavos(valor) {
  const [inteiros, decimais = ''] = String(valor).split('.')
  return Number(inteiros) * 100 + Number(decimais.padEnd(2, '0'))
}

export function prepararAcompanhamento(dados, mes, departamentoId = '', hoje = dataLocalHoje()) {
  const resumos = new Map(
    dados.resumo.map((item) => [item.despesa_recorrente_id, item]),
  )
  const despesas = relacionarDespesas(dados)
  const correspondeDepartamento = (despesa) =>
    !departamentoId || despesa.departamento_id === Number(departamentoId)
  // Despesas inativas ou fora da vigência não entram no progresso.
  const previstas = despesas.filter(
    (despesa) =>
      despesa.ativo &&
      correspondeDepartamento(despesa) &&
      despesa.data_inicio_vigencia.slice(0, 7) <= mes &&
      (!despesa.data_fim_vigencia ||
        despesa.data_fim_vigencia.slice(0, 7) >= mes),
  )
  // Usa a quantidade de lançamentos, pois um lançamento com valor zero também conta.
  const pendentes = previstas.filter(
    (despesa) => resumos.get(despesa.id)?.quantidade_lancamentos === 0,
  ).map((despesa) => ({
    ...despesa,
    vencimento: calcularVencimento(despesa.dia_vencimento, mes, hoje),
  })).sort(compararVencimentos)
  const lancadas = previstas.filter(
    (despesa) => resumos.get(despesa.id)?.quantidade_lancamentos > 0,
  ).length

  const lancamentosDoMes = dados.lancamentos.filter((lancamento) =>
    lancamento.ativo && lancamento.mes_referencia?.slice(0, 7) === mes,
  )
  const lancamentosPorDespesa = new Map()
  // Mantém os lançamentos de cada despesa para a consulta das justificativas.
  for (const lancamento of lancamentosDoMes) {
    const despesaId = lancamento.despesa_recorrente_id
    if (!lancamentosPorDespesa.has(despesaId)) {
      lancamentosPorDespesa.set(despesaId, [])
    }
    lancamentosPorDespesa.get(despesaId).push(lancamento)
  }
  for (const lancamentos of lancamentosPorDespesa.values()) {
    lancamentos.sort((a, b) =>
      b.data_recebimento.localeCompare(a.data_recebimento) || b.id - a.id,
    )
  }

  const acimaDoEstimado = []
  let totalExcedenteCentavos = 0
  // O resumo já soma os lançamentos ativos do mês, inclusive de despesas inativadas.
  for (const despesa of despesas) {
    if (!correspondeDepartamento(despesa)
      || despesa.valor_estimado == null || despesa.valor_estimado === '') continue
    const resumo = resumos.get(despesa.id)
    if (!resumo?.quantidade_lancamentos) continue

    // Calcula a diferença em centavos para evitar imprecisão com decimais.
    const excedente = valorEmCentavos(resumo.total_recebido)
      - valorEmCentavos(despesa.valor_estimado)
    if (excedente > 0) {
      totalExcedenteCentavos += excedente
      acimaDoEstimado.push({
        ...despesa,
        total_recebido: resumo.total_recebido,
        valor_excedente: excedente / 100,
        lancamentos: lancamentosPorDespesa.get(despesa.id) ?? [],
      })
    }
  }
  acimaDoEstimado.sort((a, b) => b.valor_excedente - a.valor_excedente || a.id - b.id)

  const despesasPorId = new Map(despesas.map((despesa) => [despesa.id, despesa]))
  const notas = lancamentosDoMes
    .map((nota) => ({
      ...nota,
      despesa: despesasPorId.get(nota.despesa_recorrente_id),
    }))
    .filter(
      (nota) =>
        nota.nota_pendente &&
        nota.despesa &&
        correspondeDepartamento(nota.despesa),
    )
  return {
    despesas,
    pendentes,
    notas,
    lancadas,
    acimaDoEstimado,
    totalExcedente: totalExcedenteCentavos / 100,
    total: previstas.length,
    percentual: previstas.length
      ? Math.round((lancadas / previstas.length) * 100)
      : 0,
  }
}
