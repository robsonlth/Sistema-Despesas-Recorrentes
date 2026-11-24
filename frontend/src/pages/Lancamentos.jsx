import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import DetalhesRateio from '../components/DetalhesRateio.jsx'
import FormularioLancamento from '../components/FormularioLancamento.jsx'
import ConfirmarInativacao from '../components/ConfirmarInativacao.jsx'
import ConfirmarExclusaoLancamento from '../components/ConfirmarExclusaoLancamento.jsx'
import { carregarLancamentos } from '../services/api.js'
import { prepararLancamentos } from '../utils/lancamentos.js'
import { dataLocalHoje, formatarData, formatarMes, formatarValor } from '../utils/formatacao.js'

export default function Lancamentos() {
  const [filtros, setFiltros] = useState(() => ({
    busca: '',
    mes: dataLocalHoje().slice(0, 7),
    departamento: '',
    natureza: '',
    situacao: 'ativos',
    etapa: 'todos',
  }))
  const [filtrosAplicados, setFiltrosAplicados] = useState(filtros)
  const [atualizacao, setAtualizacao] = useState(0)
  const [consulta, setConsulta] = useState({ chave: '', dados: null, erro: '' })
  const [modal, setModal] = useState(null)
  const [mensagem, setMensagem] = useState('')
  const mes = filtrosAplicados.mes
  const chaveConsulta = `${mes}:${atualizacao}`
  const carregando = consulta.chave !== chaveConsulta
  const dados = carregando ? null : consulta.dados
  const erro = carregando ? '' : consulta.erro
  const resultado = dados ? prepararLancamentos(dados, filtrosAplicados) : null

  useEffect(() => {
    // Cancela a consulta ao mudar de competência ou sair da tela.
    const controle = new AbortController()
    carregarLancamentos(mes, controle.signal)
      .then((resposta) => {
        if (!controle.signal.aborted) {
          setConsulta({ chave: chaveConsulta, dados: resposta, erro: '' })
        }
      })
      .catch((falha) => {
        if (!controle.signal.aborted) {
          setConsulta({ chave: chaveConsulta, dados: null, erro: falha.message })
        }
      })
    return () => controle.abort()
  }, [mes, chaveConsulta])

  function alterarFiltro(evento) {
    const { name, value } = evento.target
    setFiltros((anteriores) => ({ ...anteriores, [name]: value }))
  }

  function filtrar(evento) {
    evento.preventDefault()
    setFiltrosAplicados({ ...filtros })
    setMensagem('')
  }

  function voltarCompetenciaAtual() {
    const novosFiltros = { ...filtros, mes: dataLocalHoje().slice(0, 7) }
    setFiltros(novosFiltros)
    setFiltrosAplicados(novosFiltros)
    setMensagem('')
  }

  function concluirLancamento(registro) {
    // Usa a competência calculada pela API, inclusive quando a data foi editada.
    const novosFiltros = { ...filtrosAplicados, mes: registro.mes_referencia.slice(0, 7) }
    setFiltros(novosFiltros)
    setFiltrosAplicados(novosFiltros)
    setModal(null)
    setMensagem(`Lançamento salvo em ${formatarMes(novosFiltros.mes)}.`)
    setAtualizacao((valor) => valor + 1)
  }

  function concluirInativacao() {
    setModal(null)
    setMensagem('Lançamento inativado.')
    setAtualizacao((valor) => valor + 1)
  }

  function concluirExclusao() {
    setModal(null)
    setMensagem('Lançamento excluído definitivamente.')
    setAtualizacao((valor) => valor + 1)
  }

  return (
    <Layout pagina="lancamentos">
      <div className="pagina-lancamentos">
        <header className="cabecalho-pagina">
          <div>
            <p className="sobretitulo">GESTÃO DE DESPESAS</p>
            <h1>Lançamentos<span className="ponto-titulo">.</span></h1>
          </div>
          <div className="acoes-cabecalho-lancamentos">
            <button type="button" className="botao secundario" onClick={voltarCompetenciaAtual}>
              Competência atual
            </button>
            <button
              type="button"
              className="botao primario"
              disabled={!dados}
              onClick={() => setModal({ tipo: 'novo' })}
            >
              Novo lançamento
            </button>
          </div>
        </header>

        <form
          className="filtros filtros-recorrentes filtros-lancamentos"
          aria-label="Filtros de lançamentos"
          onSubmit={filtrar}
        >
          <div className="filtro-busca">
            <label htmlFor="busca-lancamentos">Buscar lançamento ou fornecedor</label>
            <div className="controle-busca">
              <input
                id="busca-lancamentos"
                name="busca"
                type="search"
                placeholder="Digite para buscar…"
                value={filtros.busca}
                onChange={alterarFiltro}
              />
            </div>
          </div>
          <div className="filtro-competencia">
            <label htmlFor="mes-lancamentos">Competência</label>
            <div className="controle-mes">
              <input
                id="mes-lancamentos"
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
            <label htmlFor="departamento-lancamentos">Tipo de despesa / departamento</label>
            <select
              id="departamento-lancamentos"
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
            <label htmlFor="situacao-lancamentos">Exibir registros</label>
            <select
              id="situacao-lancamentos"
              name="situacao"
              value={filtros.situacao}
              onChange={alterarFiltro}
            >
              <option value="ativos">Ativos</option>
              <option value="inativos">Inativos</option>
              <option value="todos">Todos</option>
            </select>
          </div>
          <div className="filtro-departamento">
            <label htmlFor="natureza-lancamentos">Natureza financeira</label>
            <select
              id="natureza-lancamentos"
              name="natureza"
              value={filtros.natureza}
              onChange={alterarFiltro}
              disabled={!dados}
            >
              <option value="">Todas as naturezas</option>
              {dados?.naturezas.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}{item.ativo ? '' : ' (inativa)'}
                </option>
              ))}
            </select>
          </div>
          <div className="filtro-departamento">
            <label htmlFor="etapa-lancamentos">Etapa do lançamento</label>
            <select
              id="etapa-lancamentos"
              name="etapa"
              value={filtros.etapa}
              onChange={alterarFiltro}
            >
              <option value="todos">Todos</option>
              <option value="pendentes">Pendentes de lançamento</option>
              <option value="nota-pendente">Nota fiscal pendente</option>
              <option value="sem-nota-pendente">Sem nota fiscal pendente</option>
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
            <span className="somente-leitor">Carregando lançamentos…</span>
            <div className="esqueleto esqueleto-titulo" />
            {[1, 2, 3].map((item) => <div key={item} className="esqueleto esqueleto-linha" />)}
          </div>
        ) : erro ? (
          <div className="estado-vazio" role="alert">
            <h3>Não foi possível carregar os lançamentos</h3>
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
          <>
            {resultado.exibirPendentes && (
              <section className="grupo-despesas lista-recorrentes" aria-labelledby="titulo-sem-lancamento">
                <header className="resumo-recorrentes" aria-live="polite" aria-atomic="true">
                  <div>
                    <h2 id="titulo-sem-lancamento">
                      Pendentes de lançamento · {resultado.pendentes.length}
                    </h2>
                    <p>{formatarMes(mes)}</p>
                  </div>
                </header>
                {resultado.pendentes.length ? (
                  <>
                    <div className="tabela-rolagem" role="region" aria-label="Despesas sem lançamento" tabIndex={0}>
                      <table className="tabela-despesas tabela-pendentes-lancamento">
                        <caption className="somente-leitor">Despesas pendentes de lançamento em {formatarMes(mes)}</caption>
                        <thead>
                          <tr>
                            <th scope="col">Fornecedor</th>
                            <th scope="col">Despesa</th>
                            <th scope="col">Natureza financeira</th>
                            <th scope="col">Rateios / vencimento</th>
                            <th scope="col" className="coluna-valor">Valor estimado<sup>*</sup></th>
                            <th scope="col" className="coluna-acao">Ações</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultado.pendentes.map((despesa) => (
                            <tr
                              key={despesa.id}
                              className={despesa.vencimento.vencido ? 'vencimento-atrasado'
                                : despesa.vencimento.proximo ? 'vencimento-proximo' : undefined}
                            >
                              <td><strong className="fornecedor-nome">{despesa.fornecedor}</strong></td>
                              <td>
                                <span className="descricao-recorrente">{despesa.descricao}</span>
                                <span className="detalhe-recorrente">{despesa.departamento}</span>
                              </td>
                              <td>{despesa.natureza}</td>
                              <td><DetalhesRateio despesa={despesa} vencimento={despesa.vencimento} /></td>
                              <td className="coluna-valor">
                                <strong className={despesa.valor_estimado === null ? 'valor-ausente' : 'valor-despesa'}>
                                  {formatarValor(despesa.valor_estimado)}
                                </strong>
                              </td>
                              <td className="coluna-acao">
                                <button
                                  type="button"
                                  className="botao botao-lancar"
                                  aria-label={`Lançar ${despesa.descricao} — ${despesa.fornecedor}`}
                                  onClick={() => setModal({ tipo: 'novo', despesa })}
                                >
                                  Lançar
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <p className="rodape-estimativa">
                      * Valor estimado informado no cadastro da despesa.
                    </p>
                  </>
                ) : (
                  <p className="lista-lancamentos-vazia">
                    Nenhuma despesa pendente de lançamento para estes filtros.
                  </p>
                )}
              </section>
            )}

            {resultado.exibirRegistros && (
              <section className="grupo-despesas lista-recorrentes" aria-labelledby="titulo-lancamentos">
                <header className="resumo-recorrentes" aria-live="polite" aria-atomic="true">
                  <div>
                    <h2 id="titulo-lancamentos">
                      {resultado.registros.length}{' '}
                      {resultado.registros.length === 1 ? 'lançamento encontrado' : 'lançamentos encontrados'}
                    </h2>
                    <p>{formatarMes(mes)}</p>
                  </div>
                </header>
                {resultado.registros.length ? (
                  <div className="tabela-rolagem" role="region" aria-label="Lançamentos registrados" tabIndex={0}>
                    <table className="tabela-despesas tabela-lancamentos">
                      <caption className="somente-leitor">Lançamentos registrados em {formatarMes(mes)}</caption>
                      <thead>
                        <tr>
                          <th scope="col">Fornecedor / despesa</th>
                          <th scope="col">Tipo de despesa / departamento</th>
                          <th scope="col">Recebimento</th>
                          <th scope="col" className="coluna-valor">Valor recebido</th>
                          <th scope="col">Situação / nota fiscal</th>
                          <th scope="col" className="coluna-acao">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {resultado.registros.map((registro) => (
                          <tr key={registro.id}>
                            <td>
                              <strong className="fornecedor-nome">
                                {registro.despesa?.fornecedor || 'Fornecedor não encontrado'}
                              </strong>
                              <span className="despesa-descricao descricao-recorrente">
                                {registro.despesa?.descricao || 'Despesa não encontrada'}
                              </span>
                              {registro.observacao && (
                                <span className="observacao-lancamento">
                                  Observação: {registro.observacao}
                                </span>
                              )}
                            </td>
                            <td>
                              <span className="etiqueta-rateio etiqueta-departamento">
                                {registro.despesa?.departamento || 'Não informado'}
                              </span>
                              <span className="detalhe-recorrente">
                                <span>Natureza:</span> {registro.despesa?.natureza || 'Não informada'}
                              </span>
                              <DetalhesRateio despesa={registro.despesa} />
                            </td>
                            <td>
                              <time dateTime={registro.data_recebimento}>
                                {formatarData(registro.data_recebimento)}
                              </time>
                              <span className="despesa-contrato">Lançamento #{registro.id}</span>
                            </td>
                            <td className="coluna-valor">
                              <strong className="valor-despesa">{formatarValor(registro.valor_recebido)}</strong>
                            </td>
                            <td>
                              <div className="situacao-lancamento">
                                <span className={`etiqueta-situacao ${registro.ativo ? 'situacao-ativa' : 'situacao-inativa'}`}>
                                  <span aria-hidden="true" />
                                  {registro.ativo ? 'Ativo' : 'Inativo'}
                                </span>
                                {registro.nota_pendente ? (
                                  <span className="etiqueta-situacao nota-pendente">Nota fiscal pendente</span>
                                ) : (
                                  <span className="nota-regular">Sem nota fiscal pendente</span>
                                )}
                              </div>
                            </td>
                            <td className="coluna-acao">
                              <div className="acoes-despesa">
                                <button
                                  type="button"
                                  className="botao-texto"
                                  title="Editar"
                                  aria-label={`Editar lançamento ${registro.id}`}
                                  onClick={() => setModal({ tipo: 'editar', lancamento: registro })}
                                >
                                  Editar
                                </button>
                                <button
                                  type="button"
                                  className="botao-texto"
                                  title={registro.ativo ? 'Inativar' : 'Lançamento já inativo'}
                                  aria-label={`Inativar lançamento ${registro.id}`}
                                  disabled={!registro.ativo}
                                  onClick={() => setModal({ tipo: 'inativar', lancamento: registro })}
                                >
                                  Inativar
                                </button>
                                <button
                                  type="button"
                                  className="botao-texto acao-excluir"
                                  aria-label={`Excluir lançamento ${registro.id}`}
                                  onClick={() => setModal({ tipo: 'excluir', lancamento: registro })}
                                >
                                  Excluir
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
                    <h3>Nenhum lançamento encontrado</h3>
                    <p>Não há lançamentos para a competência e os filtros selecionados.</p>
                  </div>
                )}
              </section>
            )}
          </>
        )}
      </div>

      {dados && (modal?.tipo === 'novo' || modal?.tipo === 'editar') && (
        <FormularioLancamento
          despesas={resultado.despesas}
          despesa={modal.despesa}
          lancamento={modal.lancamento}
          mes={mes}
          onFechar={() => setModal(null)}
          onSalvo={concluirLancamento}
        />
      )}
      {dados && modal?.tipo === 'inativar' && (
        <ConfirmarInativacao
          despesa={modal.lancamento.despesa}
          lancamento={modal.lancamento}
          onFechar={() => setModal(null)}
          onConfirmado={concluirInativacao}
        />
      )}
      {dados && modal?.tipo === 'excluir' && (
        <ConfirmarExclusaoLancamento
          lancamento={modal.lancamento}
          onFechar={() => setModal(null)}
          onConfirmado={concluirExclusao}
        />
      )}
    </Layout>
  )
}
