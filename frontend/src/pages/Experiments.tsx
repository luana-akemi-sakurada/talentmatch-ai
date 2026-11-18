import { ErrorState, Loading, PageHeading } from '@/components/common'
import { useResource } from '@/hooks/use-resource'
import { getEvaluation } from '@/services/evaluation'
import type { Interval, TaskEvaluation } from '@/services/evaluation'
import '../results.css'
import '../experiments.css'

const pct = (v: number, digits = 1) => `${(v * 100).toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits})}%`
const num = (v: number, digits = 3) => v.toLocaleString('pt-BR', {minimumFractionDigits: digits, maximumFractionDigits: digits})
const BAND = {compatibilidade_fraca: 'Fraca', compatibilidade_media: 'Média', compatibilidade_forte: 'Forte'} as Record<string, string>
const label = (name: string) => BAND[name] ?? (name === 'HR' ? 'RH (HR)' : name.replaceAll('-', ' ').toLowerCase().replace(/(^|\s)\S/g, c => c.toUpperCase()))
const SIGNALS = {cos_tfidf: 'Similaridade lexical (TF-IDF)', cos_lsa: 'Similaridade temática (LSA)', n_job_skills: 'Habilidades listadas na vaga', n_resume_skills: 'Habilidades encontradas no currículo', n_common_skills: 'Habilidades em comum', skill_recall: 'Habilidades da vaga cobertas', skill_jaccard: 'Sobreposição de habilidades', area_dot: 'Concordância de área', resume_prob_at_job_area: 'Currículo na área da vaga', job_area_conf: 'Clareza da área da vaga', resume_area_conf: 'Clareza da área do currículo', title_overlap: 'Termos do cargo no currículo', title_any: 'Cargo citado no currículo', resume_years: 'Anos de experiência do currículo', job_years: 'Anos exigidos pela vaga', years_gap: 'Diferença de anos (currículo − vaga)', resume_edu: 'Formação do currículo', job_edu: 'Formação exigida pela vaga', edu_gap: 'Diferença de formação'} as Record<string, string>
const BASELINE = {classe_majoritaria: 'Sempre a faixa mais comum', tfidf_concatenado_logistica: 'Modelo anterior (textos concatenados)'} as Record<string, string>

function Kpi({title, value, range, hint}: {title: string; value: string; range?: string; hint: string}) {
  return <div className="ev-kpi"><span className="ev-kpi-title">{title}</span><strong>{value}</strong>{range && <span className="ev-kpi-range">IC 95%: {range}</span>}<span className="ev-kpi-hint">{hint}</span></div>
}
const range = (i: Interval, f: (v: number) => string) => `${f(i.low)} a ${f(i.high)}`

function Confusion({matrix}: {matrix: {labels: string[]; counts: number[][]}}) {
  return <div className="ev-table-wrap"><table className="ev-matrix">
    <caption className="sr-only">Matriz de confusão: linhas são o rótulo real, colunas a previsão do modelo</caption>
    <thead><tr><td className="ev-corner">Real ↓ · Previsto →</td>{matrix.labels.map(l => <th key={l} scope="col">{label(l)}</th>)}</tr></thead>
    <tbody>{matrix.counts.map((row, i) => {
      const total = row.reduce((a, b) => a + b, 0)
      return <tr key={i}><th scope="row">{label(matrix.labels[i])}<small>{total} casos</small></th>{row.map((v, j) => {
        const share = total ? v / total : 0
        return <td key={j} className={i === j ? 'is-diagonal' : ''} style={{background: `rgba(34,105,79,${(share * 0.8).toFixed(3)})`, color: share > 0.5 ? '#fff' : '#24362e'}}><strong>{total ? pct(share, 0) : '—'}</strong><small>{v}</small></td>
      })}</tr>
    })}</tbody>
  </table></div>
}

