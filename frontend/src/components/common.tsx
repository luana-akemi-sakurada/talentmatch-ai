import type { ReactNode } from 'react'
import { AlertCircle, ArrowUpRight, LoaderCircle, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Button } from '@/components/ui/button'
import type { ModelMetric } from '@/types'
import { f1, modelName, percent } from '@/lib/format'

export function PageHeading({ eyebrow, title, children, action }: { eyebrow: string; title: string; children: ReactNode; action?: ReactNode }) {
  return <header className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="subtitle">{children}</p></div>{action}</header>
}
export function Notice({ children, warning = false }: { children: ReactNode; warning?: boolean }) {
  const Icon = warning ? AlertCircle : ShieldCheck
  return <div className={`notice ${warning ? 'notice-warning' : ''}`} role={warning ? 'alert' : 'note'}><Icon size={19} aria-hidden="true"/><div>{children}</div></div>
}
export function Loading({ children = 'Carregando dados reais…' }: { children?: ReactNode }) {
  return <div className="loading" role="status"><LoaderCircle className="spin" size={22}/>{children}</div>
}
export function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  return <div className="error-state" role="alert"><AlertCircle/><h2>Não foi possível carregar</h2><p>{message}</p><Button variant="outline" onClick={retry}>Tentar novamente</Button></div>
}
export function MetricChart({ models, compact = false }: { models: ModelMetric[]; compact?: boolean }) {
  const data = models.map(m => ({ name: m.name === 'LogisticRegression' ? 'Reg. logística' : m.name.startsWith('MLP') ? 'MLP' : modelName(m.name), accuracy: m.accuracy, f1_macro: m.f1_macro }))
  return <div className={`metric-charts ${compact ? 'metric-charts-compact' : ''}`}>
    {(['accuracy', 'f1_macro'] as const).map(key => {
      const accuracy = key === 'accuracy'
      const format = accuracy ? percent : f1
      const title = accuracy ? 'Acurácia' : 'F1 macro'
      return <figure className="metric-plot" key={key}>
        <figcaption><strong>{title}</strong><span>{accuracy ? 'Escala: 0% a 100%' : 'Escala: 0 a 1'}</span></figcaption>
        <div className="metric-plot-frame" role="img" aria-label={`${title}. ${models.map(m => `${modelName(m.name)}: ${format(m[key])}`).join('; ')}.`}>
          <ResponsiveContainer width="100%" height="100%"><BarChart data={data} accessibilityLayer={false} margin={{left:-12,right:12,top:25,bottom:8}}>
            <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e1e7df"/>
            <XAxis dataKey="name" tickLine={false} axisLine={false} tick={<MetricAxisTick/>} interval={0} height={42}/>
            <YAxis domain={[0,1]} ticks={[0,.25,.5,.75,1]} tickFormatter={v => accuracy ? `${v*100}%` : String(v).replace('.',',')} tickLine={false} axisLine={false} tick={{fontSize:11,fill:'#52634e'}}/>
            <Tooltip cursor={{fill:'#edf3ed'}} formatter={v => [format(Number(v)), title]} contentStyle={{borderRadius:10,border:'1px solid #dce5dd'}}/>
            <Bar dataKey={key} fill={accuracy ? '#287c63' : '#5267a0'} radius={[5,5,0,0]} maxBarSize={48} isAnimationActive={false}>
              <LabelList dataKey={key} position="top" formatter={value => format(Number(value))} fill="#344b3d" fontSize={12}/>
            </Bar>
          </BarChart></ResponsiveContainer>
        </div>
      </figure>
    })}
  </div>
}

function MetricAxisTick({ x = 0, y = 0, payload }: { x?: number; y?: number; payload?: { value: string } }) {
  const label = payload?.value || ''
  const lines = label === 'Random Forest' ? ['Random', 'Forest'] : label === 'Reg. logística' ? ['Regressão', 'logística'] : [label]
  return <text x={x} y={y} textAnchor="middle" fill="#52634e" fontSize={12}>
    {lines.map((line, index) => <tspan key={line} x={x} dy={index ? 15 : 17}>{line}</tspan>)}
  </text>
}

export function ModelMetricsTable({ models, selected }: { models: ModelMetric[]; selected: string }) {
  return <div className="table-scroll" role="region" aria-label="Tabela de métricas dos classificadores" tabIndex={0}>
    <table className="model-metrics-table"><caption>Valores originais de models/comparacao_modelos.csv</caption>
      <thead><tr><th scope="col">Classificador</th><th scope="col">Acurácia (%)</th><th scope="col">F1 macro (0–1)</th></tr></thead>
      <tbody>{models.map(model => <tr key={model.name} className={model.name === selected ? 'selected-model' : ''}>
        <th scope="row">{modelName(model.name)}{model.name === selected && <span className="selection-label">Selecionado pelo F1 macro</span>}</th>
        <td>{percent(model.accuracy)}</td><td>{f1(model.f1_macro)}</td>
      </tr>)}</tbody>
    </table>
  </div>
}
export function TextList({ items, empty = 'Nenhuma informação registrada.' }: { items: string[]; empty?: string }) {
  return items.length ? <ul className="text-list">{items.map((item, i) => <li key={i}>{item}</li>)}</ul> : <p className="muted">{empty}</p>
}
export function SectionLink({ to, children }: { to: string; children: ReactNode }) { return <Link className="section-link" to={to}>{children}<ArrowUpRight size={16}/></Link> }
