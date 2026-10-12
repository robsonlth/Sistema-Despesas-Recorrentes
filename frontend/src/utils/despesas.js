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
    rateio: rateios.get(despesa.rateio_id) || 'Rateio não encontrado',
  }))
}
