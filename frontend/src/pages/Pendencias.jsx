import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import Modal from '../components/Modal.jsx'
import FormularioLancamento from '../components/FormularioLancamento.jsx'
import { carregarPendencias } from '../services/api.js'
import { prepararAcompanhamento } from '../utils/acompanhamento.js'
import {
  dataLocalHoje,
  deslocarMes,
  formatarData,
  formatarMes,
  formatarValor,
} from '../utils/formatacao.js'

// Controla os filtros, a consulta dos dados e os formulários da tela.
export default function Pendencias() {
  const [mes, setMes] = useState(() => dataLocalHoje().slice(0, 7))
  const [departamento, setDepartamento] = useState('')
  const [atualizacao, setAtualizacao] = useState(0)
  const [consulta, setConsulta] = useState({ chave: '', dados: null, erro: '' })
  const [modal, setModal] = useState(null)
  const [mensagem, setMensagem] = useState('')

  // Identifica a consulta atual para não exibir dados do mês anterior.
  const chaveConsulta = `${mes}:${atualizacao}`
  const carregando = consulta.chave !== chaveConsulta
  const dados = carregando ? null : consulta.dados
  const erro = carregando ? '' : consulta.erro

  useEffect(() => {
    // Cancela a consulta antiga ao mudar de mês ou sair da tela.
    const controle = new AbortController()
    carregarPendencias(mes, controle.signal)
      .then((resposta) => {
        if (!controle.signal.aborted) {
          setConsulta({ chave: chaveConsulta, dados: resposta, erro: '' })
        }
      })
      .catch((falha) => {
        if (!controle.signal.aborted) {
          setConsulta({
            chave: chaveConsulta,
            dados: null,
            erro: falha.message,
          })
        }
      })
    return () => controle.abort()
  }, [mes, chaveConsulta])

  const acompanhamento = dados
    ? prepararAcompanhamento(dados, mes, departamento)
    : null

  function trocarMes(novoMes) {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(novoMes) || novoMes.startsWith('0000'))
      return
    setMes(novoMes)
    setMensagem('')
  }

  function concluirLancamento(registro) {
    setModal(null)
    setMes(registro.mes_referencia.slice(0, 7))
    setMensagem(
      `Lançamento salvo em ${formatarMes(registro.mes_referencia.slice(0, 7))}.`,
    )
    // Consulta os dados novamente depois de salvar.
    setAtualizacao((valor) => valor + 1)
  }

  return (
    <Layout>
      <div id="pendencias" className="pagina-pendencias">
        <header className="cabecalho-pagina">
          <div>
            <p className="sobretitulo">ACOMPANHAMENTO MENSAL</p>
            <h1>
              Despesas pendentes<span className="ponto-titulo">.</span>
            </h1>
          </div>
        </header>

        <section className="filtros" aria-label="Filtros de despesas">
          <div className="filtro-competencia">
            <label htmlFor="competencia">Competência</label>
            <div className="controle-mes">
              <button
                type="button"
                className="botao-texto"
                aria-label="Competência anterior"
                disabled={mes === '0001-01'}
                onClick={() => trocarMes(deslocarMes(mes, -1))}
              >
                Anterior
              </button>
              <input
                id="competencia"
                type="month"
                min="0001-01"
                max="9999-12"
                value={mes}
                onChange={(evento) => trocarMes(evento.target.value)}
              />
              <button
                type="button"
                className="botao-texto"
                aria-label="Próxima competência"
                disabled={mes === '9999-12'}
                onClick={() => trocarMes(deslocarMes(mes, 1))}
              >
                Próxima
              </button>
            </div>
          </div>
          <div className="filtro-departamento">
            <label htmlFor="departamento">Tipo de despesa/Departamento</label>
            <select
              id="departamento"
              value={departamento}
              disabled={!dados}
              onChange={(evento) => setDepartamento(evento.target.value)}
            >
              <option value="">Todos os tipos</option>
              {dados?.departamentos.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome}
                  {item.ativo ? '' : ' (inativo)'}
                </option>
              ))}
            </select>
          </div>
          <p className="filtro-contexto">
            <span>
              Visão da competência
              <br />
              <strong>{formatarMes(mes)}</strong>
            </span>
          </p>
        </section>

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

        <section
          className="indicadores"
          aria-label="Resumo da competência"
          aria-busy={carregando}
        >
          <article className="indicador">
            <div className="indicador-cabecalho">
              <span>Despesas sem lançamento</span>
            </div>
            <div className="indicador-valor">
              {acompanhamento?.pendentes.length ?? '—'}
              <span>pendentes</span>
            </div>
          </article>
          <article className="indicador">
            <div className="indicador-cabecalho">
              <span>Progresso de lançamentos</span>
            </div>
            <div className="progresso-numeros">
              <strong>
                {acompanhamento
                  ? `${acompanhamento.lancadas} de ${acompanhamento.total}`
                  : '—'}
                <span>despesas lançadas</span>
              </strong>
              <span className="percentual">
                {acompanhamento ? `${acompanhamento.percentual}%` : '—'}
              </span>
            </div>
            <progress
              max="100"
              value={acompanhamento?.percentual ?? 0}
              aria-label={
                acompanhamento
                  ? `${acompanhamento.lancadas} de ${acompanhamento.total} despesas previstas com lançamento`
                  : 'Aguardando dados'
              }
            />
          </article>
          <button
            type="button"
            className="indicador indicador-notas"
            aria-haspopup="dialog"
            disabled={!dados}
            onClick={() => setModal({ tipo: 'notas' })}
          >
            <div className="indicador-cabecalho">
              <span>Notas pendentes</span>
            </div>
            <div className="indicador-valor">
              {acompanhamento?.notas.length ?? '—'}
              <span>nota(s) pendente(s)</span>
            </div>
          </button>
        </section>

        <section
          aria-labelledby="titulo-lista"
          aria-busy={carregando}
        >
          <div className="cabecalho-lista">
            <h2 id="titulo-lista">
              Aguardando lançamento{' '}
              {acompanhamento && (
                <span className="contador">
                  {acompanhamento.pendentes.length}
                </span>
              )}
            </h2>
          </div>
          {carregando ? (
            <div className="estado-carregando" role="status">
              <div className="esqueleto esqueleto-titulo" />
              {[0, 1, 2].map((indice) => (
                <div key={indice} className="esqueleto esqueleto-linha" />
              ))}
              <span className="somente-leitor">
                Carregando despesas da competência…
              </span>
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
          ) : acompanhamento.grupos.length === 0 ? (
            <div className="estado-vazio">
              <h3>
                {acompanhamento.total
                  ? 'Tudo em dia nesta competência'
                  : 'Nenhuma despesa prevista'}
              </h3>
              <p>
                {acompanhamento.total
                  ? 'Todas as despesas previstas já têm um lançamento registrado.'
                  : 'Não há despesas previstas para o filtro selecionado.'}
              </p>
            </div>
          ) : (
            acompanhamento.grupos.map((grupo) => (
              <section
                className="grupo-despesas"
                key={grupo.id}
                aria-labelledby={`grupo-${grupo.id}`}
              >
                <header className="grupo-cabecalho">
                  <div>
                    <h3 id={`grupo-${grupo.id}`}>{grupo.nome}</h3>
                    <span className="contador">{grupo.despesas.length}</span>
                  </div>
                  <span>
                    {grupo.despesas.length === 1
                      ? '1 despesa pendente'
                      : `${grupo.despesas.length} despesas pendentes`}
                  </span>
                </header>
                <div className="tabela-rolagem">
                  <table className="tabela-despesas">
                    <thead>
                      <tr>
                        <th scope="col">Fornecedor / Despesa</th>
                        <th scope="col">Natureza</th>
                        <th scope="col">Rateio</th>
                        <th scope="col" className="coluna-valor">
                          Valor médio estimado<sup>*</sup>
                        </th>
                        <th scope="col">
                          <span className="somente-leitor">Ações</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {grupo.despesas.map((despesa) => (
                        <tr key={despesa.id}>
                          <td>
                            <strong className="fornecedor-nome">
                              {despesa.fornecedor}
                            </strong>
                            <span className="despesa-descricao">
                              {despesa.descricao}
                            </span>
                            <span className="despesa-contrato">
                              Contrato:{' '}
                              <span aria-label="Não informado">—</span>
                            </span>
                          </td>
                          <td>{despesa.natureza}</td>
                          <td>
                            <span className="etiqueta-rateio">
                              {despesa.rateio}
                            </span>
                          </td>
                          <td className="coluna-valor">
                            <strong
                              className={
                                despesa.valor_estimado == null
                                  ? 'valor-ausente'
                                  : 'valor-despesa'
                              }
                            >
                              {formatarValor(despesa.valor_estimado)}
                            </strong>
                          </td>
                          <td className="coluna-acao">
                            <button
                              type="button"
                              className="botao botao-lancar"
                              aria-label={`Lançar ${despesa.descricao} — ${despesa.fornecedor}`}
                              onClick={() =>
                                setModal({ tipo: 'lancamento', despesa })
                              }
                            >
                              Lançar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ))
          )}
          {!carregando && !erro && acompanhamento.pendentes.length > 0 && (
            <p className="nota-estimativa">
              * Exibimos o valor estimado cadastrado para a despesa. A média
              histórica não está disponível.
            </p>
          )}
        </section>
      </div>

      {modal?.tipo === 'lancamento' && (
        <FormularioLancamento
          despesas={acompanhamento.despesas}
          despesa={modal.despesa}
          mes={mes}
          onFechar={() => setModal(null)}
          onSalvo={concluirLancamento}
        />
      )}
      {modal?.tipo === 'notas' && (
        <Modal
          titulo="Notas pendentes"
          descricao={`Lançamentos de ${formatarMes(mes)}${departamento ? ` · ${dados.departamentos.find((item) => item.id === Number(departamento))?.nome}` : ''}`}
          onFechar={() => setModal(null)}
        >
          <div className="lista-notas">
            {acompanhamento.notas.length ? (
              acompanhamento.notas.map((nota) => (
                <article className="nota-item" key={nota.id}>
                  <div>
                    <strong>{nota.despesa.fornecedor}</strong>
                    <p>{nota.despesa.descricao}</p>
                    <span>
                      Recebimento em {formatarData(nota.data_recebimento)}
                    </span>
                    {nota.observacao && (
                      <p className="nota-observacao">{nota.observacao}</p>
                    )}
                  </div>
                  <strong>{formatarValor(nota.valor_recebido)}</strong>
                </article>
              ))
            ) : (
              <div className="estado-vazio">
                <h3>Nenhuma nota pendente</h3>
                <p>Não há notas pendentes para os filtros selecionados.</p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </Layout>
  )
}
