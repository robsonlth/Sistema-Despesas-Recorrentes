import { normalizarTexto } from './despesas.js'

export const tiposCadastro = [
  { id: 'fornecedores', titulo: 'Fornecedores', singular: 'fornecedor', novo: 'Novo fornecedor' },
  { id: 'departamentos', titulo: 'Tipo de despesa / departamento', singular: 'departamento', novo: 'Novo departamento' },
  { id: 'naturezas', titulo: 'Naturezas financeiras', singular: 'natureza financeira', novo: 'Nova natureza financeira' },
  { id: 'rateios', titulo: 'Rateios', singular: 'rateio', novo: 'Novo rateio' },
]

export function filtrarCadastros(registros, { busca, situacao }) {
  const termo = normalizarTexto(busca)
  // Permite buscar o CNPJ com ou sem a pontuação da máscara.
  const termoCnpj = termo.replace(/[./\s-]/g, '')

  return registros.filter((registro) => {
    const cnpj = normalizarTexto(registro.cnpj ?? '').replace(/[./\s-]/g, '')
    const correspondeBusca = normalizarTexto(registro.nome).includes(termo)
      || (termoCnpj !== '' && cnpj.includes(termoCnpj))
    const correspondeSituacao = situacao === 'todos'
      || registro.ativo === (situacao === 'ativos')
    return correspondeBusca && correspondeSituacao
  }).sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR') || a.id - b.id)
}

export function formatarCnpj(cnpj) {
  if (!cnpj) return 'Não informado'
  return cnpj.replace(/^([A-Z0-9]{2})([A-Z0-9]{3})([A-Z0-9]{3})([A-Z0-9]{4})([0-9]{2})$/i, '$1.$2.$3/$4-$5')
}
