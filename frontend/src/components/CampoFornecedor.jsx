import { useEffect, useId, useRef, useState } from 'react'
import { formatarCnpj } from '../utils/cadastros.js'
import { normalizarTexto } from '../utils/despesas.js'

function nomeFornecedor(fornecedor) {
  return `${fornecedor.nome}${fornecedor.ativo ? '' : ' (inativo)'}`
}

export default function CampoFornecedor({ registros, valor }) {
  const id = useId()
  const campo = useRef(null)
  const lista = useRef(null)
  const [selecionado, setSelecionado] = useState(
    () => registros.find((registro) => registro.id === valor) ?? null,
  )
  const [busca, setBusca] = useState(
    () => selecionado ? nomeFornecedor(selecionado) : '',
  )
  const [aberto, setAberto] = useState(false)
  const [indice, setIndice] = useState(-1)
  const termo = normalizarTexto(busca)
  const resultados = registros.filter(
    (registro) => selecionado || normalizarTexto(registro.nome).includes(termo),
  )

  useEffect(() => {
    campo.current.setCustomValidity(
      busca && !selecionado ? 'Selecione um fornecedor da lista.' : '',
    )
  }, [busca, selecionado])

  useEffect(() => {
    lista.current?.children[indice]?.scrollIntoView({ block: 'nearest' })
  }, [indice])

  function selecionar(fornecedor) {
    setSelecionado(fornecedor)
    setBusca(nomeFornecedor(fornecedor))
    setAberto(false)
    setIndice(-1)
  }

  function navegar(evento) {
    if (evento.key === 'Escape' && aberto) {
      evento.preventDefault()
      evento.stopPropagation()
      setAberto(false)
      setIndice(-1)
    } else if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
      evento.preventDefault()
      setAberto(true)
      if (!resultados.length) return
      setIndice((atual) => evento.key === 'ArrowDown'
        ? (atual + 1) % resultados.length
        : (atual <= 0 ? resultados.length - 1 : atual - 1))
    } else if (evento.key === 'Enter' && aberto) {
      evento.preventDefault()
      if (resultados[indice]) selecionar(resultados[indice])
    }
  }

  return (
    <div className="campo campo-fornecedor">
      <label htmlFor={id}>Fornecedor</label>
      <input
        ref={campo}
        id={id}
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={aberto}
        aria-controls={`${id}-opcoes`}
        aria-activedescendant={
          aberto && resultados[indice] ? `${id}-opcao-${resultados[indice].id}` : undefined
        }
        autoComplete="off"
        placeholder="Digite o nome do fornecedor"
        required
        value={busca}
        onChange={(evento) => {
          setBusca(evento.target.value)
          // Limpa a seleção para não enviar o ID do fornecedor anterior.
          setSelecionado(null)
          setAberto(true)
          setIndice(-1)
        }}
        onFocus={() => setAberto(true)}
        onBlur={() => {
          setAberto(false)
          setIndice(-1)
        }}
        onKeyDown={navegar}
      />
      <input type="hidden" name="fornecedor_id" value={selecionado?.id ?? ''} />
      {aberto && (
        <div className="fornecedor-sugestoes">
          <ul ref={lista} id={`${id}-opcoes`} role="listbox" aria-label="Fornecedores">
            {resultados.map((fornecedor, posicao) => (
              <li key={fornecedor.id} role="presentation">
                <button
                  id={`${id}-opcao-${fornecedor.id}`}
                  type="button"
                  role="option"
                  aria-selected={selecionado?.id === fornecedor.id}
                  className={indice === posicao ? 'fornecedor-opcao destacada' : 'fornecedor-opcao'}
                  tabIndex={-1}
                  onMouseDown={(evento) => evento.preventDefault()}
                  onClick={() => selecionar(fornecedor)}
                >
                  <span>{nomeFornecedor(fornecedor)}</span>
                  {fornecedor.cnpj ? (
                    <small>{formatarCnpj(fornecedor.cnpj)}</small>
                  ) : registros.some((outro) => outro.id !== fornecedor.id
                    && normalizarTexto(outro.nome) === normalizarTexto(fornecedor.nome)) && (
                    <small>Cadastro nº {fornecedor.id}</small>
                  )}
                </button>
              </li>
            ))}
          </ul>
          {!resultados.length && (
            <p className="fornecedor-sem-resultados" role="status">
              Nenhum fornecedor encontrado.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
