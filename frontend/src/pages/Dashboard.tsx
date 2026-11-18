import { ArrowRight, FlaskConical, Layers3, ShieldCheck, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ErrorState, Loading, MetricChart, PageHeading, SectionLink } from '@/components/common'
import { useResource } from '@/hooks/use-resource'
import { api } from '@/services/api'

export default function Dashboard(_props: {hasResult: boolean}) {
  const metrics = useResource(api.metrics)
  const categories = useResource(api.categories)
  const best = metrics.data?.models.find(m => m.name === metrics.data?.selected_model)
  return <>
    <PageHeading eyebrow="SEU ESPAÇO DE ANÁLISE" title="Mais contexto. Melhores decisões.">Uma visão clara sobre currículos, evidências e os modelos por trás da análise.</PageHeading>
    <section className="hero-panel"><div className="hero-copy"><Badge variant="outline" className="hero-badge"><span className="online-dot"/>MACHINE LEARNING + IA GENERATIVA</Badge><h2>Encontre evidências.<br/><span>Amplie a conversa.</span></h2><p>Conecte a experiência de um currículo aos requisitos da vaga. Entenda os pontos de encontro e o que ainda precisa ser explorado.</p><Button asChild className="hero-button"><Link to="/analise">Analisar um currículo<ArrowRight size={17}/></Link></Button><small><ShieldCheck size={14}/>Sem decisões automáticas de contratação</small></div><div className="hero-visual" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="visual-dot dot-one"/><div className="visual-dot dot-two"/><div className="document-illustration"><div className="doc-head"><div className="doc-avatar"/><div><i/><i/></div><span>CV</span></div><div className="doc-lines"><i/><i/><i/></div><div className="doc-tags"><span>Experiência</span><span>Competências</span></div><div className="doc-lines short"><i/><i/></div><div className="doc-check"><ShieldCheck size={20}/><span>Evidências, com contexto</span></div></div><div className="visual-label label-ml"><Layers3 size={18}/><div><strong>Classificação ML</strong><small>Áreas profissionais</small></div></div><div className="visual-label label-human"><ShieldCheck size={18}/><div><strong>Revisão humana</strong><small>Você conduz a análise</small></div></div></div></section>
    <div className="section-heading"><h2>O que sustenta a análise</h2><span className="muted text-sm">Experimentos reais · artefatos preservados</span></div>
    <div className="stat-grid">
      <Stat icon={<Target size={19}/>} label="Melhor acurácia registrada" value={best ? `${(best.accuracy * 100).toFixed(2).replace('.', ',')}%` : '—'} detail="Classificação de área profissional"/>
      <Stat icon={<Layers3 size={19}/>} label="Categorias profissionais" value={categories.data ? String(categories.data.categories.length) : '—'} detail="Recuperadas do modelo treinado"/>
      <Stat icon={<FlaskConical size={19}/>} label="Algoritmos comparados" value={metrics.data ? String(metrics.data.models.length).padStart(2,'0') : '—'} detail="Regressão logística, RF e MLP"/>
      <Stat icon={<ShieldCheck size={19}/>} label="Modelo selecionado" value={metrics.data?.selected_model === 'RandomForest' ? 'Random Forest' : metrics.data?.selected_model || '—'} detail="Critério: maior F1 macro" compact/>
    </div>
    {metrics.error && <ErrorState message={metrics.error} retry={metrics.reload}/>}
    {categories.error && <ErrorState message={`Categorias indisponíveis. ${categories.error}`} retry={categories.reload}/>}
    <Card><CardContent className="panel-content"><div className="section-heading"><div><h2>Desempenho dos modelos</h2><p className="muted text-sm">Acurácia em % · F1 macro de 0 a 1</p></div><SectionLink to="/experimentos">Explorar</SectionLink></div>{metrics.loading ? <Loading/> : metrics.data && <MetricChart models={metrics.data.models} compact/>}<p className="chart-footnote">Fonte: models/comparacao_modelos.csv. Mesmo teste usado para seleção e avaliação, sem teste final independente. As métricas não medem compatibilidade com vagas.</p></CardContent></Card>
  </>
}
function Stat({icon,label,value,detail,compact}: {icon:React.ReactNode;label:string;value:string;detail:string;compact?:boolean}) { return <Card><CardContent className="stat-content"><div className="stat-top"><span>{label}</span><div className="stat-icon">{icon}</div></div><div className={`stat-value ${compact ? 'compact' : ''}`}>{value}</div><p>{detail}</p></CardContent></Card> }
