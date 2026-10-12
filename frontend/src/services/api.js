const nomesCampos = {
  valor_recebido: 'Valor recebido',
  data_recebimento: 'Data de recebimento',
  despesa_recorrente_id: 'Despesa',
  observacao: 'Observação',
}

// Envia a requisição e trata os erros retornados pela API.
async function requisitar(caminho, opcoes = {}) {
  let resposta
  try {
    resposta = await fetch(`/api${caminho}`, {
      ...opcoes,
      headers: {
        ...(opcoes.body ? { 'Content-Type': 'application/json' } : {}),
        ...opcoes.headers,
      },
    })
  } catch (erro) {
    if (erro.name === 'AbortError') throw erro
    throw new Error(
      'Não foi possível conectar ao servidor. Tente novamente em instantes.',
    )
  }
  const dados = await resposta.json().catch(() => null)
  if (!resposta.ok) {
    // O FastAPI pode retornar uma lista de erros de validação.
    if (Array.isArray(dados?.detail)) {
      throw new Error(
        dados.detail
          .map((erro) => {
            const campo = nomesCampos[erro.loc.at(-1)] || 'Dados do formulário'
            return `${campo}: ${erro.msg.replace(/^Value error, /, '')}`
          })
          .join(' '),
      )
    }
    throw new Error(
      typeof dados?.detail === 'string'
        ? dados.detail
        : 'Não foi possível concluir a solicitação. Tente novamente em instantes.',
    )
  }
  if (dados === null) {
    throw new Error('Não foi possível ler a resposta do servidor.')
  }
  return dados
}

const caminhosDespesas = {
  fornecedores: '/fornecedores',
  departamentos: '/departamentos',
  naturezas: '/naturezas-financeiras',
  rateios: '/rateios',
  despesas: '/despesas-recorrentes',
}

async function carregarListas(caminhos, signal) {
  const resultados = await Promise.all(
    Object.entries(caminhos).map(async ([nome, caminho]) => {
      const registros = await requisitar(caminho, { signal })
      if (!Array.isArray(registros)) {
        throw new Error('O servidor retornou uma lista de dados inválida.')
      }
      return [nome, registros]
    }),
  )
  return Object.fromEntries(resultados)
}

export function carregarPendencias(mes, signal) {
  return carregarListas({
    ...caminhosDespesas,
    resumo: `/lancamentos-despesa/resumo-mensal?mes_referencia=${mes}-01`,
    notas: `/lancamentos-despesa?mes_referencia=${mes}-01&ativo=true&nota_pendente=true`,
  }, signal)
}

export function criarLancamento(dados) {
  return requisitar('/lancamentos-despesa', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}
