// Converte valores e porcentagens em centésimos para conferir a soma sem arredondamento.
export function paraCentesimos(valor) {
  const texto = String(valor ?? '')
  if (!/^\d+(\.\d{1,2})?$/.test(texto)) return null
  const [inteiros, decimais = ''] = texto.split('.')
  const resultado = Number(inteiros) * 100 + Number(decimais.padEnd(2, '0'))
  return Number.isSafeInteger(resultado) ? resultado : null
}

export function resumirRateios(parcelas, modo, valorEstimado) {
  const quantias = parcelas.map((parcela) => paraCentesimos(parcela.quantia))
  const total = quantias.reduce((soma, quantia) => soma + (quantia ?? 0), 0)
  const esperado = modo === 'percentual' ? 10000 : paraCentesimos(valorEstimado)
  const ids = parcelas.map((parcela) => Number(parcela.rateio_id))
  let erro = ''

  if (!parcelas.length) erro = 'Adicione pelo menos um rateio.'
  else if (ids.some((id) => !Number.isInteger(id) || id <= 0 || id > 2147483647)) {
    erro = 'Selecione o cadastro de cada rateio.'
  } else if (new Set(ids).size !== ids.length) erro = 'Não repita o mesmo rateio na despesa.'
  else if (quantias.some((quantia) => quantia === null)) {
    erro = 'Preencha as parcelas com números positivos ou zero e até duas casas decimais.'
  } else if (quantias.some((quantia) => quantia > (modo === 'percentual' ? 10000 : 9999999999))) {
    erro = modo === 'percentual' ? 'Cada porcentagem deve ficar entre 0% e 100%.' : 'O valor de cada rateio deve ser menor que R$ 100.000.000,00.'
  } else if (esperado === null) erro = 'Informe o valor estimado da despesa para ratear em reais.'
  else if (total !== esperado) {
    erro = modo === 'percentual'
      ? 'As porcentagens dos rateios devem somar 100%.'
      : 'A soma dos rateios deve ser igual ao valor estimado da despesa.'
  }

  return { total, esperado, diferenca: esperado === null ? null : esperado - total, erro }
}
