import { useState } from 'react'
import { atualizarDespesa, criarDespesa } from '../services/api.js'
import { dataInicialDoFormulario } from '../utils/formatacao.js'
import CampoFornecedor from './CampoFornecedor.jsx'
import EditorRateios from './EditorRateios.jsx'
import { resumirRateios } from '../utils/rateios.js'
import Modal from './Modal.jsx'

function CampoCadastro({ nome, titulo, registros, valor = '' }) {
  return (
    <label className="campo">
      {titulo}
      <select name={nome} required defaultValue={valor}>
        <option value="" disabled>
          Selecione
        </option>
        {registros.map((item) => (
          <option key={item.id} value={item.id}>
            {item.nome}
            {item.ativo ? '' : ' (inativo)'}
          </option>
        ))}
      </select>
    </label>
  )
}

export default function FormularioDespesa({
  dados,
  mes,
  despesa,
  onFechar,
  onSalvo,
}) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')
  const [valorEstimado, setValorEstimado] = useState(despesa?.valor_estimado ?? '')
  const [modoRateio, setModoRateio] = useState(despesa?.rateios?.[0]?.valor != null ? 'valor' : 'percentual')
  const [parcelas, setParcelas] = useState(() => despesa?.rateios?.length
    ? despesa.rateios.map((parcela, chave) => ({
      chave,
      rateio_id: String(parcela.rateio_id),
      quantia: String(parcela.percentual ?? parcela.valor),
    }))
    : [{ chave: 0, rateio_id: '', quantia: '100' }])
  const resumoRateios = resumirRateios(parcelas, modoRateio, valorEstimado)
  const semCadastros = [
    'fornecedores',
    'departamentos',
    'naturezas',
    'rateios',
  ].some((chave) => !dados[chave].length)

  async function salvar(evento) {
    evento.preventDefault()
    if (salvando) return
    if (resumoRateios.erro) {
      setErro(resumoRateios.erro)
      return
    }
    const valores = Object.fromEntries(new FormData(evento.currentTarget))
    if (!dados.fornecedores.some((fornecedor) => fornecedor.id === Number(valores.fornecedor_id))) {
      setErro('Selecione um fornecedor da lista.')
      return
    }
    if (
      valores.data_fim_vigencia &&
      valores.data_fim_vigencia < valores.data_inicio_vigencia
    ) {
      setErro('A data final da vigência não pode ser anterior à data inicial.')
      return
    }
    setSalvando(true)
    setErro('')
    try {
      // O formulário retorna texto, mas a API espera os IDs como números.
      const cadastro = {
        descricao: valores.descricao.trim(),
        fornecedor_id: Number(valores.fornecedor_id),
        departamento_id: Number(valores.departamento_id),
        natureza_financeira_id: Number(valores.natureza_financeira_id),
        rateios: parcelas.map((parcela) => ({
          rateio_id: Number(parcela.rateio_id),
          [modoRateio]: parcela.quantia,
        })),
        dia_vencimento: valores.dia_vencimento ? Number(valores.dia_vencimento) : null,
        data_inicio_vigencia: valores.data_inicio_vigencia,
        data_fim_vigencia: valores.data_fim_vigencia || null,
        valor_estimado: valores.valor_estimado || null,
        ativo: despesa ? valores.ativo === 'true' : true,
      }
      const registro = despesa
        ? await atualizarDespesa(despesa.id, cadastro)
        : await criarDespesa(cadastro)
      onSalvo(registro)
    } catch (falha) {
      setErro(falha.message)
      setSalvando(false)
    }
  }

  return (
    <Modal
      titulo={despesa ? 'Editar despesa' : 'Nova despesa'}
      ocupado={salvando}
      onFechar={onFechar}
    >
      <form onSubmit={salvar} className="formulario">
        {semCadastros && (
          <p className="aviso" role="status">
            É necessário ter fornecedor, departamento, natureza financeira e
            rateio cadastrados para salvar uma despesa.
          </p>
        )}
        {erro && (
          <p className="erro-formulario" role="alert">
            {erro}
          </p>
        )}
        <fieldset disabled={salvando}>
          <label className="campo">
            Descrição da despesa
            <textarea
              name="descricao"
              defaultValue={despesa?.descricao ?? ''}
              rows={2}
              required
              maxLength={350}
              placeholder="Ex.: Aluguel do escritório"
            />
          </label>
          <div className="formulario-grade">
            <CampoFornecedor
              registros={dados.fornecedores}
              valor={despesa?.fornecedor_id}
            />
            <CampoCadastro
              nome="departamento_id"
              titulo="Tipo de despesa / departamento"
              registros={dados.departamentos}
              valor={despesa?.departamento_id}
            />
            <CampoCadastro
              nome="natureza_financeira_id"
              titulo="Natureza financeira"
              registros={dados.naturezas}
              valor={despesa?.natureza_financeira_id}
            />
            <label className="campo">
              Dia do vencimento <span className="opcional">Opcional</span>
              <input type="number" name="dia_vencimento" min="1" max="31" step="1"
                defaultValue={despesa?.dia_vencimento ?? ''} placeholder="Dia do mês (1 a 31)" />
            </label>
            <label className="campo">
              Início da vigência
              <input
                type="date"
                name="data_inicio_vigencia"
                required
                defaultValue={
                  despesa?.data_inicio_vigencia ?? dataInicialDoFormulario(mes)
                }
                min="0001-01-01"
                max="9999-12-31"
              />
            </label>
            <label className="campo">
              Fim da vigência <span className="opcional">Opcional</span>
              <input
                type="date"
                name="data_fim_vigencia"
                defaultValue={despesa?.data_fim_vigencia ?? ''}
                min="0001-01-01"
                max="9999-12-31"
              />
            </label>
          </div>
          <label className="campo">
            Valor estimado (R$) {modoRateio === 'percentual' && <span className="opcional">Opcional</span>}
            <input
              type="number"
              inputMode="decimal"
              name="valor_estimado"
              value={valorEstimado}
              onChange={(evento) => setValorEstimado(evento.target.value)}
              required={modoRateio === 'valor'}
              min="0"
              max="99999999.99"
              step="0.01"
              placeholder="0,00"
            />
          </label>
          <EditorRateios registros={dados.rateios} parcelas={parcelas} modo={modoRateio}
            resumo={resumoRateios} onAlterar={setParcelas}
            onModo={(modo) => {
              setModoRateio(modo)
              setParcelas((atuais) => atuais.map((parcela) => ({ ...parcela, quantia: '' })))
              setErro('')
            }} />
          {despesa && (
            <label className="campo">
              Situação da despesa
              <select name="ativo" defaultValue={String(despesa.ativo)}>
                <option value="true">Ativa</option>
                <option value="false">Inativa</option>
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
            disabled={salvando || semCadastros || Boolean(resumoRateios.erro)}
          >
            {salvando
              ? 'Salvando…'
              : despesa ? 'Salvar alterações' : 'Cadastrar despesa'}
          </button>
        </footer>
      </form>
    </Modal>
  )
}
