import { Card, CardContent } from '@/components/ui/card'
import type { Analysis } from '@/types'

export function RequirementCoverage({coverage}: {coverage: Analysis['cobertura_requisitos']}) {
  const calculated = coverage?.status === 'calculada' && coverage.percentual != null
  const labels = {evidencia_verificada:'Evidência verificada', sem_evidencia_suficiente:'Sem evidência suficiente', indeterminado:'Indeterminado'}
  return <Card className="score-card"><CardContent className="panel-content">
    <h2>Cobertura de requisitos identificados</h2>
    <p><strong>{coverage?.com_evidencia ?? 0} de {coverage?.total ?? 0} requisitos com evidência.</strong></p>
    {calculated ? <><p className="result-area">{coverage.percentual!.toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1})}% de cobertura documental.</p>
      <div className="probability-track score-track" role="progressbar" aria-label="Cobertura documental" aria-valuemin={0} aria-valuemax={100} aria-valuenow={coverage.percentual!}><div className="primary" style={{width:`${coverage.percentual}%`}}/></div></>
      : <p>Cobertura total indeterminada: a lista ou suas avaliações ainda não estão completas e verificadas.</p>}
    <p>Sem evidência suficiente: {coverage?.sem_evidencia ?? 0}. Indeterminados: {coverage?.indeterminados ?? 0}. Lista completa: {coverage?.lista_completa ? 'sim' : 'não'}.</p>
    <p className="score-formula">Fórmula: requisitos distintos com evidências verificadas ÷ requisitos distintos avaliados × 100. Sem pesos.</p>
    <p>Mede a presença de evidências textuais entre os requisitos identificados. Não comprova competências nem representa chance de contratação.</p>
    {!!coverage?.requisitos.length && <details><summary>Conferir requisitos e evidências</summary>{coverage.requisitos.map(item => <div key={item.id} className="evidence-list"><p><strong>{item.texto}</strong> — {labels[item.estado]}</p><p>Referência na vaga: {item.referencias_vaga.join(' | ')}</p>{item.evidencias.map((quote,i) => <blockquote key={i}>{quote}</blockquote>)}</div>)}</details>}
  </CardContent></Card>
}
