import { useEffect, useState } from 'react'
import Pendencias from './pages/Pendencias.jsx'
import DespesasRecorrentes from './pages/DespesasRecorrentes.jsx'
import Lancamentos from './pages/Lancamentos.jsx'
import Cadastros from './pages/Cadastros.jsx'
import Analise from './pages/Analise.jsx'
import './App.css'

const titulos = {
  pendencias: 'Despesas pendentes',
  'despesas-recorrentes': 'Despesas recorrentes',
  lancamentos: 'Lançamentos',
  cadastros: 'Cadastros',
  analise: 'Análise da competência',
}

function paginaAtual() {
  const pagina = window.location.hash.slice(1)
  return Object.hasOwn(titulos, pagina) ? pagina : 'pendencias'
}

export default function App() {
  const [pagina, setPagina] = useState(paginaAtual)

  useEffect(() => {
    const navegar = () => setPagina(paginaAtual())
    window.addEventListener('hashchange', navegar)
    return () => window.removeEventListener('hashchange', navegar)
  }, [])

  useEffect(() => {
    document.title = `${titulos[pagina]} · Compasso`
  }, [pagina])

  if (pagina === 'lancamentos') return <Lancamentos />
  if (pagina === 'cadastros') return <Cadastros />
  if (pagina === 'analise') return <Analise />
  if (pagina === 'despesas-recorrentes') return <DespesasRecorrentes />
  return <Pendencias />
}
