import { dataLocalHoje } from './formatacao.js'

function dataEmUtc(ano, mes, dia) {
  const data = new Date(0)
  data.setUTCFullYear(ano, mes - 1, dia)
  return data
}

export function calcularVencimento(dia, mes, hoje = dataLocalHoje()) {
  if (!Number.isInteger(dia) || dia < 1 || dia > 31) {
    return { data: null, diasRestantes: null, proximo: false, vencido: false, aviso: '' }
  }

  const [ano, numeroMes] = mes.split('-').map(Number)
  // O dia zero do mês seguinte é o último dia da competência selecionada.
  const ultimoDia = dataEmUtc(ano, numeroMes + 1, 0).getUTCDate()
  const vencimento = dataEmUtc(ano, numeroMes, Math.min(dia, ultimoDia))
  const [anoHoje, mesHoje, diaHoje] = hoje.split('-').map(Number)
  // Compara as datas em UTC para contar dias inteiros, sem efeito do horário de verão.
  const diasRestantes = (vencimento - dataEmUtc(anoHoje, mesHoje, diaHoje)) / 86400000
  const proximo = diasRestantes >= 0 && diasRestantes <= 5
  const vencido = diasRestantes < 0
  let aviso = ''
  if (vencido) {
    const diasAtrasados = -diasRestantes
    aviso = `Vencida há ${diasAtrasados} ${diasAtrasados === 1 ? 'dia' : 'dias'}`
  } else if (proximo) {
    aviso = diasRestantes === 0 ? 'Vence hoje'
      : diasRestantes === 1 ? 'Vence amanhã'
        : `Vence em ${diasRestantes} dias`
  }

  return { data: vencimento.toISOString().slice(0, 10), diasRestantes, proximo, vencido, aviso }
}

export function compararVencimentos(a, b) {
  // Ordena as datas no formato YYYY-MM-DD e deixa as despesas sem vencimento no final.
  return (a.vencimento.data ?? '9999-99-99').localeCompare(b.vencimento.data ?? '9999-99-99')
    || a.fornecedor.localeCompare(b.fornecedor, 'pt-BR')
    || a.descricao.localeCompare(b.descricao, 'pt-BR')
    || a.id - b.id
}
