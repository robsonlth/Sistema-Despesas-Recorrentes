import { formatarValor, formatarPercentual } from '../utils/formatacao.js'

export default function EditorRateios({ registros, parcelas, modo, resumo, onAlterar, onModo }) {
  const formatar = (quantia) => modo === 'percentual'
    ? formatarPercentual(quantia / 100)
    : formatarValor(quantia / 100)

  function alterar(chave, campo, valor) {
    onAlterar(parcelas.map((parcela) => parcela.chave === chave ? { ...parcela, [campo]: valor } : parcela))
  }

  function adicionar() {
    const chave = Math.max(-1, ...parcelas.map((parcela) => parcela.chave)) + 1
    onAlterar([...parcelas, { chave, rateio_id: '', quantia: '' }])
  }

  return (
    <section className="editor-rateios" aria-labelledby="titulo-rateios">
      <h3 id="titulo-rateios">Rateios da despesa</h3>
      <label className="campo">
        Informar parcelas em
        <select value={modo} onChange={(evento) => onModo(evento.target.value)}>
          <option value="percentual">Porcentagem (%)</option>
          <option value="valor">Valor (R$)</option>
        </select>
      </label>
      <p className="dica-campo">
        {modo === 'percentual'
          ? 'Distribua 100% entre os rateios. Ao trocar o modo, preencha as parcelas novamente.'
          : 'Distribua o valor estimado da despesa. Ao trocar o modo, preencha as parcelas novamente.'}
      </p>
      {parcelas.map((parcela, indice) => (
        <div className="linha-rateio" key={parcela.chave}>
          <label className="campo">
            Rateio {indice + 1}
            <select required value={parcela.rateio_id} onChange={(evento) => alterar(parcela.chave, 'rateio_id', evento.target.value)}>
              <option value="" disabled>Selecione</option>
              {registros.map((registro) => (
                <option key={registro.id} value={registro.id}
                  disabled={parcelas.some((outra) => outra.chave !== parcela.chave && Number(outra.rateio_id) === registro.id)}>
                  {registro.nome}{registro.ativo ? '' : ' (inativo)'}
                </option>
              ))}
            </select>
          </label>
          <label className="campo">
            {modo === 'percentual' ? 'Porcentagem (%)' : 'Valor (R$)'}
            <input type="number" inputMode="decimal" required min="0" step="0.01"
              max={modo === 'percentual' ? '100' : '99999999.99'} value={parcela.quantia}
              aria-label={`${modo === 'percentual' ? 'Porcentagem' : 'Valor'} do rateio ${indice + 1}`}
              onChange={(evento) => alterar(parcela.chave, 'quantia', evento.target.value)} />
          </label>
          <button type="button" className="botao-texto acao-excluir" disabled={parcelas.length === 1}
            aria-label={`Remover rateio ${indice + 1}`}
            onClick={() => onAlterar(parcelas.filter((outra) => outra.chave !== parcela.chave))}>
            Remover
          </button>
        </div>
      ))}
      <button type="button" className="botao secundario" onClick={adicionar}
        disabled={parcelas.length >= registros.length}>Adicionar rateio</button>
      <div className="resumo-rateios" role="status" aria-live="polite" aria-atomic="true">
        <strong>Distribuído: {formatar(resumo.total)}</strong>
        {resumo.diferenca !== null && (
          <span>{resumo.diferenca === 0 ? 'Total completo.'
            : `${resumo.diferenca > 0 ? 'Faltam' : 'Excedem'} ${formatar(Math.abs(resumo.diferenca))}.`}</span>
        )}
        {resumo.erro && <p>{resumo.erro}</p>}
      </div>
    </section>
  )
}
