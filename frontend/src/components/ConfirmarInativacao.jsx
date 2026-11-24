import { useState } from 'react'
import { inativarDespesa, inativarLancamento } from '../services/api.js'
import { formatarData, formatarValor } from '../utils/formatacao.js'
import Modal from './Modal.jsx'

export default function ConfirmarInativacao({ despesa, lancamento, onFechar, onConfirmado }) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const titulo = lancamento ? 'Inativar lançamento' : 'Inativar despesa'

  async function confirmar(evento) {
    evento.preventDefault()
    if (salvando) return
    setSalvando(true)
    setErro('')
    try {
      if (lancamento) {
        await inativarLancamento(lancamento.id)
      } else {
        await inativarDespesa(despesa.id)
      }
      onConfirmado()
    } catch (falha) {
      setErro(falha.message)
      setSalvando(false)
    }
  }

  return (
    <Modal
      titulo={titulo}
      descricao={lancamento
        ? 'O lançamento ficará inativo e não será considerado no acompanhamento do mês.'
        : 'A despesa ficará inativa. Os lançamentos já registrados serão mantidos.'}
      ocupado={salvando}
      onFechar={onFechar}
    >
      <form className="formulario" onSubmit={confirmar}>
        <p className="despesa-confirmacao">
          <strong>{despesa?.descricao || 'Despesa não encontrada'}</strong>
          <span>{despesa?.fornecedor || 'Fornecedor não encontrado'}</span>
          {lancamento && (
            <span>
              Lançamento #{lancamento.id} · {formatarData(lancamento.data_recebimento)}
              {' · '}{formatarValor(lancamento.valor_recebido)}
            </span>
          )}
        </p>
        {erro && <p className="erro-formulario" role="alert">{erro}</p>}
        <footer className="modal-acoes">
          <button type="button" className="botao secundario" disabled={salvando} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className="botao primario" disabled={salvando}>
            {salvando ? 'Inativando…' : titulo}
          </button>
        </footer>
      </form>
    </Modal>
  )
}