function Section({title, lead, task, primary}: {title: string; lead: string; task: TaskEvaluation; primary?: boolean}) {
  const e = task.evaluation
  const test = task.splits.test
  const report = task.classes.map(c => ({name: c, row: e.classification_report[c]})).filter((x): x is {name: string; row: {precision: number; recall: number; 'f1-score': number; support: number}} => typeof x.row === 'object')
  const baselines = e.baselines ? [{name: 'Modelo atual', accuracy: e.metrics.accuracy.point, f1: e.metrics.f1_macro.point, current: true}, ...Object.entries(e.baselines).map(([key, b]) => ({name: BASELINE[key] ?? key, accuracy: b.accuracy, f1: b.f1_macro, current: false}))] : null
  const importance = e.feature_importance?.slice(0, 6)
  const topImportance = Math.max(...(importance?.map(f => f.importance) ?? [0]), 0.001)
  return <section className={`rs-card ev-section ${primary ? 'is-primary' : ''}`}>
    <h2 className="rs-title">{title}</h2>
    <p className="ev-lead">{lead}</p>
    <div className="ev-kpis">
      <Kpi title="Acurácia" value={pct(e.metrics.accuracy.point)} range={range(e.metrics.accuracy, v => pct(v, 0))} hint="Porcentagem de acertos no teste."/>
      <Kpi title="F1 macro" value={num(e.metrics.f1_macro.point, 2)} range={range(e.metrics.f1_macro, v => num(v, 2))} hint="Acerto médio entre classes, de 0 a 1; penaliza ignorar as raras."/>
      {e.regression && <Kpi title="R² do score" value={num(e.regression.r2.point, 2)} range={range(e.regression.r2, v => num(v, 2))} hint="Quanto da variação do score o modelo explica (1 = tudo)."/>}
      {e.regression && <Kpi title="Erro médio do score" value={num(e.regression.mae.point, 3)} range={range(e.regression.mae, v => num(v, 3))} hint={`Em pontos de score. O score varia ~${num(e.regression.score_std_teste, 3)} no teste.`}/>}
    </div>
    <p className="rs-note">Teste com {test.rows.toLocaleString('pt-BR')} exemplos{test.jobs ? ` (${test.jobs} vagas e ${test.resume_groups} currículos que o modelo nunca viu)` : ` (${test.resume_groups} currículos que o modelo nunca viu)`}.</p>

    {baselines && <><h3 className="rs-sub">Comparação com alternativas simples</h3>
      <ul className="rs-bars ev-baselines">{baselines.map(b => <li key={b.name} className={b.current ? 'is-top' : ''}>
        <span className="rs-bars-label">{b.name}</span>
        <span className="rs-bars-track"><span style={{width: `${b.accuracy * 100}%`}}/></span>
        <span className="rs-bars-value">{pct(b.accuracy, 0)}</span>
        <span className="ev-f1">F1 {num(b.f1, 2)}</span>
      </li>)}</ul>
      <p className="rs-note">Barras mostram a acurácia. Se o modelo não supera “sempre a faixa mais comum”, a faixa informa pouco além da frequência do dataset.</p></>}

    <h3 className="rs-sub">Onde o modelo acerta e erra</h3>
    <Confusion matrix={e.confusion_matrix}/>
    <p className="rs-note">Cada linha soma 100% dos casos reais daquela classe. A diagonal (destacada) são os acertos; o número pequeno é a contagem.</p>

    <div className="ev-two">
      <div>
        <h3 className="rs-sub">Desempenho por classe</h3>
        <div className="ev-table-wrap"><table className="ev-table">
          <thead><tr><th>Classe</th><th>Precisão</th><th>Recall</th><th>F1</th><th>Casos</th></tr></thead>
          <tbody>{report.map(({name, row}) => <tr key={name}><th scope="row">{label(name)}</th><td>{num(row.precision, 2)}</td><td>{num(row.recall, 2)}</td><td>{num(row['f1-score'], 2)}</td><td>{row.support}</td></tr>)}</tbody>
        </table></div>
        <p className="rs-note">Precisão: dos que o modelo apontou, quantos eram da classe. Recall: dos que eram da classe, quantos ele encontrou.</p>
      </div>
      {importance && <div>
        <h3 className="rs-sub">O que mais pesa no score</h3>
        <ul className="rs-bars ev-importance">{importance.map(f => <li key={f.feature}><span className="rs-bars-label">{SIGNALS[f.feature] ?? f.label}</span><span className="rs-bars-track"><span style={{width: `${Math.max(f.importance, 0) / topImportance * 100}%`}}/></span></li>)}</ul>
        <p className="rs-note">Importância por permutação: quanto o modelo piora quando o sinal é embaralhado.</p>
      </div>}
    </div>

    <details className="ev-details">
      <summary>Detalhes técnicos</summary>
      <div className="ev-table-wrap"><table className="ev-table">
        <caption>Divisão dos dados (nenhum currículo{test.jobs ? ' ou vaga' : ''} aparece em dois conjuntos)</caption>
        <thead><tr><th>Conjunto</th><th>Exemplos</th><th>Currículos</th>{test.jobs != null && <th>Vagas</th>}</tr></thead>
        <tbody>{Object.entries(task.splits).map(([name, s]) => <tr key={name}><th scope="row">{({train: 'Treino', calibration: 'Calibração', validation: 'Validação', test: 'Teste'} as Record<string, string>)[name] ?? name}</th><td>{s.rows.toLocaleString('pt-BR')}</td><td>{s.resume_groups.toLocaleString('pt-BR')}</td>{s.jobs != null && <td>{s.jobs}</td>}</tr>)}</tbody>
      </table></div>
      <p>Qualidade das probabilidades (menor é melhor): {Object.entries(e.probability_quality).map(([name, q]) => `${name === 'calibrated' ? 'calibradas' : 'sem calibração'}: log loss ${num(q.log_loss, 3)}, Brier ${num(q.multiclass_brier, 3)}`).join(' · ')}.</p>
      {e.interval_80_coverage_test != null && <p>O intervalo de 80% do score contém o valor real em {pct(e.interval_80_coverage_test)} dos casos de teste (esperado: ~80%).</p>}
      <p>Modelo: {task.model}. Intervalos: {e.bootstrap.iterations} reamostras (bootstrap). {e.bootstrap.scope}</p>
    </details>
  </section>
}

