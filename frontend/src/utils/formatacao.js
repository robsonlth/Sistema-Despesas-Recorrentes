const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})
const meses = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
]

export function formatarValor(valor) {
  return valor === null || valor === undefined || valor === ''
    ? 'Não informado'
    : moeda.format(Number(valor))
}

export function formatarMes(mes) {
  const [ano, numero] = mes.split('-')
  return `${meses[Number(numero) - 1]} de ${ano}`
}

export function formatarData(data) {
  return data.split('-').reverse().join('/')
}

// Usa a data local para evitar mudança de dia por causa do fuso horário.
export function dataLocalHoje() {
  const hoje = new Date()
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}-${String(hoje.getDate()).padStart(2, '0')}`
}

export function dataInicialDoFormulario(mes) {
  const hoje = dataLocalHoje()
  return hoje.startsWith(mes) ? hoje : `${mes}-01`
}

// Converte ano e mês em um número para avançar ou voltar, inclusive na virada do ano.
export function deslocarMes(mes, deslocamento) {
  const [ano, numero] = mes.split('-').map(Number)
  const indice = Math.min(
    9999 * 12 - 1,
    Math.max(0, (ano - 1) * 12 + numero - 1 + deslocamento),
  )
  return `${String(Math.floor(indice / 12) + 1).padStart(4, '0')}-${String((indice % 12) + 1).padStart(2, '0')}`
}
