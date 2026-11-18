import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ErrorState, Loading, Notice, PageHeading } from '@/components/common'
import { useResource } from '@/hooks/use-resource'
import { getEvaluation } from '@/services/evaluation'
export default function Dashboard(_props: {hasResult: boolean}) {
  const resource = useResource(getEvaluation)
  const data = resource.data
  return <><PageHeading eyebrow="VISÃO GERAL" title="Análise de currículos com evidências.">O ML estima padrões do dataset; o LLM verifica evidências textuais. A decisão permanece humana.</PageHeading><Button asChild><Link to="/analise">Analisar currículo e vaga</Link></Button>{resource.loading && <Loading/>}{resource.error && <ErrorState message={resource.error} retry={resource.reload}/>} {data && <><Notice>Dataset: {data.dataset} · execução {data.run_id}. Métricas do teste; não representam chance de contratação.</Notice><div className="two-column">{(['area', 'compatibility'] as const).map(key => {const task = data.tasks[key]; return <Card key={key}><CardContent className="panel-content"><h2>{key === 'area' ? 'Área derivada' : 'Compatibilidade currículo–vaga'}</h2><p>{task.model}</p><p>Acurácia: {(task.evaluation.metrics.accuracy.point*100).toFixed(2)}%</p><p>F1 macro: {task.evaluation.metrics.f1_macro.point.toFixed(3)}</p><p>Teste: {task.splits.test.rows} exemplos, {task.splits.test.resume_groups} grupos de currículos.</p><Link to="/experimentos">Ver intervalos, classes e limitações</Link></CardContent></Card>})}</div></>}</>
}
