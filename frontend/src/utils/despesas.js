export function relacionarDespesas(dados) {
  const porId = (registros) =>
    new Map(registros.map((registro) => [registro.id, registro.nome]))
  const fornecedores = porId(dados.fornecedores)
  const departamentos = porId(dados.departamentos)
  const naturezas = porId(dados.naturezas)
  const rateios = porId(dados.rateios)

  return dados.despesas.map((despesa) => ({
    ...despesa,
    fornecedor: fornecedores.get(despesa.fornecedor_id) || 'Fornecedor não encontrado',
    departamento: departamentos.get(despesa.departamento_id) || 'Departamento não encontrado',
    natureza: naturezas.get(despesa.natureza_financeira_id) || 'Natureza não encontrada',
    rateios: (despesa.rateios ?? []).map((parcela) => ({
      ...parcela,
      nome: rateios.get(parcela.rateio_id) || 'Rateio não encontrado',
    })),
  }))
}

export function normalizarTexto(texto) {
  // Ignora maiúsculas e acentos apenas na comparação da busca.
  return texto
    .trim()
    .toLocaleLowerCase('pt-BR')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

export function filtrarDespesas(despesas, { busca, mes, departamento, situacao }) {
  const termo = normalizarTexto(busca)
  const registros = despesas.filter((despesa) => {
    const correspondeBusca = normalizarTexto(despesa.descricao).includes(termo)
      || normalizarTexto(despesa.fornecedor).includes(termo)
    const correspondeDepartamento = !departamento
      || despesa.departamento_id === Number(departamento)
    const correspondeSituacao = situacao === 'todos'
      || despesa.ativo === (situacao === 'ativos')
    const vigente = despesa.data_inicio_vigencia.slice(0, 7) <= mes
      && (!despesa.data_fim_vigencia || despesa.data_fim_vigencia.slice(0, 7) >= mes)
    return correspondeBusca && correspondeDepartamento && correspondeSituacao && vigente
  }).sort((a, b) => a.descricao.localeCompare(b.descricao, 'pt-BR') || a.id - b.id)

  // Soma em centavos para evitar diferenças de arredondamento com decimais.
  const totalCentavos = registros.reduce((total, despesa) => {
    const [inteiros, decimais = ''] = String(despesa.valor_estimado ?? '0').split('.')
    return total + Number(inteiros) * 100 + Number(decimais.padEnd(2, '0'))
  }, 0)

  return {
    registros,
    valorTotal: totalCentavos / 100,
    semEstimativa: registros.filter((despesa) => despesa.valor_estimado === null).length,
  }
}
