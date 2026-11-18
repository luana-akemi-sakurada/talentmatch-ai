import { useEffect, useRef, useState } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Activity, ChartNoAxesCombined, FlaskConical, Menu, ScanText, ShieldCheck, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useResource } from '@/hooks/use-resource'
import { api } from '@/services/api'
import Dashboard from '@/pages/Dashboard'
import Analyze from '@/pages/Analyze'
import Results from '@/pages/Results'
import Experiments from '@/pages/Experiments'
import Ethics from '@/pages/Ethics'
import type { Analysis } from '@/types'

const links = [
  { to: '/analise', label: 'Analisar currículo e vaga', icon: ScanText },
  { to: '/experimentos', label: 'Modelos e validação', icon: FlaskConical },
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
      if (event.key === 'Escape') { setMenu(false); menuButton.current?.focus() }
      if (event.key !== 'Tab') return
      const focusable = Array.from(navigation.current?.querySelectorAll<HTMLElement>('a[href],button') || []).filter(element => element.getClientRects().length > 0)
      const first = focusable[0], last = focusable.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    document.addEventListener('keydown', handleKey)
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', handleKey); menuButton.current?.focus() }
  }, [menu])
  function closeMenu() { setMenu(false); menuButton.current?.focus() }
  const label = links.find(l => l.to === location.pathname)?.label || (location.pathname.startsWith('/demonstracao') ? 'Demonstração offline' : 'Resultado da análise')
  const ready = !health.error && health.data?.model_loaded === true
  const healthLabel = health.loading ? 'Verificando API…' : health.error ? 'API inacessível' : ready ? 'API conectada · modelos disponíveis' : 'API conectada · modelos indisponíveis'
  return <div className="app-shell">
    <a className="skip-link" href="#main">Pular para o conteúdo</a>
    {menu && <button className="sidebar-backdrop" tabIndex={-1} aria-label="Fechar navegação" onClick={closeMenu}/>}
    <aside ref={navigation} id="navigation" className={`sidebar ${menu ? 'is-open' : ''}`}>
      <NavLink className="brand" to="/" onClick={() => setMenu(false)}><span className="brand-symbol"><ChartNoAxesCombined size={24}/></span><span>talentmatch<span className="brand-ai">AI</span><small>INTELIGÊNCIA COM EVIDÊNCIAS</small></span></NavLink>
      <button className="mobile-close" aria-label="Fechar menu" onClick={closeMenu}><X/></button>
      <p className="nav-label">ANÁLISE CURRÍCULO–VAGA</p>
      <nav aria-label="Navegação principal">{links.map(({to,label,icon: Icon}) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setMenu(false)} className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={19}/>{label}</NavLink>)}</nav>
      <div className="workspace-footer"><div><strong>Projeto acadêmico</strong><span>PUCPR · TDE2 / v2.0</span></div></div>
    </aside>
    <div className="workspace" inert={menu}>
      <div className="topbar"><div className="breadcrumbs"><button ref={menuButton} className="mobile-toggle" aria-label="Abrir navegação" aria-expanded={menu} aria-controls="navigation" onClick={() => setMenu(!menu)}><Menu size={22}/></button><span>Workspace</span><span className="slash">/</span><strong>{label}</strong></div><div className={`health-chip ${ready ? 'healthy' : ''}`} role="status" title={health.error || (ready ? 'API e artefatos ML acessíveis. O provedor LLM não é testado nesta verificação.' : 'API acessível, mas os artefatos ML não estão disponíveis. Execute o treino e reinicie o backend.')}><Activity size={14}/>{healthLabel}{!health.loading && !ready && <button onClick={health.reload}>Verificar novamente</button>}</div></div>
      {health.error && <div role="alert" className="panel-content"><p>Não foi possível verificar a API: {health.error}</p><p>Confirme que o backend está em execução e que a URL ou o proxy da API aponta para a porta correta.</p></div>}
      {!health.loading && !health.error && health.data && !ready && <div role="alert" className="panel-content"><p>A API respondeu, mas os modelos não foram carregados. Confira os quatro artefatos em models/ e reinicie o backend após o treinamento.</p></div>}
      <main id="main" tabIndex={-1} key={location.pathname}>
        <Routes>
          <Route path="/" element={<Dashboard hasResult={!!result}/>}/>
          <Route path="/analise" element={<Analyze onResult={setResult}/>}/>
          <Route path="/demonstracao" element={<Analyze key="offline" onResult={setResult} offline/>}/>
          <Route path="/resultado" element={<Results result={result} onClear={() => setResult(null)}/>}/>
          <Route path="/experimentos" element={<Experiments/>}/>
          <Route path="/etica" element={<Ethics/>}/>
          <Route path="*" element={<div className="error-state"><h1>Página não encontrada</h1><Button asChild><NavLink to="/">Voltar ao início</NavLink></Button></div>}/>
        </Routes>
        <footer className="main-footer"><span>TalentMatch AI <span className="footer-dot">·</span> Apoio responsável à análise de currículos</span><span>ML + LLM <span className="footer-dot">·</span> Revisão humana sempre</span></footer>
      </main>
    </div>
  </div>
}
