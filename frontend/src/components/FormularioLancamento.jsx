import { useState } from 'react'
import { atualizarLancamento, criarLancamento } from '../services/api.js'
import { dataInicialDoFormulario, formatarMes, formatarValor } from '../utils/formatacao.js'
import Modal from './Modal.jsx'

export default function FormularioLancamento({
  despesas,
  despesa,
  lancamento,
  mes,
  onFechar,
  onSalvo,
}) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [despesaId, setDespesaId] = useState(
    String(lancamento?.despesa_recorrente_id ?? despesa?.id ?? ''),
  )
  const [valorRecebido, setValorRecebido] = useState(lancamento?.valor_recebido ?? '')
  const [dataRecebimento, setDataRecebimento] = useState(
    lancamento?.data_recebimento ?? dataInicialDoFormulario(mes),
  )
  const despesaSelecionada = despesas.find((item) => item.id === Number(despesaId))
  const valorEstimado = despesaSelecionada?.valor_estimado
  // Uma estimativa de zero também deve ser comparada.
  const acimaDoEstimado = valorRecebido !== ''
    && valorEstimado !== null && valorEstimado !== undefined && valorEstimado !== ''
    && Number(valorRecebido) > Number(valorEstimado)

  async function salvar(evento) {
    evento.preventDefault()
    if (salvando) return
    const valores = Object.fromEntries(new FormData(evento.currentTarget))
    setSalvando(true)
    setErro('')
    try {
      // Envia a data de recebimento; o backend calcula a competência.
      const cadastro = {
        despesa_recorrente_id: Number(valores.despesa_recorrente_id),
        valor_recebido: valores.valor_recebido,
        data_recebimento: valores.data_recebimento,
        observacao: valores.observacao.trim() || null,
        nota_pendente: valores.nota_pendente === 'on',
        ativo: lancamento ? valores.ativo === 'true' : true,
      }
      const registro = lancamento
        ? await atualizarLancamento(lancamento.id, cadastro)
        : await criarLancamento(cadastro)
      onSalvo(registro)
    } catch (falha) {
      setErro(falha.message)
      setSalvando(false)
    }
  }

  return (
    <Modal
      titulo={lancamento ? 'Editar lançamento' : 'Novo lançamento'}
      ocupado={salvando}
      onFechar={onFechar}
    >
      <form onSubmit={salvar} className="formulario">
        {!despesas.length && (
          <p className="aviso">
            Cadastre uma despesa recorrente antes de fazer um lançamento.
          </p>
        )}
        {erro && (
          <p className="erro-formulario" role="alert">
            {erro}
          </p>
        )}
        <fieldset disabled={salvando}>
          <label className="campo">
            Despesa recorrente
            <select
              name="despesa_recorrente_id"
              required
              value={despesaId}
              onChange={(evento) => setDespesaId(evento.target.value)}
            >
              <option value="" disabled>
                Selecione uma despesa
              </option>
              {despesas.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.descricao} — {item.fornecedor}
                  {item.ativo ? '' : ' (inativa)'}
                </option>
              ))}
            </select>
          </label>
          <div className="formulario-grade">
            <label className="campo">
              Valor recebido (R$)
              <input
                name="valor_recebido"
                value={valorRecebido}
                onChange={(evento) => setValorRecebido(evento.target.value)}
                aria-describedby={acimaDoEstimado ? 'aviso-valor-estimado' : undefined}
                type="number"
                inputMode="decimal"
                min="0"
                max="99999999.99"
                step="0.01"
                required
                placeholder="0,00"
              />
            </label>
            <label className="campo">
              Data de recebimento
              <input
                name="data_recebimento"
                type="date"
                min="0001-01-01"
                max="9999-12-31"
                value={dataRecebimento}
                onChange={(evento) => setDataRecebimento(evento.target.value)}
                required
              />
            </label>
          </div>
          <p className="dica-campo">
            {dataRecebimento
              ? `Competência: ${formatarMes(dataRecebimento.slice(0, 7))}, conforme a data de recebimento.`
              : 'Selecione a data de recebimento para definir a competência.'}
          </p>
          {acimaDoEstimado && (
            <p id="aviso-valor-estimado" className="aviso" role="status">
              O valor informado é maior que o estimado de {formatarValor(valorEstimado)}.
              {' '}Se desejar, explique o motivo no campo abaixo.
            </p>
          )}
          <label className="campo">
            {acimaDoEstimado ? 'Justificativa / observação' : 'Observação'}
            {' '}<span className="opcional">Opcional</span>
            <textarea
              name="observacao"
              defaultValue={lancamento?.observacao ?? ''}
              aria-describedby={acimaDoEstimado ? 'aviso-valor-estimado' : undefined}
              maxLength={320}
              rows={3}
              placeholder={acimaDoEstimado
                ? 'Se desejar, explique o motivo do valor acima do estimado'
                : 'Informações sobre este lançamento'}
            />
          </label>
          <label className="campo-checkbox">
            <input
              name="nota_pendente"
              type="checkbox"
              defaultChecked={lancamento?.nota_pendente ?? false}
            />
            <span>Nota fiscal pendente</span>
          </label>
          {lancamento && (
            <label className="campo">
              Situação do lançamento
              <select name="ativo" defaultValue={String(lancamento.ativo)}>
                <option value="true">Ativo</option>
                <option value="false">Inativo</option>
              </select>
            </label>
          )}
        </fieldset>
        <footer className="modal-acoes">
          <button
            type="button"
            className="botao secundario"
            disabled={salvando}
            onClick={onFechar}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="botao primario"
            disabled={salvando || !despesas.length}
          >
            {salvando ? 'Salvando…' : 'Salvar lançamento'}
          </button>
        </footer>
      </form>
    </Modal>
  )
}
