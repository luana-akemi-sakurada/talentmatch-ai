import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, FileText, FlaskConical, LoaderCircle, ShieldCheck, Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Notice, PageHeading } from '@/components/common'
import { api } from '@/services/api'
import type { Analysis } from '@/types'
import '../results.css'
import '../analyze.css'

export const EXAMPLE_RESUME = 'EXEMPLO FICTÍCIO PARA DEMONSTRAÇÃO\nData analyst with 3 years of experience using Python, pandas and SQL for retail reporting. Developed Power BI dashboards and data quality checks. Collaborated with business teams using Git.'
export const EXAMPLE_JOB = 'Vaga: Analista de dados (exemplo fictício)\nRequisitos:\n- Python\n- SQL\n- Power BI\nDesejáveis:\n- AWS\n- comunicação com equipes de negócio'

export default function Analyze({onResult, offline = false}: {onResult: (result: Analysis) => void; offline?: boolean}) {
  const [text,setText] = useState('')
  const [job,setJob] = useState('')
  const [files,setFiles] = useState<File[]>([])
  const mode = offline ? 'demo' : 'live'
  const [consent,setConsent] = useState(false)
  const [error,setError] = useState('')
  const [busy,setBusy] = useState(false)
  const controller = useRef<AbortController | null>(null)
  const navigate = useNavigate()
  useEffect(() => () => controller.current?.abort(), [])
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setBusy(true)
    controller.current = new AbortController()
    const data = new FormData()
    data.set('job_description',job); data.set('mode',mode)
    if (files[0]) data.set('file',files[0]); else data.set('resume_text',text)
    try { const result = await api.analyze(data,controller.current.signal); onResult(result); navigate('/resultado') }
    catch(e) { if ((e as Error).name !== 'AbortError') setError((e as Error).message) }
    finally { setBusy(false) }
  }
  const steps = [
    ['Envie os textos', 'Currículo e descrição da vaga.'],
    ['O modelo estima', 'Compatibilidade e área profissional.'],
    [mode === 'demo' ? 'Contexto simulado' : 'O LLM cita evidências', mode === 'demo' ? 'Correspondência literal, sem chamada externa.' : 'Trechos do currículo que sustentam cada requisito.'],
  ]
  return <><PageHeading eyebrow="ANÁLISE DE CURRÍCULO" title="Uma oportunidade. Um novo contexto." action={<Button type="button" variant="outline" disabled={busy} onClick={() => {setText(EXAMPLE_RESUME);setJob(EXAMPLE_JOB);setFiles([]);setError('')}}><FlaskConical size={16}/>Usar exemplo fictício</Button>}>Reúna o currículo e a vaga para ver a compatibilidade estimada e as evidências encontradas no texto.</PageHeading>
    <ol className="an-steps" aria-label="Etapas da análise">{steps.map(([title, text], i) => <li key={title}><span>{i + 1}</span><div><strong>{title}</strong><p>{text}</p></div></li>)}</ol>
    <form className="an" onSubmit={submit} aria-busy={busy}>
      <div className="an-grid">
        <section className="rs-card an-card">
          <header className="an-head"><span className="an-badge">1</span><div><h2>Currículo</h2><p>Envie um documento ou cole o texto.</p></div></header>
          <FileDrop files={files} onChange={setFiles} disabled={busy}/>
          <div className="an-or"><span>ou cole o texto</span></div>
          <label className="an-label" htmlFor="resume">Texto do currículo</label>
          <textarea id="resume" aria-describedby="resume-hint" maxLength={40000} rows={12} value={text} disabled={files.length > 0 || busy} onChange={e => setText(e.target.value)} placeholder="Experiência profissional, formação e competências…" required={!files.length}/>
          <p id="resume-hint" className="an-hint">{files.length ? 'Arquivo selecionado. Remova-o para usar o texto colado.' : `${text.length.toLocaleString('pt-BR')} / 40.000 caracteres. PDFs precisam ter texto selecionável; não há OCR.`}</p>
        </section>
        <section className="rs-card an-card">
          <header className="an-head"><span className="an-badge">2</span><div><h2>Vaga</h2><p>Os requisitos são a referência da análise.</p></div></header>
          <label className="an-label" htmlFor="job">Descrição da vaga</label>
          <textarea id="job" maxLength={16000} rows={15} required value={job} disabled={busy} onChange={e => setJob(e.target.value)} placeholder="Cargo, responsabilidades, requisitos essenciais e desejáveis…"/>
          <p className="an-hint">{job.length.toLocaleString('pt-BR')} / 16.000 caracteres. Dica: comece pela linha do cargo.</p>
          <p className="an-tip"><ShieldCheck size={16}/>Prefira requisitos objetivos e ligados ao trabalho. Evite características pessoais como critério.</p>
        </section>
      </div>
      {offline && <Notice warning>Demonstração offline: o contexto é simulado e não há chamada ao LLM.</Notice>}
      {error && <Notice warning>{error}</Notice>}
      <section className="rs-card an-submit">
        {mode === 'live' && <label className="an-consent"><input type="checkbox" required checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)}/><span>Tenho autorização para processar estes dados e sei que os textos, com dados pessoais minimizados, serão enviados ao provedor externo do LLM. A remoção automática é limitada.</span></label>}
        <div className="an-actions">
          <p><ShieldCheck size={16}/>{mode === 'demo' ? 'Sem chamada externa' : 'Envio ao provedor externo do LLM'} · sem armazenamento permanente · revisão humana obrigatória</p>
          <Button size="lg" disabled={busy || (mode === 'live' && !consent)} type="submit">{busy ? <><LoaderCircle size={18} className="spin"/>Processando…</> : <>Analisar currículo<ArrowRight size={18}/></>}</Button>
        </div>
      </section>
      <div role="status" className="sr-only">{busy ? 'Classificando currículo e processando análise. Aguarde.' : ''}</div>
    </form></>
}

