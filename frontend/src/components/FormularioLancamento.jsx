import { useState } from 'react'
import { criarLancamento } from '../services/api.js'
import { dataInicialDoFormulario, formatarMes } from '../utils/formatacao.js'
import Modal from './Modal.jsx'

export default function FormularioLancamento({
  despesas,
  despesa,
  mes,
  onFechar,
  onSalvo,
}) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [dataRecebimento, setDataRecebimento] = useState(
    dataInicialDoFormulario(mes),
  )

  async function salvar(evento) {
    // Evita recarregar a página ao enviar o formulário.
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
        ativo: true,
      }
      const registro = await criarLancamento(cadastro)
      onSalvo(registro)
    } catch (falha) {
      setErro(falha.message)
      setSalvando(false)
    }
  }

  return (
    <Modal
      titulo="Novo lançamento"
      descricao="Registre o recebimento vinculado a uma despesa recorrente."
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
              defaultValue={despesa?.id ?? ''}
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
            Competência:{' '}
            {dataRecebimento
              ? formatarMes(dataRecebimento.slice(0, 7))
              : 'selecione a data'}
            . Definida pela data de recebimento.
          </p>
          <label className="campo">
            Observação <span className="opcional">Opcional</span>
            <textarea
              name="observacao"
              maxLength={320}
              rows={3}
              placeholder="Informações sobre este lançamento"
            />
          </label>
          <label className="campo-checkbox">
            <input
              name="nota_pendente"
              type="checkbox"
            />
            <span>Nota fiscal pendente</span>
          </label>
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
