import { useState } from 'react'
import { atualizarCadastro, criarCadastro } from '../services/api.js'
import Modal from './Modal.jsx'

export default function FormularioCadastro({ tipo, cadastro, onFechar, onSalvo }) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const fornecedor = tipo.id === 'fornecedores'

  async function salvar(evento) {
    evento.preventDefault()
    if (salvando) return
    const valores = Object.fromEntries(new FormData(evento.currentTarget))
    const nome = valores.nome.trim()
    if (!nome) {
      setErro('Informe o nome do cadastro.')
      return
    }

    setSalvando(true)
    setErro('')
    try {
      const dados = {
        nome,
        ativo: cadastro ? valores.ativo === 'true' : true,
      }
      // A validação do CNPJ fica na API.
      if (fornecedor) dados.cnpj = valores.cnpj.trim() || null
      const registro = cadastro
        ? await atualizarCadastro(tipo.id, cadastro.id, dados)
        : await criarCadastro(tipo.id, dados)
      onSalvo(registro)
    } catch (falha) {
      setErro(falha.message)
      setSalvando(false)
    }
  }

  return (
    <Modal
      titulo={cadastro ? `Editar ${tipo.singular}` : tipo.novo}
      ocupado={salvando}
      onFechar={onFechar}
    >
      <form className="formulario" onSubmit={salvar}>
        {erro && <p className="erro-formulario" role="alert">{erro}</p>}
        <fieldset disabled={salvando}>
          <label className="campo">
            Nome
            <input name="nome" defaultValue={cadastro?.nome ?? ''} required maxLength={150} />
          </label>
          {fornecedor && (
            <label className="campo">
              CNPJ <span className="opcional">Opcional</span>
              <input
                name="cnpj"
                type="text"
                defaultValue={cadastro?.cnpj ?? ''}
                maxLength={18}
                placeholder="Com ou sem pontuação"
                spellCheck={false}
              />
            </label>
          )}
          {cadastro && (
            <label className="campo">
              Situação
              <select name="ativo" defaultValue={String(cadastro.ativo)}>
                <option value="true">Ativo</option>
                <option value="false">Inativo</option>
              </select>
            </label>
          )}
        </fieldset>
        <footer className="modal-acoes">
          <button type="button" className="botao secundario" disabled={salvando} onClick={onFechar}>
            Cancelar
          </button>
          <button type="submit" className="botao primario" disabled={salvando}>
            {salvando ? 'Salvando…' : cadastro ? 'Salvar alterações' : 'Cadastrar'}
          </button>
        </footer>
      </form>
    </Modal>
  )
}
