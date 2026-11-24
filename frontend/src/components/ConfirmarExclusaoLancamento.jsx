import { useState } from 'react'
import { excluirLancamento } from '../services/api.js'
import { formatarData, formatarValor } from '../utils/formatacao.js'
import Modal from './Modal.jsx'

export default function ConfirmarExclusaoLancamento({ lancamento, onFechar, onConfirmado }) {
  const [excluindo, setExcluindo] = useState(false)
  const [erro, setErro] = useState('')

  async function confirmar(evento) {
    evento.preventDefault()
    if (excluindo) return
    setExcluindo(true)
    setErro('')
    try {
      await excluirLancamento(lancamento.id)
      onConfirmado()
    } catch (falha) {
      setErro(falha.message)
      setExcluindo(false)
    }
  }

  return (
    <Modal titulo="Excluir lançamento" ocupado={excluindo} onFechar={onFechar}
      descricao="Este lançamento será apagado definitivamente. Esta ação não pode ser desfeita.">
      <form className="formulario" onSubmit={confirmar}>
        <p className="despesa-confirmacao">
          <strong>{lancamento.despesa?.descricao || 'Despesa não encontrada'}</strong>
          <span>{lancamento.despesa?.fornecedor || 'Fornecedor não encontrado'}</span>
          <span>Lançamento #{lancamento.id} · {formatarData(lancamento.data_recebimento)}</span>
          <span>{formatarValor(lancamento.valor_recebido)}</span>
        </p>
        <p className="aviso">O acompanhamento do mês será atualizado após a exclusão.</p>
        {erro && <p className="erro-formulario" role="alert">{erro}</p>}
        <footer className="modal-acoes">
          <button type="button" className="botao secundario" disabled={excluindo} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className="botao perigo" disabled={excluindo}>
            {excluindo ? 'Excluindo…' : 'Excluir definitivamente'}
          </button>
        </footer>
      </form>
    </Modal>
  )
}
