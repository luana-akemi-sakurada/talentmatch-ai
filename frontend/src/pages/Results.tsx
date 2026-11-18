import { Download, ScanText, Trash2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Notice, PageHeading } from '@/components/common'
import { RequirementCoverage } from '@/components/RequirementCoverage'
import type { Analysis, CompatibilityPrediction } from '@/types'
import '../results.css'

const ok = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const number = (v: number, digits = 3) => ok(v) ? v.toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits}) : '—'
const percent = (v: number) => ok(v) ? (v * 100).toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '%' : '—'
const signed = (v: number) => (v >= 0 ? '+' : '−') + Math.abs(v).toLocaleString('pt-BR', {minimumFractionDigits: 3, maximumFractionDigits: 3})
const titleCase = (text: string) => text.replaceAll('-', ' ').toLowerCase().replace(/(^|\s)\S/g, c => c.toUpperCase())
const SHORT_FRAGMENT = 45

/** Escala do score com as faixas do dataset, o ponto estimado e o intervalo de 80%. */
function ScoreScale({score, interval, cuts}: {score: number; interval: [number, number]; cuts: [number, number]}) {
  const min = 0.40, max = 0.80
  const at = (v: number) => Math.min(100, Math.max(0, (v - min) / (max - min) * 100))
  const [low, high] = interval
  return <div className="rs-scale" role="img" aria-label={`Score estimado ${number(score, 2)}. Intervalo de 80%: ${number(low, 2)} a ${number(high, 2)}. Cortes das faixas: ${number(cuts[0], 2)} e ${number(cuts[1], 2)}.`}>
    <div className="rs-track">
      <span className="rs-zone rs-zone-weak" style={{left: 0, width: `${at(cuts[0])}%`}}/>
      <span className="rs-zone rs-zone-mid" style={{left: `${at(cuts[0])}%`, width: `${at(cuts[1]) - at(cuts[0])}%`}}/>
      <span className="rs-zone rs-zone-strong" style={{left: `${at(cuts[1])}%`, right: 0}}/>
      <span className="rs-interval" style={{left: `${at(low)}%`, width: `${Math.max(at(high) - at(low), 1)}%`}}/>
      <span className="rs-marker" style={{left: `${at(score)}%`}}/>
    </div>
    <div className="rs-zone-labels" aria-hidden="true">
      <span style={{left: `${at(cuts[0]) / 2}%`}}>Fraca</span>
      <span style={{left: `${(at(cuts[0]) + at(cuts[1])) / 2}%`}}>Média</span>
      <span style={{left: `${(at(cuts[1]) + 100) / 2}%`}}>Forte</span>
    </div>
  </div>
}

function ProbabilityRows({rows, highlight}: {rows: {label: string; value: number}[]; highlight?: string}) {
  return <ul className="rs-bars">{rows.map(row => <li key={row.label} className={row.label === highlight ? 'is-top' : ''}>
    <span className="rs-bars-label">{row.label}</span>
    <span className="rs-bars-track"><span style={{width: `${Math.max(row.value * 100, row.value > 0 ? 1.5 : 0)}%`}}/></span>
    <span className="rs-bars-value">{percent(row.value)}</span>
  </li>)}</ul>
}

function SignalBars({signals}: {signals: {sinal: string; contribuicao: number}[]}) {
  const largest = Math.max(...signals.map(s => Math.abs(s.contribuicao)), 0.001)
  return <ul className="rs-signals">{signals.map(s => {
    const width = Math.abs(s.contribuicao) / largest * 50
    const positive = s.contribuicao >= 0
    return <li key={s.sinal}>
      <span className="rs-signal-name">{s.sinal}</span>
      <span className="rs-signal-track" aria-hidden="true"><span className={positive ? 'is-positive' : 'is-negative'} style={positive ? {left: '50%', width: `${width}%`} : {right: '50%', width: `${width}%`}}/></span>
      <span className="rs-signal-value">{signed(s.contribuicao)}</span>
    </li>
  })}</ul>
}

function Fact({label, children}: {label: string; children: ReactNode}) {
  return <div className="rs-fact"><dt>{label}</dt><dd>{children}</dd></div>
}

