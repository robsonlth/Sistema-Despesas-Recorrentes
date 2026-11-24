const nomesCampos = {
  nome: 'Nome',
  cnpj: 'CNPJ',
  descricao: 'Descrição',
  fornecedor_id: 'Fornecedor',
  departamento_id: 'Departamento',
  natureza_financeira_id: 'Natureza financeira',
  rateio_id: 'Rateio',
  rateios: 'Rateios',
  percentual: 'Porcentagem',
  valor: 'Valor do rateio',
  dia_vencimento: 'Dia do vencimento',
  data_inicio_vigencia: 'Início da vigência',
  data_fim_vigencia: 'Fim da vigência',
  valor_estimado: 'Valor estimado',
  valor_recebido: 'Valor recebido',
  data_recebimento: 'Data de recebimento',
  despesa_recorrente_id: 'Despesa',
  observacao: 'Observação',
}

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
  if (resposta.status === 204) return null
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

const caminhosCadastros = {
  fornecedores: '/fornecedores',
  departamentos: '/departamentos',
  naturezas: '/naturezas-financeiras',
  rateios: '/rateios',
}

const caminhosDespesas = {
  ...caminhosCadastros,
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

export function carregarDespesas(signal) {
  return carregarListas(caminhosDespesas, signal)
}

export function carregarPendencias(mes, signal) {
  return carregarListas({
    ...caminhosDespesas,
    resumo: `/lancamentos-despesa/resumo-mensal?mes_referencia=${mes}-01`,
    lancamentos: `/lancamentos-despesa?mes_referencia=${mes}-01&ativo=true`,
  }, signal)
}

export function carregarAnalise(mes, signal) {
  return requisitar(`/lancamentos-despesa/analise?mes_referencia=${mes}-01`, { signal })
}

export function criarDespesa(dados) {
  return requisitar('/despesas-recorrentes', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function carregarLancamentos(mes, signal) {
  return carregarListas({
    ...caminhosDespesas,
    resumo: `/lancamentos-despesa/resumo-mensal?mes_referencia=${mes}-01`,
    lancamentos: `/lancamentos-despesa?mes_referencia=${mes}-01`,
  }, signal)
}

export function criarLancamento(dados) {
  return requisitar('/lancamentos-despesa', {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function atualizarDespesa(id, dados) {
  return requisitar(`/despesas-recorrentes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(dados),
  })
}

export function inativarDespesa(id) {
  return requisitar(`/despesas-recorrentes/${id}`, { method: 'DELETE' })
}

export function atualizarLancamento(id, dados) {
  return requisitar(`/lancamentos-despesa/${id}`, {
    method: 'PUT',
    body: JSON.stringify(dados),
  })
}

export function inativarLancamento(id) {
  return requisitar(`/lancamentos-despesa/${id}/inativar`, { method: 'PATCH' })
}

export function excluirLancamento(id) {
  return requisitar(`/lancamentos-despesa/${id}`, { method: 'DELETE' })
}

export function carregarCadastros(signal) {
  return carregarListas(caminhosCadastros, signal)
}

function caminhoCadastro(tipo) {
  if (!Object.hasOwn(caminhosCadastros, tipo)) {
    throw new Error('Tipo de cadastro inválido.')
  }
  return caminhosCadastros[tipo]
}

export function criarCadastro(tipo, dados) {
  return requisitar(caminhoCadastro(tipo), {
    method: 'POST',
    body: JSON.stringify(dados),
  })
}

export function atualizarCadastro(tipo, id, dados) {
  return requisitar(`${caminhoCadastro(tipo)}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(dados),
  })
}

export function inativarCadastro(tipo, id) {
  return requisitar(`${caminhoCadastro(tipo)}/${id}`, { method: 'DELETE' })
}
