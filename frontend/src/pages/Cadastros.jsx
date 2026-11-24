import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import FormularioCadastro from '../components/FormularioCadastro.jsx'
import ConfirmarInativacaoCadastro from '../components/ConfirmarInativacaoCadastro.jsx'
import { carregarCadastros } from '../services/api.js'
import { filtrarCadastros, formatarCnpj, tiposCadastro } from '../utils/cadastros.js'

const filtrosIniciais = { busca: '', situacao: 'ativos' }

export default function Cadastros() {
  const [aba, setAba] = useState('fornecedores')
  const [filtros, setFiltros] = useState(filtrosIniciais)
  const [filtrosAplicados, setFiltrosAplicados] = useState(filtrosIniciais)
  const [atualizacao, setAtualizacao] = useState(0)
  const [consulta, setConsulta] = useState({ versao: -1, dados: null, erro: '' })
  const [modal, setModal] = useState(null)
  const [mensagem, setMensagem] = useState('')
  const tipo = tiposCadastro.find((item) => item.id === aba)
  const carregando = consulta.versao !== atualizacao
  const dados = carregando ? null : consulta.dados
  const erro = carregando ? '' : consulta.erro
  const registros = filtrarCadastros(dados?.[aba] ?? [], filtrosAplicados)

  useEffect(() => {
    const controle = new AbortController()
    carregarCadastros(controle.signal)
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

  function trocarAba(id) {
    if (id === aba) return
    setAba(id)
    setFiltros(filtrosIniciais)
    setFiltrosAplicados(filtrosIniciais)
    setMensagem('')
  }

  function navegarAbas(evento, indice) {
    let proximo
    if (evento.key === 'ArrowRight') proximo = (indice + 1) % tiposCadastro.length
    else if (evento.key === 'ArrowLeft') proximo = (indice - 1 + tiposCadastro.length) % tiposCadastro.length
    else if (evento.key === 'Home') proximo = 0
    else if (evento.key === 'End') proximo = tiposCadastro.length - 1
    else return
    evento.preventDefault()
    const id = tiposCadastro[proximo].id
    trocarAba(id)
    document.getElementById(`aba-${id}`).focus()
  }

  function alterarFiltro(evento) {
    const { name, value } = evento.target
    setFiltros((anteriores) => ({ ...anteriores, [name]: value }))
  }

  function filtrar(evento) {
    evento.preventDefault()
    setFiltrosAplicados({ ...filtros })
    setMensagem('')
  }

  function concluir(texto) {
    setModal(null)
    setMensagem(texto)
    // Refaz a consulta após salvar ou inativar um cadastro.
    setAtualizacao((valor) => valor + 1)
  }

  return (
    <Layout pagina="cadastros">
      <div className="pagina-cadastros">
        <header className="cabecalho-pagina">
          <div>
            <p className="sobretitulo">GESTÃO DE DESPESAS</p>
            <h1>Cadastros<span className="ponto-titulo">.</span></h1>
          </div>
          <button
            type="button"
            className="botao primario"
            disabled={!dados}
            onClick={() => setModal({ tipo: 'novo' })}
          >
            Novo cadastro
          </button>
        </header>

        <div className="abas-cadastros" role="tablist" aria-label="Tipos de cadastro">
          {tiposCadastro.map((item, indice) => (
            <button
              key={item.id}
              id={`aba-${item.id}`}
              type="button"
              role="tab"
              aria-selected={aba === item.id}
              aria-controls="painel-cadastros"
              tabIndex={aba === item.id ? 0 : -1}
              onClick={() => trocarAba(item.id)}
              onKeyDown={(evento) => navegarAbas(evento, indice)}
            >
              {item.titulo}
            </button>
          ))}
        </div>

        <section id="painel-cadastros" role="tabpanel" aria-labelledby={`aba-${aba}`}>
          <form className="filtros filtros-cadastros" aria-label="Filtros de cadastros" onSubmit={filtrar}>
            <div className="filtro-busca">
              <label htmlFor="busca-cadastro">
                {aba === 'fornecedores' ? 'Buscar por nome ou CNPJ' : 'Buscar por nome'}
              </label>
              <div className="controle-busca">
                <input
                  id="busca-cadastro"
                  name="busca"
                  type="search"
                  placeholder="Digite para buscar…"
                  value={filtros.busca}
                  onChange={alterarFiltro}
                />
              </div>
            </div>
            <div className="filtro-departamento">
              <label htmlFor="situacao-cadastro">Situação do cadastro</label>
              <select id="situacao-cadastro" name="situacao" value={filtros.situacao} onChange={alterarFiltro}>
                <option value="ativos">Ativos</option>
                <option value="inativos">Inativos</option>
                <option value="todos">Todos</option>
              </select>
            </div>
            <button type="submit" className="botao secundario" disabled={!dados}>Filtrar</button>
          </form>

          {mensagem && (
            <div className="mensagem-sucesso" role="status">
              <span>{mensagem}</span>
              <button type="button" className="botao-texto" aria-label="Fechar mensagem" onClick={() => setMensagem('')}>
                Fechar
              </button>
            </div>
          )}

          {carregando ? (
            <div className="estado-carregando" role="status" aria-busy="true">
              <span className="somente-leitor">Carregando cadastros…</span>
              <div className="esqueleto esqueleto-titulo" />
              {[1, 2, 3].map((item) => <div key={item} className="esqueleto esqueleto-linha" />)}
            </div>
          ) : erro ? (
            <div className="estado-vazio" role="alert">
              <h3>Não foi possível carregar os cadastros</h3>
              <p>{erro}</p>
              <button type="button" className="botao secundario" onClick={() => setAtualizacao((valor) => valor + 1)}>
                Tentar novamente
              </button>
            </div>
          ) : (
            <section className="grupo-despesas lista-recorrentes" aria-label={tipo.titulo}>
              <header className="resumo-recorrentes" aria-live="polite" aria-atomic="true">
                <div>
                  <h2>{registros.length} {registros.length === 1 ? 'cadastro encontrado' : 'cadastros encontrados'}</h2>
                  <p>{tipo.titulo}</p>
                </div>
              </header>
              {registros.length ? (
                <div className="tabela-rolagem" role="region" aria-label={`Tabela de ${tipo.titulo.toLowerCase()}`} tabIndex={0}>
                  <table className="tabela-despesas tabela-cadastros">
                    <caption className="somente-leitor">{tipo.titulo}</caption>
                    <thead>
                      <tr>
                        <th scope="col">Nome</th>
                        {aba === 'fornecedores' && <th scope="col" className="coluna-cnpj">CNPJ</th>}
                        <th scope="col" className="coluna-situacao">Situação</th>
                        <th scope="col" className="coluna-acao">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {registros.map((registro) => (
                        <tr key={registro.id}>
                          <td><strong className="fornecedor-nome">{registro.nome}</strong></td>
                          {aba === 'fornecedores' && <td>{formatarCnpj(registro.cnpj)}</td>}
                          <td>
                            <span className={`etiqueta-situacao ${registro.ativo ? 'situacao-ativa' : 'situacao-inativa'}`}>
                              {registro.ativo ? 'Ativo' : 'Inativo'}
                            </span>
                          </td>
                          <td className="coluna-acao">
                            <div className="acoes-despesa">
                              <button
                                type="button"
                                className="botao-texto"
                                aria-label={`Editar: ${registro.nome}`}
                                onClick={() => setModal({ tipo: 'editar', cadastro: registro })}
                              >
                                Editar
                              </button>
                              <button
                                type="button"
                                className="botao-texto"
                                aria-label={`Inativar: ${registro.nome}`}
                                disabled={!registro.ativo}
                                title={registro.ativo ? 'Inativar' : 'Cadastro já inativo'}
                                onClick={() => setModal({ tipo: 'inativar', cadastro: registro })}
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
                  <h3>Nenhum cadastro encontrado</h3>
                  <p>Não há registros para os filtros selecionados.</p>
                </div>
              )}
            </section>
          )}
        </section>
      </div>

      {(modal?.tipo === 'novo' || modal?.tipo === 'editar') && (
        <FormularioCadastro
          tipo={tipo}
          cadastro={modal.cadastro}
          onFechar={() => setModal(null)}
          onSalvo={() => concluir(modal.tipo === 'editar' ? 'Cadastro atualizado.' : 'Cadastro criado.')}
        />
      )}
      {modal?.tipo === 'inativar' && (
        <ConfirmarInativacaoCadastro
          tipo={tipo}
          cadastro={modal.cadastro}
          onFechar={() => setModal(null)}
          onConfirmado={() => concluir('Cadastro inativado.')}
        />
      )}
    </Layout>
  )
}
