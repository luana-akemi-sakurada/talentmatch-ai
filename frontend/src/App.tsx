import { useEffect, useRef, useState } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Activity, ArrowUpRight, ChartNoAxesCombined, FlaskConical, LayoutDashboard, Menu, ScanText, ShieldCheck, Sparkles, Users, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useResource } from '@/hooks/use-resource'
import { api } from '@/services/api'
import Dashboard from '@/pages/Dashboard'
import Analyze from '@/pages/Analyze'
import Results from '@/pages/Results'
import Experiments from '@/pages/Experiments'
import Compare from '@/pages/Compare'
import Ethics from '@/pages/Ethics'
import type { Analysis } from '@/types'

const links = [
  { to: '/', label: 'Visão geral', icon: LayoutDashboard },
  { to: '/analise', label: 'Nova análise', icon: ScanText },
  { to: '/comparacao', label: 'Comparar currículos', icon: Users },
  { to: '/experimentos', label: 'Experimentos de ML', icon: FlaskConical },
  { to: '/etica', label: 'Ética e transparência', icon: ShieldCheck },
]
export default function App() {
  const [menu, setMenu] = useState(false)
  const [result, setResult] = useState<Analysis | null>(null)
  const health = useResource(api.health)
  const location = useLocation()
  const navigation = useRef<HTMLElement>(null)
  const menuButton = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    window.scrollTo(0, 0)
    document.getElementById('main')?.focus({ preventScroll: true })
  }, [location.pathname])
  useEffect(() => {
    if (!menu) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    navigation.current?.querySelector<HTMLButtonElement>('.mobile-close')?.focus()
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setMenu(false)
        menuButton.current?.focus()
      }
      if (event.key !== 'Tab') return
      const focusable = Array.from(navigation.current?.querySelectorAll<HTMLElement>('a[href],button') || [])
        .filter(element => element.getClientRects().length > 0)
      const first = focusable[0], last = focusable.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    document.addEventListener('keydown', handleKey)
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', handleKey); menuButton.current?.focus() }
  }, [menu])
  function closeMenu() { setMenu(false); menuButton.current?.focus() }
  const label = links.find(l => l.to === location.pathname)?.label || (location.pathname.startsWith('/demonstracao') ? 'Demonstração offline' : 'Resultado da análise')
  return <div className="app-shell">
    <a className="skip-link" href="#main">Pular para o conteúdo</a>
    {menu && <button className="sidebar-backdrop" tabIndex={-1} aria-label="Fechar navegação" onClick={closeMenu}/>}
    <aside ref={navigation} id="navigation" className={`sidebar ${menu ? 'is-open' : ''}`}>
      <NavLink className="brand" to="/" onClick={() => setMenu(false)}><span className="brand-symbol"><ChartNoAxesCombined size={24}/></span><span>talentmatch<span className="brand-ai">AI</span><small>INTELIGÊNCIA COM EVIDÊNCIAS</small></span></NavLink>
      <button className="mobile-close" aria-label="Fechar menu" onClick={closeMenu}><X/></button>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Navegação principal">{links.map(({to,label,icon: Icon}) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setMenu(false)} className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={19}/>{label}</NavLink>)}</nav>
      <div className="sidebar-note"><span className="tiny-spark"><Sparkles size={18}/></span><h3>IA como apoio.<br/>Pessoas no centro.</h3><p>Analise o contexto com evidências. A decisão continua humana.</p><NavLink to="/etica" onClick={() => setMenu(false)}>Conheça os princípios <ArrowUpRight size={15}/></NavLink></div>
      <div className="workspace-footer"><div className="avatar">TM</div><div><strong>Projeto acadêmico</strong><span>PUCPR · TDE2 / v2.0</span></div><span className="online-dot"/></div>
    </aside>
    <div className="workspace" inert={menu}>
      <div className="topbar"><div className="breadcrumbs"><button ref={menuButton} className="mobile-toggle" aria-label="Abrir navegação" aria-expanded={menu} aria-controls="navigation" onClick={() => setMenu(!menu)}><Menu size={22}/></button><span>Workspace</span><span className="slash">/</span><strong>{label}</strong></div><div className={`health-chip ${health.data ? 'healthy' : ''}`} title={health.error || 'Estado do classificador no backend'}><Activity size={14}/>{health.loading ? 'Conectando…' : health.data ? 'Classificador disponível' : 'API indisponível'}{health.error && <button onClick={health.reload}>Reconectar</button>}</div></div>
      <main id="main" tabIndex={-1} key={location.pathname}>
        <Routes>
          <Route path="/" element={<Dashboard hasResult={!!result}/>}/>
          <Route path="/analise" element={<Analyze onResult={setResult}/>}/>
          <Route path="/demonstracao" element={<Analyze key="offline" onResult={setResult} offline/>}/>
          <Route path="/demonstracao/comparacao" element={<Compare key="offline" offline/>}/>
          <Route path="/resultado" element={<Results result={result} onClear={() => setResult(null)}/>}/>
          <Route path="/experimentos" element={<Experiments/>}/>
          <Route path="/comparacao" element={<Compare/>}/>
          <Route path="/etica" element={<Ethics/>}/>
          <Route path="*" element={<div className="error-state"><h1>Página não encontrada</h1><Button asChild><NavLink to="/">Voltar ao início</NavLink></Button></div>}/>
        </Routes>
        <footer className="main-footer"><span>TalentMatch AI <span className="footer-dot">·</span> Apoio responsável à análise de currículos</span><span>ML + LLM <span className="footer-dot">·</span> Revisão humana sempre</span></footer>
      </main>
    </div>
  </div>
}