export default function Experiments() {
  const resource = useResource(getEvaluation)
  const data = resource.data
  const compat = data?.tasks.compatibility
  const area = data?.tasks.area
  const compatLead = compat && `Em currículos e vagas que o modelo nunca viu, ele acertou a faixa (Fraca, Média ou Forte) em ${pct(compat.evaluation.metrics.accuracy.point, 0)} dos casos${compat.evaluation.baselines ? `; sempre chutar a faixa mais comum acertaria ${pct(compat.evaluation.baselines.classe_majoritaria.accuracy, 0)}` : ''}. O ganho é modesto: use o score e os sinais como apoio, não como decisão.`
  const areaLead = area && `Acertou a área profissional em ${pct(area.evaluation.metrics.accuracy.point, 0)} dos currículos de teste. O F1 macro (${num(area.evaluation.metrics.f1_macro.point, 2)}) é menor porque conta igualmente as áreas raras, que têm poucos exemplos.`
  return <>
    <PageHeading eyebrow="MODELOS E VALIDAÇÃO" title="Avaliação de área e compatibilidade.">Como os dois modelos foram testados e o que dá para esperar deles.</PageHeading>
    {resource.loading && <Loading/>}
    {resource.error && <ErrorState message={resource.error} retry={resource.reload}/>}
    {data && compat && area && <div className="rs ev">
      <p className="ev-meta">Dataset {data.dataset} · execução {data.run_id} · scikit-learn {data.sklearn_version}</p>
      <Section primary title="Compatibilidade currículo–vaga" lead={compatLead!} task={compat}/>
      <Section title="Área profissional derivada" lead={areaLead!} task={area}/>
      <details className="rs-details">
        <summary>Como os dados foram separados</summary>
        <p>{data.split_strategy}</p>
        <p>Currículos com empate entre categorias excluídos da tarefa de área: {data.area_candidates_excluded_ambiguous}.</p>
      </details>
      <details className="rs-details" open>
        <summary>Limitações</summary>
        <ul>{data.limitations.map(t => <li key={t}>{t}</li>)}</ul>
      </details>
    </div>}
  </>
}
