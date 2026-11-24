import { formatarData, formatarPercentual, formatarValor, formatarVencimento } from '../utils/formatacao.js'

export default function DetalhesRateio({ despesa, vencimento }) {
  return (
    <div className="detalhes-rateio">
      <span className="detalhe-recorrente">Rateios:</span>
      {despesa?.rateios?.length ? (
        <ul>
          {despesa.rateios.map((parcela) => (
            <li key={parcela.rateio_id}>
              {parcela.nome} — {parcela.percentual != null
                ? formatarPercentual(parcela.percentual) : formatarValor(parcela.valor)}
            </li>
          ))}
        </ul>
      ) : <span>Não informado</span>}
      <span className="detalhe-recorrente">
        <span>Vencimento:</span> {vencimento?.data
          ? formatarData(vencimento.data) : formatarVencimento(despesa?.dia_vencimento)}
      </span>
      {vencimento?.aviso && (
        <span className={vencimento.vencido ? 'aviso-vencimento aviso-vencimento-atrasado' : 'aviso-vencimento'}>
          {vencimento.aviso}
        </span>
      )}
    </div>
  )
}
