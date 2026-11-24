import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import { carregarAnalise } from '../services/api.js'
import {
  dataLocalHoje,
  deslocarMes,
  formatarMes,
  formatarPercentual,
  formatarValor,
} from '../utils/formatacao.js'

const situacoes = {
  sem_lancamento: { nome: 'Sem lançamento', classe: 'situacao-inativa' },
  dentro_do_estimado: { nome: 'Dentro do estimado', classe: 'situacao-ativa' },
  acima_do_estimado: { nome: 'Acima do estimado', classe: 'situacao-excedente' },
  nota_pendente: { nome: 'Nota pendente', classe: 'situacao-nota-pendente' },
}

export default function Analise() {
  const [mes, setMes] = useState(() => dataLocalHoje().slice(0, 7))
  const [atualizacao, setAtualizacao] = useState(0)
  const [consulta, setConsulta] = useState({ chave: '', dados: null, erro: '' })
  const chaveConsulta = `${mes}:${atualizacao}`
  const carregando = consulta.chave !== chaveConsulta
  const dados = carregando ? null : consulta.dados
  const erro = carregando ? '' : consulta.erro

  useEffect(() => {
    // Cancela a consulta ao mudar de competência ou sair da tela.
    const controle = new AbortController()
    carregarAnalise(mes, controle.signal)
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

  function trocarMes(novoMes) {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(novoMes) || novoMes.startsWith('0000'))
      return
    setMes(novoMes)
  }

  // Formata os indicadores calculados pela API.
  const indicadores = [
    { nome: 'Total estimado', valor: dados ? formatarValor(dados.total_estimado) : '—', detalhe: 'Cadastro ou média histórica' },
    { nome: 'Total realizado', valor: dados ? formatarValor(dados.total_realizado) : '—', detalhe: 'Despesas incluídas na análise' },
    { nome: 'Diferença', valor: dados ? formatarValor(dados.diferenca) : '—', detalhe: 'Realizado − estimado' },
    { nome: 'Variação', valor: dados?.variacao_percentual == null ? '—' : formatarPercentual(dados.variacao_percentual), detalhe: 'Diferença em relação ao estimado' },
    { nome: 'Despesas pendentes', valor: dados?.despesas_pendentes ?? '—', detalhe: 'Despesas previstas sem lançamento' },
    { nome: 'Notas pendentes', valor: dados?.notas_pendentes ?? '—', detalhe: 'Lançamentos com nota pendente' },
  ]

  return (
    <Layout pagina="analise">
      <div className="pagina-analise">
        <header className="cabecalho-pagina">
          <div>
            <p className="sobretitulo">ACOMPANHAMENTO MENSAL</p>
            <h1>Análise da competência<span className="ponto-titulo">.</span></h1>
          </div>
        </header>

        <section className="filtros" aria-label="Competência da análise">
          <div className="filtro-competencia">
            <label htmlFor="competencia">Competência</label>
            <div className="controle-mes">
              <button
                type="button"
                className="botao-texto"
                aria-label="Competência anterior"
                disabled={mes === '0001-01'}
                onClick={() => trocarMes(deslocarMes(mes, -1))}
              >Anterior</button>
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
              >Próxima</button>
            </div>
          </div>
          <p className="filtro-contexto">
            <span>Competência selecionada<br /><strong>{formatarMes(mes)}</strong></span>
          </p>
        </section>

        {dados?.despesas_excluidas > 0 && (
          <p className="aviso-estimativa-analise" role="status">
            {dados.despesas_excluidas === 1
              ? '1 despesa ficou fora da análise'
              : `${dados.despesas_excluidas} despesas ficaram fora da análise`}{' '}
            por falta de estimativa cadastrada e de lançamentos ativos nos três meses anteriores.
          </p>
        )}

        <section className="indicadores indicadores-analise" aria-label="Resumo da análise" aria-busy={carregando}>
          {indicadores.map((indicador) => (
            <article className="indicador" key={indicador.nome}>
              <div className="indicador-cabecalho"><span>{indicador.nome}</span></div>
              <div className="indicador-valor">{indicador.valor}</div>
              <p className="indicador-detalhe">{indicador.detalhe}</p>
            </article>
          ))}
        </section>

        <section aria-labelledby="titulo-detalhamento" aria-busy={carregando}>
          <div className="cabecalho-lista">
            <h2 id="titulo-detalhamento">
              Detalhamento por despesa{' '}
              {dados && <span className="contador">{dados.despesas.length}</span>}
            </h2>
          </div>
          {carregando ? (
            <div className="estado-carregando" role="status">
              <div className="esqueleto esqueleto-titulo" />
              {[0, 1, 2].map((indice) => <div key={indice} className="esqueleto esqueleto-linha" />)}
              <span className="somente-leitor">Carregando análise da competência…</span>
            </div>
          ) : erro ? (
            <div className="estado-vazio" role="alert">
              <h3>Não foi possível carregar a análise</h3>
              <p>{erro}</p>
              <button type="button" className="botao secundario" onClick={() => setAtualizacao((valor) => valor + 1)}>
                Tentar novamente
              </button>
            </div>
          ) : dados.despesas.length === 0 ? (
            <div className="estado-vazio">
              <h3>{dados.despesas_excluidas > 0 ? 'Nenhuma despesa com estimativa disponível' : 'Nenhuma despesa nesta competência'}</h3>
              <p>{dados.despesas_excluidas > 0
                ? 'As despesas desta competência ainda não têm valor estimado cadastrado nem histórico nos três meses anteriores.'
                : `Não há despesas previstas nem lançamentos ativos em ${formatarMes(mes)}.`}</p>
            </div>
          ) : (
            <>
              <div className="grupo-despesas">
                <div className="tabela-rolagem" tabIndex={0} role="region" aria-label="Análise das despesas da competência">
                  <table className="tabela-despesas tabela-analise">
                    <thead>
                      <tr>
                        <th scope="col">Fornecedor / despesa</th>
                        <th scope="col">Departamento</th>
                        <th scope="col" className="coluna-valor">Estimado</th>
                        <th scope="col" className="coluna-valor">Realizado</th>
                        <th scope="col" className="coluna-valor">Diferença</th>
                        <th scope="col" className="coluna-valor">Variação</th>
                        <th scope="col">Situação</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dados.despesas.map((despesa) => (
                        <tr key={despesa.despesa_recorrente_id}>
                          <td>
                            <strong className="fornecedor-nome">{despesa.fornecedor}</strong>
                            <span className="despesa-descricao">{despesa.descricao}</span>
                          </td>
                          <td>{despesa.departamento}</td>
                          <td className="coluna-valor">
                            {formatarValor(despesa.valor_estimado)}
                            <span className="despesa-descricao">
                              {despesa.origem_estimativa === 'media_historica'
                                ? `Média de ${despesa.meses_historico} ${despesa.meses_historico === 1 ? 'mês' : 'meses'}`
                                : 'Cadastro'}
                            </span>
                          </td>
                          <td className="coluna-valor"><strong className="valor-despesa">{formatarValor(despesa.valor_realizado)}</strong></td>
                          <td className="coluna-valor">{despesa.diferenca == null ? '—' : formatarValor(despesa.diferenca)}</td>
                          <td className="coluna-valor">{despesa.variacao_percentual == null ? '—' : formatarPercentual(despesa.variacao_percentual)}</td>
                          <td>
                            <div className="situacoes-analise">
                              {despesa.situacoes.map((situacao) => (
                                <span className={`etiqueta-situacao ${situacoes[situacao].classe}`} key={situacao}>
                                  <span aria-hidden="true" />{situacoes[situacao].nome}
                                </span>
                              ))}
                              {despesa.situacoes.length === 0 && '—'}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </Layout>
  )
}