function MatchCard({match}: {match: CompatibilityPrediction | null}) {
  if (!match) return <section className="rs-card rs-hero"><p className="rs-eyebrow">Compatibilidade currículo–vaga · ML</p><p className="rs-muted">Matching indisponível: não há contexto estatístico utilizável nesta resposta.</p></section>
  const hasScore = ok(match.score_estimado) && match.intervalo_80 && match.cortes_faixas
  const bands = match.faixas ?? [{faixa: match.compatibilidade_prevista, probabilidade: match.probabilidade_calibrada}, ...match.alternativas.map(a => ({faixa: a.compatibilidade, probabilidade: a.probabilidade_calibrada}))]
  return <section className="rs-card rs-hero">
    <p className="rs-eyebrow">Compatibilidade currículo–vaga · ML</p>
    <div className="rs-headline"><span className={`rs-band rs-band-${match.rotulo_bruto.replace('compatibilidade_', '')}`}>{match.compatibilidade_prevista}</span>{hasScore && <span className="rs-score">score estimado <strong>{number(match.score_estimado!, 2)}</strong></span>}</div>
    {hasScore && <ScoreScale score={match.score_estimado!} interval={match.intervalo_80!} cuts={match.cortes_faixas!}/>}
    {hasScore && <p className="rs-caption">A faixa verde-claro é o intervalo de 80% do score ({number(match.intervalo_80![0], 2)} a {number(match.intervalo_80![1], 2)}). Quanto mais largo, menos preciso o modelo.</p>}
    <h3 className="rs-sub">Probabilidade por faixa</h3>
    <ProbabilityRows rows={bands.map(b => ({label: b.faixa, value: b.probabilidade}))} highlight={match.compatibilidade_prevista}/>
    <p className="rs-note">Faixas e score reproduzem a heurística do dataset. Não são percentual de requisitos atendidos nem chance de contratação.</p>
  </section>
}

function AreaCard({result}: {result: Analysis}) {
  const ctx = result.ml_context
  const top = result.ml.top_categories
  const abstained = result.ml.status === 'abstained'
  const ood = ctx?.disponivel && ctx.deteccao_fora_distribuicao.possivel_ood
  return <section className="rs-card">
    <p className="rs-eyebrow">Área derivada · ML</p>
    <p className="rs-area">{abstained ? 'Indeterminada' : titleCase(result.ml.predicted_area)}</p>
    {top.length > 0 && <ProbabilityRows rows={top.map(t => ({label: titleCase(t.category), value: t.probability}))} highlight={titleCase(result.ml.predicted_area)}/>}
    {abstained && <p className="rs-muted">O texto não tem vocabulário reconhecido pelo modelo.</p>}
    {ood && <p className="rs-chip-note">Vocabulário pouco comum em relação ao treino (alerta experimental).</p>}
    <p className="rs-note">Área inferida das vagas associadas no dataset. Não comprova profissão, competência ou adequação à vaga.</p>
  </section>
}

function WhyCard({match}: {match: CompatibilityPrediction}) {
  const common = match.habilidades_em_comum ?? []
  const missing = match.habilidades_da_vaga_ausentes ?? []
  const jobSkills = match.n_habilidades_vaga ?? common.length + missing.length
  const joined = (a: string | number | null | undefined, b: string | number | null | undefined) => `${a ?? '—'} · ${b ?? '—'}`
  return <section className="rs-card">
    <h2 className="rs-title">O que influenciou o score</h2>
    <div className="rs-two">
      <div>
        {match.sinais && match.sinais.length > 0 && <>
          <h3 className="rs-sub">Efeito de cada sinal</h3>
          <SignalBars signals={match.sinais}/>
          <p className="rs-note">Diferença no score estimado ao neutralizar cada grupo de sinais. Barras à direita elevam o score; à esquerda reduzem. Os efeitos não somam exatamente.</p>
        </>}
      </div>
      <div>
        <h3 className="rs-sub">Comparação direta</h3>
        <dl className="rs-facts">
          <Fact label="Habilidades da vaga no currículo">{common.length}{jobSkills ? ` de ${jobSkills}` : ''}</Fact>
          <Fact label="Anos de experiência (currículo · vaga)">{ok(match.anos_curriculo) ? number(match.anos_curriculo, 0) : 'não identificado'} · {ok(match.anos_vaga) ? number(match.anos_vaga, 0) : 'não informado'}</Fact>
          <Fact label="Formação (currículo · vaga)">{joined(match.formacao_curriculo, match.formacao_vaga)}</Fact>
          {ok(match.similaridade_textual) && <Fact label="Similaridade textual (TF-IDF)">{number(match.similaridade_textual, 2)}</Fact>}
        </dl>
        {(common.length > 0 || missing.length > 0) && <>
          <h3 className="rs-sub">Habilidades da vaga</h3>
          <div className="rs-chips">
            {common.map(s => <Badge key={`c-${s}`} variant="secondary" className="rs-chip-ok">✓ {s}</Badge>)}
            {missing.map(s => <Badge key={`m-${s}`} variant="outline" className="rs-chip-miss">{s}</Badge>)}
          </div>
          <p className="rs-note">Termos de um vocabulário extraído do dataset, buscados por correspondência literal. “Não encontrada” não significa que a pessoa não saiba.</p>
        </>}
      </div>
    </div>
  </section>
}

