import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, FileText, FlaskConical, LoaderCircle, ShieldCheck, Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Notice, PageHeading } from '@/components/common'
import { api } from '@/services/api'
import type { Analysis } from '@/types'

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
  return <><PageHeading eyebrow="ANÁLISE DE CURRÍCULO" title="Uma oportunidade. Um novo contexto." action={<Button type="button" variant="outline" disabled={busy} onClick={() => {setText(EXAMPLE_RESUME);setJob(EXAMPLE_JOB);setFiles([]);setError('')}}><FlaskConical size={16}/>Usar exemplo fictício</Button>}>Reúna o currículo e a vaga para explorar competências e evidências.</PageHeading>
    <ol className="analysis-guide" aria-label="Etapas da análise"><li><span>01</span><div><strong>Currículo + vaga</strong><p>Documento ou texto, com os requisitos da oportunidade.</p></div></li><li><span>02</span><div><strong>Classificação ML real</strong><p>O modelo treinado estima a área profissional.</p></div></li><li><span>03</span><div><strong>{mode === 'demo' ? 'Contexto simulado' : 'Análise por LLM'}</strong><p>{mode === 'demo' ? 'Correspondência literal; sem chamada externa.' : 'Textos minimizados enviados ao provedor.'}</p></div></li></ol>
    <Notice>Os arquivos são processados para esta solicitação, sem armazenamento permanente. Revise e remova dados pessoais antes do envio.</Notice>
    <form onSubmit={submit} aria-busy={busy}>
      <div className="form-grid"><Card><CardContent className="panel-content"><div className="form-section-title"><span className="step-marker">01</span><div><h2>O currículo</h2><p className="muted text-sm">Envie um documento ou cole o texto.</p></div></div><FileDrop files={files} onChange={setFiles} disabled={busy}/><div className="or-divider"><span>ou cole o texto</span></div><label className="field-label" htmlFor="resume">Texto do currículo</label><textarea id="resume" aria-describedby="resume-hint" maxLength={40000} rows={9} value={text} disabled={files.length > 0 || busy} onChange={e => setText(e.target.value)} placeholder="Experiência profissional, formação e competências…" required={!files.length}/><p id="resume-hint" className="field-hint">{files.length ? 'Arquivo selecionado. Remova-o para utilizar o texto colado.' : `${text.length.toLocaleString('pt-BR')} / 40.000 caracteres. PDFs precisam conter texto selecionável; não há OCR.`}</p></CardContent></Card>
      <Card><CardContent className="panel-content"><div className="form-section-title"><span className="step-marker">02</span><div><h2>A oportunidade</h2><p className="muted text-sm">Os requisitos serão a referência da análise.</p></div></div><label className="field-label" htmlFor="job">Descrição da vaga</label><textarea id="job" maxLength={16000} rows={15} required value={job} disabled={busy} onChange={e => setJob(e.target.value)} placeholder="Descreva o papel, as responsabilidades e os requisitos essenciais e desejáveis…"/><p className="field-hint">{job.length.toLocaleString('pt-BR')} / 16.000 caracteres</p><div className="tip-box"><ShieldCheck size={18}/><p>Prefira requisitos objetivos e relacionados ao trabalho. Evite características pessoais como critério.</p></div></CardContent></Card></div>
      {offline && <Notice warning>Demonstração offline explícita. O contexto é simulado; não há chamada ao LLM.</Notice>}
      <Card className="mode-card"><CardContent className="panel-content"><h2>{offline ? 'Demonstração offline' : 'Análise com LLM'}</h2><p className="muted text-sm">{offline ? 'ML local real e contexto simulado para apresentação.' : 'O ML local e a análise contextual têm origens separadas. Falhas do provedor não ativam simulação.'}</p>
      {mode === 'live' && <label className="consent"><input type="checkbox" required checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)}/><span>Tenho autorização para processar estes dados e estou ciente do envio dos textos minimizados ao provedor externo. A remoção automática de dados pessoais é limitada.</span></label>}
      </CardContent></Card>
      {error && <Notice warning>{error}</Notice>}
      <div className="form-actions"><p><ShieldCheck size={16}/>{mode === 'demo' ? 'Sem chamada externa · revisão humana obrigatória' : 'Envio ao provedor externo · revisão humana obrigatória'}</p><Button size="lg" disabled={busy || (mode === 'live' && !consent)} type="submit">{busy ? <><LoaderCircle size={18} className="spin"/>Processando análise…</> : <>Analisar currículo<ArrowRight size={18}/></>}</Button></div><div role="status" className="sr-only">{busy ? 'Classificando currículo e processando análise. Aguarde.' : ''}</div>
    </form></>
}

export function FileDrop({files,onChange,multiple=false,disabled=false}: {files:File[];onChange:(files:File[])=>void;multiple?:boolean;disabled?:boolean}) {
  const [error,setError] = useState('')
  const input = useRef<HTMLInputElement>(null)
  const hintId = useId()
  function choose(list: File[]) {
    if (!list.length) return
    if (list.length > (multiple ? 5 : 1)) {setError(multiple ? 'Selecione até 5 currículos.' : 'Selecione apenas um currículo.'); return}
    if (list.some(f => !/\.(pdf|txt)$/i.test(f.name) || f.size > 5*1024*1024)) {setError('Use PDF ou TXT com até 5 MB por arquivo.');return}
    setError('');onChange(list)
  }
  return <><div className={`drop-zone ${disabled ? 'disabled' : ''}`} onDragOver={e => e.preventDefault()} onDrop={e => {e.preventDefault();if(!disabled) choose(Array.from(e.dataTransfer.files))}}><div className="upload-icon"><Upload size={24}/></div><strong>{multiple ? 'Selecione os currículos para comparar' : 'Arraste seu currículo até aqui'}</strong><p id={hintId}>PDF ou TXT · até 5 MB{multiple ? ' por arquivo · 2 a 5 arquivos' : ''}</p><Button type="button" variant="outline" disabled={disabled} aria-describedby={hintId} onClick={() => input.current?.click()}>Selecionar {multiple ? 'arquivos' : 'arquivo'}</Button><input ref={input} className="sr-only" tabIndex={-1} type="file" aria-describedby={hintId} aria-label={multiple ? 'Enviar currículos' : 'Enviar currículo'} accept=".pdf,.txt" multiple={multiple} disabled={disabled} onChange={e => {choose(Array.from(e.target.files || [])); e.target.value=''}}/></div><div aria-live="polite">{files.map((file,i) => <div className="file-feedback" key={i}><FileText size={18}/><span><strong>{multiple ? `Candidato ${i+1} · ` : ''}{file.name}</strong><small>{(file.size/1024).toFixed(1)} KB · pronto para análise</small></span><Button type="button" variant="ghost" size="icon" disabled={disabled} aria-label={`Remover arquivo ${i+1}`} onClick={() => onChange(files.filter((_,index) => index !== i))}><X size={16}/></Button></div>)}</div>{error && <p role="alert" className="field-error">{error}</p>}</>
}
