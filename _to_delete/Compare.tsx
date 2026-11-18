import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { LoaderCircle, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Notice, PageHeading } from '@/components/common'
import { FileDrop } from '@/pages/Analyze'
import { AnalysisDetail } from '@/pages/Results'
import { api } from '@/services/api'
import type { Analysis, Comparison } from '@/types'

const criteria: { title: string; render: (result: Analysis) => ReactNode }[] = [
  { title: 'Classificação ML', render: r => r.ml.predicted_area.replaceAll('-', ' ') },
  { title: 'Perfil contextual (LLM)', render: r => r.llm!.perfil_profissional?.descricao || 'Não estabelecido com evidência suficiente' },
  { title: 'Competências citadas', render: r => r.llm!.habilidades.join(', ') || 'Nenhuma competência identificada' },
  { title: 'Requisitos demonstrados', render: r => r.llm!.requisitos_atendidos.length
    ? r.llm!.requisitos_atendidos.map((item, index) => <div className="comparison-evidence" key={index}><strong>{item.requisito}</strong><q>{item.evidencia}</q></div>)
    : 'Nenhuma evidência registrada' },
  { title: 'Sem evidência suficiente', render: r => r.llm!.requisitos_sem_evidencia.join(', ') || 'Nenhum requisito listado nesta categoria' },
  { title: 'Experiência explícita', render: r => r.mode === 'demo' ? 'Não avaliada na simulação'
    : r.llm!.experiencia_profissional.join('; ') || 'Sem detalhamento de experiência registrado' },
]

export default function Compare({offline = false}: {offline?: boolean}) {
  const [files, setFiles] = useState<File[]>([])
  const [job, setJob] = useState('')
  const mode = offline ? 'demo' : 'live'
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<Comparison | null>(null)
  const controller = useRef<AbortController | null>(null)
  useEffect(() => () => controller.current?.abort(), [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(''); setResult(null); setBusy(true)
    const data = new FormData()
    data.set('job_description', job); data.set('mode', mode)
    files.forEach(file => data.append('files', file))
    controller.current = new AbortController()
    try { setResult(await api.compare(data, controller.current.signal)) }
    catch (error) { if ((error as Error).name !== 'AbortError') setError((error as Error).message) }
    finally { setBusy(false) }
  }

  return <>
    <PageHeading eyebrow="COMPARAÇÃO DE CURRÍCULOS" title="Perspectivas lado a lado.">Explore evidências para uma mesma vaga, preservando o contexto de cada pessoa.</PageHeading>
    <Notice>A ordem de envio é preservada. Não há ranking, recomendação de contratação ou rejeição automática.</Notice>
    <form onSubmit={submit} aria-busy={busy}>
      <div className="form-grid">
        <Card><CardContent className="panel-content">
          <h2>Currículos para comparar</h2>
          <p className="muted text-sm mb-5">De 2 a 5 documentos. Identificados como Candidato 1, 2…</p>
          <FileDrop files={files} onChange={setFiles} multiple disabled={busy}/>
        </CardContent></Card>
        <Card><CardContent className="panel-content">
          <label htmlFor="compare-job" className="field-label">Descrição da vaga</label>
          <textarea id="compare-job" rows={8} value={job} onChange={e => setJob(e.target.value)} maxLength={16000} required disabled={busy} placeholder="Requisitos essenciais e desejáveis da mesma oportunidade…"/>
          <p className="field-hint">{offline ? 'Demonstração offline explícita: contexto simulado.' : 'Análise com LLM; o resultado ML local é preservado em caso de falha.'}</p>
          {mode === 'live' && <label className="consent"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} required disabled={busy}/><span>Tenho autorização para o processamento e envio dos textos minimizados ao provedor externo. A minimização automática é limitada.</span></label>}
          <p className="field-hint">No modo LLM, até cinco chamadas sequenciais. Falhas individuais são identificadas.</p>
        </CardContent></Card>
      </div>
      {error && <Notice warning>{error}</Notice>}
      <div className="form-actions"><p>Os resultados ficam apenas nesta tela até sair ou limpar.</p><Button type="submit" disabled={busy || files.length < 2 || (mode === 'live' && !consent)}>{busy ? <><LoaderCircle className="spin" size={17}/>Processando currículos…</> : <><Users size={17}/>Comparar evidências</>}</Button></div>
      <div role="status" className="sr-only">{busy && 'Analisando currículos em sequência. Aguarde.'}</div>
    </form>
    {result && <section className="comparison-results" aria-label="Resultados da comparação">
      <div className="section-heading"><h2>Evidências por currículo</h2><Button variant="outline" onClick={() => { setResult(null); setFiles([]); setJob('') }}>Limpar comparação</Button></div>
      {result.failures.map(failure => <Notice warning key={failure.candidate_id}>{failure.candidate_id}: {failure.message}</Notice>)}
      {!result.results.length ? <Notice warning>Nenhum currículo pôde ser analisado. Confira as mensagens dos arquivos e tente novamente.</Notice> : <>
        <Card><CardContent className="panel-content">
          <p className="muted text-sm mb-5">{result.notice}</p>
          {result.results.some(r => r.mode === 'demo') && <Notice warning>Contexto simulado: apenas correspondência de termos. A experiência profissional não é avaliada neste modo. Consulte o currículo original.</Notice>}
          <div className="table-scroll" role="region" aria-label="Tabela comparativa de evidências" tabIndex={0}>
            <table className="comparison-table">
              <caption className="sr-only">Competências e evidências na ordem de envio</caption>
              <thead><tr><th scope="col">Critério</th>{result.results.map(r => <th scope="col" key={r.candidate_id}>{r.candidate_id} {r.mode === 'demo' && <Badge variant="secondary">Simulado</Badge>}</th>)}</tr></thead>
              <tbody>{criteria.map(criterion => <tr key={criterion.title}><th scope="row">{criterion.title}</th>{result.results.map(r => <td key={r.candidate_id}>{r.llm ? criterion.render(r) : 'Análise contextual indisponível'}</td>)}</tr>)}</tbody>
            </table>
          </div>
        </CardContent></Card>
        {result.results.map(r => <details className="candidate-details" key={r.candidate_id}><summary>{r.candidate_id}<span>Análise individual completa</span></summary><AnalysisDetail result={r}/></details>)}
      </>}
    </section>}
  </>
}
