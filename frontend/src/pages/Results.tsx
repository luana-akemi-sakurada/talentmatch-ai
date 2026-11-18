import { Download, ScanText, Trash2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Notice, PageHeading, TextList } from '@/components/common'
import { RequirementCoverage } from '@/components/RequirementCoverage'
import type { Analysis } from '@/types'
const number = (v: number) => Number.isFinite(v) ? v.toLocaleString('pt-BR', {maximumFractionDigits: 3}) : 'Indisponível'
const percent = (v: number) => Number.isFinite(v) ? (v*100).toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '%' : 'Indisponível'
export default function Results({result, onClear}: {result: Analysis | null; onClear: () => void}) {
  const navigate = useNavigate()
  if (!result) return <><PageHeading eyebrow="RESULTADO" title="Nenhuma análise nesta sessão.">Envie um currículo e uma vaga.</PageHeading><div className="empty-state"><ScanText/><Button asChild><Link to="/analise">Analisar currículo e vaga</Link></Button></div></>
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify({...result, report_notice: 'Resultado automatizado parcial ou completo conforme os estados informados. Não é decisão de contratação.'}, null, 2)], {type: 'application/json;charset=utf-8'}))
    const link = document.createElement('a'); link.href = url; link.download = 'talentmatch-relatorio.json'; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  return <><PageHeading eyebrow="RESULTADO DA ANÁLISE" title="Resultados e evidências." action={<div className="button-row"><Button variant="outline" onClick={() => {onClear(); navigate('/analise')}}><Trash2 size={16}/>Limpar</Button><Button onClick={download}><Download size={16}/>Baixar relatório</Button></div>}>Resultado temporário. Revise o estado de cada etapa antes de interpretar.</PageHeading><AnalysisDetail result={result}/></>
}
export function AnalysisDetail({result}: {result: Analysis}) {
  const r = result.llm
  const ctx = result.ml_context
  const match = ctx?.disponivel ? ctx.compatibilidade_curriculo_vaga : null
  const completed = result.mode === 'live' && !!r && !result.llm_error
  const coverage = result.cobertura_requisitos
  return <div className="analysis-detail">
    {result.ml.warnings?.map((text, i) => <Notice warning key={i}>{text}</Notice>)}
    <Notice warning>Matching experimental treinado em inglês. Pares em português ou em idiomas diferentes não foram validados. Não interprete o rótulo como julgamento de aptidão.</Notice>
    {result.mode === 'demo' && <Notice warning>Demonstração: a análise contextual é simulada, não gerada pelo LLM.</Notice>}
    {result.llm_error && <Notice warning>Análise contextual não concluída: {result.warnings.at(-1)} Isso é uma falha de processamento ou validação, não evidência de falta de competências. Os resultados ML são independentes.</Notice>}
    {!r && !result.llm_error && <Notice warning>Nenhuma análise contextual disponível nesta resposta.</Notice>}
    <div className="result-overview"><Card><CardContent className="panel-content"><h2>Área derivada · ML</h2><p className="result-area">{result.ml.predicted_area.replaceAll('-', ' ')}</p><p>{result.ml.model_name}</p>{result.ml.top_categories.map(item => <p key={item.category}>{item.category.replaceAll('-', ' ')}: {percent(item.probability)}</p>)}{ctx?.disponivel && <><p>Entropia da área: {number(ctx.entropia_normalizada)}</p><p>Margem da área: {number(ctx.margem_top1_top2)}</p>{ctx.deteccao_fora_distribuicao.possivel_ood && <Notice warning>Alerta lexical experimental para a área: currículo distante dos centróides de treino. Não é um detector OOD validado externamente, nem uma medição da compatibilidade.</Notice>}</>}<p className="chart-footnote">Categorias derivadas das vagas associadas no dataset. Não comprovam profissão, competência ou adequação à vaga enviada.</p></CardContent></Card>
    <Card><CardContent className="panel-content"><h2>Compatibilidade currículo–vaga · ML</h2>{match ? <><p className="result-area">{match.compatibilidade_prevista}</p><p>Probabilidade prevista da classe “{match.compatibilidade_prevista}”: {percent(match.probabilidade_calibrada)}</p><p>Entropia do matching: {number(match.entropia_normalizada)}</p><p>Margem do matching: {number(match.margem_top1_top2)}</p>{match.alternativas.map((item, i) => <p key={i}>{item.compatibilidade}: {percent(item.probabilidade_calibrada)}</p>)}<p>Faixas de confiança: {match.nivel_confianca}.</p></> : <p>Matching indisponível: não há contexto estatístico utilizável nesta resposta.</p>}<p className="chart-footnote">O modelo reproduz rótulos do dataset. Esta probabilidade não é percentual de requisitos atendidos, chance de contratação ou confiança validada para este caso.</p></CardContent></Card></div>
    {completed && r && <Card><CardContent className="panel-content"><h2>Perfil profissional citado</h2>{r.perfil_profissional ? <><p>{r.perfil_profissional.descricao}</p><blockquote>{r.perfil_profissional.evidencia}</blockquote></> : <p>A extração foi concluída, mas não estabeleceu uma designação profissional citável.</p>}</CardContent></Card>}
    {completed && coverage && coverage.total > 0 ? <RequirementCoverage coverage={coverage}/> : <Card><CardContent className="panel-content"><h2>Cobertura documental indisponível</h2><p>{!completed ? 'A etapa contextual não foi concluída em modo ao vivo.' : 'Não há um inventário de requisitos suficiente para apresentar a cobertura.'} Isso não significa cobertura zero nem ausência de competências.</p></CardContent></Card>}
    {ctx?.disponivel && ctx.requisitos_priorizados.length > 0 && <Card><CardContent className="panel-content"><h2>Similaridade lexical por item identificado</h2><p>Itens não são classificados automaticamente aqui como obrigatórios ou preferenciais. Listas de tecnologias da vaga podem ser apenas exemplos por equipe.</p>{ctx.requisitos_priorizados.map((item, i) => <p key={i}>{item.requisito}: {number(item.similaridade_cosseno)}</p>)}<p>Similaridade não confirma atendimento nem ausência de habilidade.</p></CardContent></Card>}
    {r && <><Card><CardContent className="panel-content"><h2>{result.mode === 'demo' ? 'Extração simulada' : 'Extração contextual'}</h2><p>{r.resumo}</p><div className="skill-tags">{r.habilidades.map((s, i) => <Badge key={i} variant="secondary">{s}</Badge>)}</div><TextList items={r.experiencia_profissional} empty="Sem experiência detalhada nesta extração."/><p>Duração total explícita: {r.anos_experiencia === null ? 'não estabelecida' : `${r.anos_experiencia} anos; confirme no documento`}.</p></CardContent></Card><div className="two-column"><Card><CardContent className="panel-content"><h2>Associações com evidência</h2>{r.requisitos_atendidos.map((item, i) => <div key={i}><h3>{item.requisito}</h3><blockquote>{item.evidencia}</blockquote></div>)}{!r.requisitos_atendidos.length && <p>Nenhuma associação publicada nesta extração.</p>}</CardContent></Card><Card><CardContent className="panel-content"><h2>Itens sem evidência suficiente</h2><TextList items={r.requisitos_sem_evidencia}/><p>Não demonstrado não significa não possuir a competência.</p></CardContent></Card></div><Card><CardContent className="panel-content"><h2>Fundamentação e limites</h2><p>{r.justificativa}</p><TextList items={r.pontos_fortes}/><TextList items={r.lacunas}/></CardContent></Card></>}
    <details className="transparency-details"><summary>Transparência e diagnóstico</summary><ul>{result.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul><p>Etapa contextual: {result.llm_error ? `não concluída (${result.llm_error})` : r ? result.mode === 'demo' ? 'simulada' : 'extração recebida e validada; consulte limitações' : 'indisponível'}.</p><p>Remoções automáticas: {String(result.privacy.resume_redactions)} no currículo; {String(result.privacy.job_redactions)} na vaga. Minimização não garante anonimização.</p></details>
  </div>
}
