import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import DetalhesRateio from '../components/DetalhesRateio.jsx'
import FormularioDespesa from '../components/FormularioDespesa.jsx'
import FormularioLancamento from '../components/FormularioLancamento.jsx'
import ConfirmarInativacao from '../components/ConfirmarInativacao.jsx'
import { carregarDespesas } from '../services/api.js'
import { filtrarDespesas, relacionarDespesas } from '../utils/despesas.js'
import {
  dataLocalHoje,
  formatarData,
  formatarMes,
  formatarValor,
} from '../utils/formatacao.js'

export default function DespesasRecorrentes() {
  const [filtros, setFiltros] = useState(() => ({
    busca: '',
    mes: dataLocalHoje().slice(0, 7),
    departamento: '',
    situacao: 'ativos',
  }))
  const [filtrosAplicados, setFiltrosAplicados] = useState(filtros)
  const [atualizacao, setAtualizacao] = useState(0)
  const [consulta, setConsulta] = useState({ versao: -1, dados: null, erro: '' })
  const [modal, setModal] = useState(null)
  const [mensagem, setMensagem] = useState('')

  const carregando = consulta.versao !== atualizacao
  const dados = carregando ? null : consulta.dados
  const erro = carregando ? '' : consulta.erro
  const despesas = dados ? relacionarDespesas(dados) : []
  const resultado = filtrarDespesas(despesas, filtrosAplicados)

  useEffect(() => {
    const controle = new AbortController()
    carregarDespesas(controle.signal)
      .then((resposta) => {
        if (!controle.signal.aborted) {
          setConsulta({ versao: atualizacao, dados: resposta, erro: '' })
        }
      })
      .catch((falha) => {
        if (!controle.signal.aborted) {
          setConsulta({ versao: atualizacao, dados: null, erro: falha.message })
        }
      })
    return () => controle.abort()
  }, [atualizacao])

  function alterarFiltro(evento) {
    const { name, value } = evento.target
    setFiltros((anteriores) => ({ ...anteriores, [name]: value }))
  }

  function filtrar(evento) {
    evento.preventDefault()
    // A lista só muda quando o usuário aplica os filtros.
    setFiltrosAplicados({ ...filtros })
    setMensagem('')
  }

  function concluir(texto) {
    setModal(null)
    setMensagem(texto)
    setAtualizacao((valor) => valor + 1)
  }

  return (
    <Layout pagina="despesas-recorrentes">
      <div className="pagina-despesas">
        <header className="cabecalho-pagina">
          <div>
            <p className="sobretitulo">GESTÃO DE DESPESAS</p>
            <h1>Despesas recorrentes<span className="ponto-titulo">.</span></h1>
          </div>
          <button
            type="button"
            className="botao primario"
            disabled={!dados}
            onClick={() => setModal({ tipo: 'nova' })}
          >
            Nova despesa
          </button>
        </header>

        <form
          className="filtros filtros-recorrentes"
          aria-label="Filtros de despesas recorrentes"
          onSubmit={filtrar}
        >
          <div className="filtro-busca">
            <label htmlFor="busca-despesa">Buscar despesa ou fornecedor</label>
            <div className="controle-busca">
              <input
                id="busca-despesa"
                name="busca"
                type="search"
                placeholder="Digite para buscar…"
                value={filtros.busca}
                onChange={alterarFiltro}
              />
            </div>
          </div>
          <div className="filtro-competencia">
            <label htmlFor="mes-despesas">Competência</label>
            <div className="controle-mes">
              <input
                id="mes-despesas"
                name="mes"
                type="month"
                min="0001-01"
                max="9999-12"
                required
                value={filtros.mes}
                onChange={alterarFiltro}
              />
            </div>
          </div>
          <div className="filtro-departamento">
            <label htmlFor="departamento-despesas">Tipo de despesa / departamento</label>
            <select
              id="departamento-despesas"
              name="departamento"
              value={filtros.departamento}
              onChange={alterarFiltro}
              disabled={!dados}
            >
              <option value="">Todos os tipos</option>
              {dados?.departamentos.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}{item.ativo ? '' : ' (inativo)'}
                </option>
              ))}
            </select>
          </div>
          <div className="filtro-departamento">
            <label htmlFor="situacao-despesas">Situação da despesa</label>
            <select
              id="situacao-despesas"
              name="situacao"
              value={filtros.situacao}
              onChange={alterarFiltro}
            >
              <option value="ativos">Ativas</option>
              <option value="inativos">Inativas</option>
              <option value="todos">Todas</option>
            </select>
          </div>
          <button type="submit" className="botao secundario" disabled={!dados}>
            Filtrar
          </button>
        </form>

        {mensagem && (
          <div className="mensagem-sucesso" role="status">
            <span>{mensagem}</span>
            <button
              type="button"
              className="botao-texto"
              aria-label="Fechar mensagem"
              onClick={() => setMensagem('')}
            >
              Fechar
            </button>
          </div>
        )}

        {carregando ? (
          <div className="estado-carregando" role="status" aria-busy="true">
            <span className="somente-leitor">Carregando despesas recorrentes…</span>
            <div className="esqueleto esqueleto-titulo" />
            {[1, 2, 3].map((item) => <div key={item} className="esqueleto esqueleto-linha" />)}
          </div>
        ) : erro ? (
          <div className="estado-vazio" role="alert">
            <h3>Não foi possível carregar as despesas</h3>
            <p>{erro}</p>
            <button
              type="button"
              className="botao secundario"
              onClick={() => setAtualizacao((valor) => valor + 1)}
            >
              Tentar novamente
            </button>
          </div>
        ) : (
          <section className="grupo-despesas lista-recorrentes" aria-label="Despesas encontradas">
            <header className="resumo-recorrentes" aria-live="polite" aria-atomic="true">
              <div>
                <h2>
                  {resultado.registros.length}{' '}
                  {resultado.registros.length === 1 ? 'despesa encontrada' : 'despesas encontradas'}
                </h2>
                <p>{formatarMes(filtrosAplicados.mes)}</p>
              </div>
              <div className="total-estimado">
                <span>Valor estimado total</span>
                <strong>{formatarValor(resultado.valorTotal)}</strong>
              </div>
            </header>
            {resultado.registros.length ? (
              <div
                className="tabela-rolagem"
                role="region"
                aria-label="Tabela de despesas recorrentes"
                tabIndex={0}
              >
                <table className="tabela-despesas tabela-recorrentes">
                  <caption className="somente-leitor">
                    Despesas recorrentes em {formatarMes(filtrosAplicados.mes)}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Despesa / fornecedor</th>
                      <th scope="col">Tipo de despesa / departamento</th>
                      <th scope="col">Vigência</th>
                      <th scope="col" className="coluna-valor">Valor estimado</th>
                      <th scope="col">Situação</th>
                      <th scope="col" className="coluna-acao">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultado.registros.map((despesa) => (
                      <tr key={despesa.id}>
                        <td>
                          <strong className="fornecedor-nome descricao-recorrente">
                            {despesa.descricao}
                          </strong>
                          <span className="despesa-descricao">{despesa.fornecedor}</span>
                        </td>
                        <td>
                          <span className="etiqueta-rateio etiqueta-departamento">
                            {despesa.departamento}
                          </span>
                          <span className="detalhe-recorrente">
                            <span>Natureza:</span> {despesa.natureza}
                          </span>
                          <DetalhesRateio despesa={despesa} />
                        </td>
                        <td>
                          <time dateTime={despesa.data_inicio_vigencia}>
                            {formatarData(despesa.data_inicio_vigencia)}
                          </time>
                          <span className="despesa-contrato">
                            {despesa.data_fim_vigencia ? (
                              <>Até <time dateTime={despesa.data_fim_vigencia}>
                                {formatarData(despesa.data_fim_vigencia)}
                              </time></>
                            ) : 'Sem data final'}
                          </span>
                        </td>
                        <td className="coluna-valor">
                          <span className={
                            despesa.valor_estimado === null ? 'valor-ausente' : 'valor-despesa'
                          }>
                            {formatarValor(despesa.valor_estimado)}
                          </span>
                        </td>
                        <td>
                          <span className={
                            `etiqueta-situacao ${despesa.ativo ? 'situacao-ativa' : 'situacao-inativa'}`
                          }>
                            <span aria-hidden="true" />
                            {despesa.ativo ? 'Ativa' : 'Inativa'}
                          </span>
                        </td>
                        <td className="coluna-acao">
                          <div className="acoes-despesa">
                            <button
                              type="button"
                              className="botao-texto acao-lancar"
                              title="Lançar"
                              aria-label={`Lançar: ${despesa.descricao}`}
                              onClick={() => setModal({ tipo: 'lancamento', despesa })}
                            >
                              Lançar
                            </button>
                            <button
                              type="button"
                              className="botao-texto"
                              title="Editar"
                              aria-label={`Editar: ${despesa.descricao}`}
                              onClick={() => setModal({ tipo: 'editar', despesa })}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className="botao-texto"
                              title={despesa.ativo ? 'Inativar' : 'Despesa já inativa'}
                              aria-label={`Inativar: ${despesa.descricao}`}
                              disabled={!despesa.ativo}
                              onClick={() => setModal({ tipo: 'inativar', despesa })}
                            >
                              Inativar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="estado-vazio">
                <h3>Nenhuma despesa encontrada</h3>
                <p>Não há despesas para a competência e os filtros selecionados.</p>
              </div>
            )}
            {resultado.semEstimativa > 0 && (
              <p className="rodape-estimativa">
                {resultado.semEstimativa} {resultado.semEstimativa === 1
                  ? 'despesa sem valor estimado não entra'
                  : 'despesas sem valor estimado não entram'} no total.
              </p>
            )}
          </section>
        )}
      </div>

      {dados && (modal?.tipo === 'nova' || modal?.tipo === 'editar') && (
        <FormularioDespesa
          dados={dados}
          mes={filtrosAplicados.mes}
          despesa={modal.despesa}
          onFechar={() => setModal(null)}
          onSalvo={() => concluir(modal.tipo === 'editar' ? 'Despesa atualizada.' : 'Despesa cadastrada.')}
        />
      )}
      {dados && modal?.tipo === 'lancamento' && (
        <FormularioLancamento
          despesas={despesas}
          despesa={modal.despesa}
          mes={filtrosAplicados.mes}
          onFechar={() => setModal(null)}
          onSalvo={(registro) => concluir(
            `Lançamento salvo em ${formatarMes(registro.mes_referencia.slice(0, 7))}.`,
          )}
        />
      )}
      {dados && modal?.tipo === 'inativar' && (
        <ConfirmarInativacao
          despesa={modal.despesa}
          onFechar={() => setModal(null)}
          onConfirmado={() => concluir('Despesa inativada.')}
        />
      )}
    </Layout>
  )
}
