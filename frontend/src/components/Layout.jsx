import logoCompasso from '../assets/Compasso.png'

const itens = [
  { nome: 'Pendências', pagina: 'pendencias' },
  { nome: 'Despesas recorrentes', pagina: 'despesas-recorrentes' },
  { nome: 'Lançamentos', pagina: 'lancamentos' },
  { nome: 'Análise', pagina: 'analise' },
  { nome: 'Cadastros', pagina: 'cadastros' },
]

export default function Layout({ children, pagina = 'pendencias' }) {
  return (
    <div className="aplicacao">
      <a
        className="pular-conteudo"
        href="#conteudo"
        onClick={(evento) => {
          evento.preventDefault()
          document.getElementById('conteudo').focus()
        }}
      >
        Ir para o conteúdo
      </a>
      <aside className="sidebar" aria-label="Navegação principal">
        <a
          className="marca"
          href="#pendencias"
          aria-label="Compasso — Pendências"
        >
          <img
            className="marca-simbolo"
            src={logoCompasso}
            alt=""
            aria-hidden="true"
          />
          <span>
            Compasso
            <span className="marca-descricao">DESPESAS RECORRENTES</span>
          </span>
        </a>
        <div className="sidebar-linha" />
        <p className="menu-legenda">GESTÃO FINANCEIRA</p>
        <nav className="menu">
          {itens.map((item) => (
            <a
              key={item.nome}
              href={`#${item.pagina}`}
              className={`menu-item${item.pagina === pagina ? ' ativo' : ''}`}
              aria-current={item.pagina === pagina ? 'page' : undefined}
            >
              <span>{item.nome}</span>
            </a>
          ))}
        </nav>
      </aside>
      <main id="conteudo" className="conteudo" tabIndex={-1}>
        {children}
      </main>
    </div>
  )
}