function ExperienceBlock({items}: {items: string[]}) {
  const fragments = items.filter(item => item.length <= SHORT_FRAGMENT)
  const passages = items.filter(item => item.length > SHORT_FRAGMENT)
  if (!items.length) return <p className="rs-muted">Sem experiência detalhada nesta extração.</p>
  return <>
    {fragments.length > 0 && <div className="rs-chips rs-chips-plain" aria-label="Cargos, empresas e períodos citados">{fragments.map((item, i) => <span key={i} className="rs-fragment">{item}</span>)}</div>}
    {passages.length > 0 && <ul className="rs-passages">{passages.map((item, i) => <li key={i}>{item}</li>)}</ul>}
  </>
}

export default function Results({result, onClear}: {result: Analysis | null; onClear: () => void}) {
  const navigate = useNavigate()
  if (!result) return <><PageHeading eyebrow="RESULTADO" title="Nenhuma análise nesta sessão.">Envie um currículo e uma vaga.</PageHeading><div className="empty-state"><ScanText/><Button asChild><Link to="/analise">Analisar currículo e vaga</Link></Button></div></>
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify({...result, report_notice: 'Resultado automatizado parcial ou completo conforme os estados informados. Não é decisão de contratação.'}, null, 2)], {type: 'application/json;charset=utf-8'}))
    const link = document.createElement('a'); link.href = url; link.download = 'talentmatch-relatorio.json'; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
  return <><PageHeading eyebrow="RESULTADO DA ANÁLISE" title="Resultados e evidências." action={<div className="button-row"><Button variant="outline" onClick={() => {onClear(); navigate('/analise')}}><Trash2 size={16}/>Limpar</Button><Button onClick={download}><Download size={16}/>Baixar relatório</Button></div>}>Resultado temporário de apoio à análise. A decisão final é humana.</PageHeading><AnalysisDetail result={result}/></>
}