export function FileDrop({files,onChange,disabled=false}: {files:File[];onChange:(files:File[])=>void;disabled?:boolean}) {
  const [error,setError] = useState('')
  const [over,setOver] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const hintId = useId()
  function choose(list: File[]) {
    if (!list.length) return
    if (list.length > 1) {setError('Selecione apenas um currículo.'); return}
    if (list.some(f => !/\.(pdf|txt)$/i.test(f.name) || f.size > 5*1024*1024)) {setError('Use PDF ou TXT com até 5 MB.');return}
    setError('');onChange(list)
  }
  return <>
    {files.length === 0 && <div className={`an-drop ${disabled ? 'is-disabled' : ''} ${over ? 'is-over' : ''}`} onDragOver={e => {e.preventDefault(); setOver(true)}} onDragLeave={() => setOver(false)} onDrop={e => {e.preventDefault(); setOver(false); if(!disabled) choose(Array.from(e.dataTransfer.files))}}>
      <Upload size={22} aria-hidden="true"/>
      <div><strong>Arraste o currículo até aqui</strong><p id={hintId}>PDF ou TXT · até 5 MB</p></div>
      <Button type="button" variant="outline" disabled={disabled} aria-describedby={hintId} onClick={() => input.current?.click()}>Selecionar arquivo</Button>
      <input ref={input} className="sr-only" tabIndex={-1} type="file" aria-describedby={hintId} aria-label="Enviar currículo" accept=".pdf,.txt" disabled={disabled} onChange={e => {choose(Array.from(e.target.files || [])); e.target.value=''}}/>
    </div>}
    <div aria-live="polite">{files.map((file,i) => <div className="an-file" key={i}><FileText size={18}/><span><strong>{file.name}</strong><small>{(file.size/1024).toFixed(1)} KB · pronto para análise</small></span><Button type="button" variant="ghost" size="icon" disabled={disabled} aria-label="Remover arquivo" onClick={() => onChange(files.filter((_,index) => index !== i))}><X size={16}/></Button></div>)}</div>
    {error && <p role="alert" className="an-error">{error}</p>}
  </>
}
