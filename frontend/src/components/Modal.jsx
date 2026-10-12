import { useEffect, useRef } from 'react'

export default function Modal({
  titulo,
  descricao,
  ocupado = false,
  onFechar,
  children,
}) {
  const referencia = useRef(null)

  // Abre a janela quando ela aparece e fecha quando sai da tela.
  useEffect(() => {
    const dialogo = referencia.current
    dialogo.showModal()
    return () => dialogo.close()
  }, [])

  return (
    <dialog
      ref={referencia}
      className="modal"
      aria-labelledby="modal-titulo"
      aria-describedby="modal-descricao"
      onCancel={(evento) => {
        // Impede que a tecla Esc feche o formulário durante o envio.
        evento.preventDefault()
        if (!ocupado) onFechar()
      }}
    >
      <header className="modal-cabecalho">
        <div>
          <h2 id="modal-titulo">{titulo}</h2>
          <p id="modal-descricao">{descricao}</p>
        </div>
        <button
          type="button"
          className="botao-texto"
          aria-label="Fechar janela"
          disabled={ocupado}
          onClick={onFechar}
        >
          Fechar
        </button>
      </header>
      {children}
    </dialog>
  )
}
