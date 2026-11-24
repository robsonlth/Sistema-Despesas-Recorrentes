import { useState } from 'react'
import { inativarCadastro } from '../services/api.js'
import { formatarCnpj } from '../utils/cadastros.js'
import Modal from './Modal.jsx'

export default function ConfirmarInativacaoCadastro({ tipo, cadastro, onFechar, onConfirmado }) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')

  async function confirmar(evento) {
    evento.preventDefault()
    if (salvando) return
    setSalvando(true)
    setErro('')
    try {
      await inativarCadastro(tipo.id, cadastro.id)
      onConfirmado()
    } catch (falha) {
      setErro(falha.message)
      setSalvando(false)
    }
  }

  return (
    <Modal
      titulo={`Inativar ${tipo.singular}`}
      descricao="O cadastro ficará inativo. As despesas e os lançamentos vinculados serão mantidos."
      ocupado={salvando}
      onFechar={onFechar}
    >
      <form className="formulario" onSubmit={confirmar}>
        <p className="despesa-confirmacao">
          <strong>{cadastro.nome}</strong>
          {cadastro.cnpj && <span>CNPJ: {formatarCnpj(cadastro.cnpj)}</span>}
        </p>
        {erro && <p className="erro-formulario" role="alert">{erro}</p>}
        <footer className="modal-acoes">
          <button type="button" className="botao secundario" disabled={salvando} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className="botao primario" disabled={salvando}>
            {salvando ? 'Inativando…' : 'Inativar cadastro'}
          </button>
        </footer>
      </form>
    </Modal>
  )
}