export function AnalysisDetail({result}: {result: Analysis}) {
  const r = result.llm
  const ctx = result.ml_context
  const match = ctx?.disponivel ? ctx.compatibilidade_curriculo_vaga : null
  const completed = result.mode === 'live' && !!r && !result.llm_error
  const coverage = result.cobertura_requisitos
  const limitations = [...new Set([
    'Modelos treinados em inglês: textos em português são traduzidos automaticamente antes do ML e o desempenho nesse caso não foi validado.',
    ...(result.ml.warnings ?? []),
    ...(ctx?.disponivel ? [ctx.interpretacao] : []),
    ...result.warnings,
  ].filter(Boolean))]
  const stats = ctx?.disponivel ? ctx : null
  return <div className="rs">
    {result.mode === 'demo' && <Notice warning>Demonstração: a análise contextual é simulada, não gerada pelo LLM.</Notice>}
    {result.llm_error && <Notice warning>Análise contextual não concluída: {result.warnings.at(-1)} Isso é uma falha de processamento ou validação, não evidência de falta de competências. Os resultados ML são independentes.</Notice>}
    {!r && !result.llm_error && <Notice warning>Nenhuma análise contextual disponível nesta resposta.</Notice>}
    {r?.abstention_reason === 'partial_extraction' && <Notice warning>Extração parcial: alguns itens sugeridos pelo LLM não puderam ser verificados no texto e foram omitidos.</Notice>}

    <div className="rs-summary"><MatchCard match={match}/><AreaCard result={result}/></div>

    {match && <WhyCard match={match}/>}

    {completed && coverage && coverage.total > 0 && <RequirementCoverage coverage={coverage}/>}

    {r && <section className="rs-card">
      <h2 className="rs-title">{result.mode === 'demo' ? 'Extração simulada' : 'O que o currículo comprova'}</h2>
      {completed && <>
        <h3 className="rs-sub">Perfil profissional citado</h3>
        {r.perfil_profissional ? <><p className="rs-profile">{r.perfil_profissional.descricao}</p>{r.perfil_profissional.evidencia.trim().toLowerCase() !== r.perfil_profissional.descricao.trim().toLowerCase() && <blockquote className="rs-quote">{r.perfil_profissional.evidencia}</blockquote>}</> : <p className="rs-muted">Nenhuma designação profissional citável foi estabelecida.</p>}
      </>}
      <h3 className="rs-sub">Habilidades com menção literal{r.habilidades.length ? ` (${r.habilidades.length})` : ''}</h3>
      {r.habilidades.length ? <div className="rs-chips">{r.habilidades.map((s, i) => <Badge key={i} variant="secondary">{s}</Badge>)}</div> : <p className="rs-muted">Nenhuma habilidade verificada.</p>}
      <h3 className="rs-sub">Experiência citada</h3>
      <ExperienceBlock items={r.experiencia_profissional}/>
      <p className="rs-muted">Duração total explícita: {r.anos_experiencia === null ? 'não estabelecida' : `${r.anos_experiencia} anos; confirme no documento`}.</p>
    </section>}

    {r && <div className="rs-two rs-two-cards">
      <section className="rs-card">
        <h2 className="rs-title">Requisitos com evidência</h2>
        {r.requisitos_atendidos.length ? r.requisitos_atendidos.map((item, i) => <div key={i} className="rs-evidence"><h3>{item.requisito}</h3><blockquote className="rs-quote">{item.evidencia}</blockquote></div>) : <p className="rs-muted">Nenhuma associação publicada nesta extração.</p>}
      </section>
      <section className="rs-card">
        <h2 className="rs-title">Sem evidência suficiente</h2>
        {r.requisitos_sem_evidencia.length ? <div className="rs-chips">{r.requisitos_sem_evidencia.map((item, i) => <Badge key={i} variant="outline" className="rs-chip-miss">{item}</Badge>)}</div> : <p className="rs-muted">Nenhum item listado.</p>}
        <p className="rs-note">Não demonstrado não significa não possuir a competência.</p>
      </section>
    </div>}

    {ctx?.disponivel && ctx.requisitos_priorizados.length > 0 && <details className="rs-details">
      <summary>Similaridade lexical por requisito ({ctx.requisitos_priorizados.length})</summary>
      <ul className="rs-bars rs-bars-wide">{ctx.requisitos_priorizados.map((item, i) => <li key={i}><span className="rs-bars-label">{item.requisito}</span><span className="rs-bars-track"><span style={{width: `${Math.min(item.similaridade_cosseno, 1) * 100}%`}}/></span><span className="rs-bars-value">{number(item.similaridade_cosseno, 2)}</span></li>)}</ul>
      <p className="rs-note">Similaridade TF-IDF não confirma atendimento nem ausência de habilidade.</p>
    </details>}

    {r && (r.justificativa || r.pontos_fortes.length > 0) && <details className="rs-details">
      <summary>Fundamentação e limites da extração</summary>
      <p>{r.justificativa}</p>
    </details>}

    <details className="rs-details" id="limitacoes">
      <summary>Detalhes estatísticos e limitações</summary>
      {stats && <dl className="rs-facts rs-facts-inline">
        <Fact label="Entropia da área">{number(stats.entropia_normalizada)}</Fact>
        <Fact label="Margem da área">{number(stats.margem_top1_top2)}</Fact>
        {match && <Fact label="Entropia do matching">{number(match.entropia_normalizada)}</Fact>}
        {match && <Fact label="Margem do matching">{number(match.margem_top1_top2)}</Fact>}
        <Fact label="Similaridade ao centróide de área">{number(stats.deteccao_fora_distribuicao.similaridade_ao_centroide_mais_proximo, 3)} (limiar {number(stats.deteccao_fora_distribuicao.limiar_validado, 3)})</Fact>
      </dl>}
      <ul>{limitations.map((text, i) => <li key={i}>{text}</li>)}</ul>
      <p>Etapa contextual: {result.llm_error ? `não concluída (${result.llm_error})` : r ? result.mode === 'demo' ? 'simulada' : 'extração recebida e validada; consulte limitações' : 'indisponível'}.</p>
      <p>Remoções automáticas: {String(result.privacy.resume_redactions)} no currículo; {String(result.privacy.job_redactions)} na vaga. Minimização não garante anonimização.</p>
    </details>
  </div>
}
