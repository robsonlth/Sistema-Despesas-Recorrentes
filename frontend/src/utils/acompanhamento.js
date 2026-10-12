import { relacionarDespesas } from './despesas.js'

// Prepara as listas e os indicadores da tela de pendências.
export function prepararAcompanhamento(dados, mes, departamentoId = '') {
  const resumos = new Map(
    dados.resumo.map((item) => [item.despesa_recorrente_id, item]),
  )
  const despesas = relacionarDespesas(dados)
  const correspondeDepartamento = (despesa) =>
    !departamentoId || despesa.departamento_id === Number(departamentoId)
  // Compara ano e mês para verificar se a despesa está vigente na competência.
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
  )
  const lancadas = previstas.filter(
    (despesa) => resumos.get(despesa.id)?.quantidade_lancamentos > 0,
  ).length
  // Agrupa as pendências por departamento.
  const grupos = new Map()
  for (const despesa of pendentes) {
    if (!grupos.has(despesa.departamento_id)) {
      grupos.set(despesa.departamento_id, {
        id: despesa.departamento_id,
        nome: despesa.departamento,
        despesas: [],
      })
    }
    grupos.get(despesa.departamento_id).despesas.push(despesa)
  }
  for (const grupo of grupos.values()) {
    grupo.despesas.sort(
      (a, b) =>
        a.fornecedor.localeCompare(b.fornecedor, 'pt-BR') ||
        a.descricao.localeCompare(b.descricao, 'pt-BR'),
    )
  }
  const despesasPorId = new Map(despesas.map((despesa) => [despesa.id, despesa]))
  const notas = dados.notas
    .map((nota) => ({
      ...nota,
      despesa: despesasPorId.get(nota.despesa_recorrente_id),
    }))
    .filter(
      (nota) =>
        nota.ativo &&
        nota.nota_pendente &&
        nota.mes_referencia?.slice(0, 7) === mes &&
        nota.despesa &&
        correspondeDepartamento(nota.despesa),
    )
  return {
    despesas,
    pendentes,
    notas,
    lancadas,
    total: previstas.length,
    percentual: previstas.length
      ? Math.round((lancadas / previstas.length) * 100)
      : 0,
    grupos: [...grupos.values()].sort((a, b) =>
      a.nome.localeCompare(b.nome, 'pt-BR'),
    ),
  }
}
