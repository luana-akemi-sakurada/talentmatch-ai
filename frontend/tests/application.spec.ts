import { test, expect, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { readFileSync } from 'node:fs'
import { modelName } from '../src/lib/format'
import type { Analysis } from '../src/types'

async function capture(page: Page, path: string) {
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({path, fullPage:true})
}

test('fluxo principal usa LLM sem seletor e exemplo não ativa simulação', async ({page}) => {
  await page.goto('/analise')
  await expect(page.getByRole('radio')).toHaveCount(0)
  await expect(page.getByRole('combobox')).toHaveCount(0)
  await expect(page.getByRole('heading',{name:'Análise com LLM',exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await expect(page.getByRole('button',{name:'Analisar currículo',exact:true})).toBeDisabled()
  await page.getByRole('checkbox').check()
  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/analyze') && response.request().method() === 'POST')
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  expect((await (await responsePromise).json()).llm_error).toBe('llm_not_configured')
  await expect(page.getByText('Análise contextual indisponível.',{exact:true})).toBeVisible()
  await expect(page.getByText('Demonstração simulada.',{exact:true})).toHaveCount(0)
  await expect(page.getByRole('heading',{name:'Classificação profissional'})).toBeVisible()
  await expect(page.getByRole('navigation',{name:'Navegação principal'}).getByRole('link',{name:/Demonstração/})).toHaveCount(0)
})

test('perfil contextual e resultados essenciais separados, sem perguntas', async ({page,request}) => {
  const fixture = JSON.parse(readFileSync('../backend/tests/fixtures/contextual.json','utf8'))
  const response = await request.post('http://127.0.0.1:8011/api/analyze',{form:{
    resume_text:fixture.resume,job_description:fixture.job,mode:'demo'}})
  const data = await response.json() as Analysis
  const mlCategory = data.ml.predicted_area.replaceAll('-',' ')
  data.mode = 'live'; data.warnings = []
  data.llm!.nota_aderencia = null
  data.llm!.perfil_profissional = fixture.provider.perfil_profissional
  await page.route('**/api/analyze',route=>{
    expect(route.request().postData()).toContain('live')
    return route.fulfill({json:data})
  })
  await page.setViewportSize({width:390,height:844})
  await page.goto('/analise')
  await page.getByLabel('Texto do currículo',{exact:true}).fill(fixture.resume)
  await page.getByLabel('Descrição da vaga',{exact:true}).fill(fixture.job)
  await page.getByRole('checkbox').check()
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page.getByText('Desenvolvedora Backend Java',{exact:true})).toBeVisible()
  await expect(page.getByText(mlCategory,{exact:true}).first()).toBeVisible()
  await expect(page.getByText(/Cobertura total indeterminada/)).toBeVisible()
  await expect(page.getByRole('heading',{name:'Perguntas para entrevista'})).toHaveCount(0)
  await expect(page.locator('.score-number')).toHaveCount(0)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true)
  const audit = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()
  expect(audit.violations).toEqual([])
})

test('vetor vazio tem abstenção visível sem categoria ou probabilidade inventada', async ({page}) => {
  await page.goto('/demonstracao')
  await page.getByLabel('Texto do currículo',{exact:true}).fill('zzqxv zzqxv')
  await page.getByLabel('Descrição da vaga',{exact:true}).fill('Python SQL')
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page).toHaveURL(/resultado/)
  await expect(page.getByText('INDETERMINADA',{exact:true})).toBeVisible()
  await expect(page.getByRole('alert').filter({hasText:'vetor vazio'})).toBeVisible()
  await expect(page.locator('.probability-list .probability-label')).toHaveCount(0)
  await expect(page.getByText('ML · abstenção',{exact:true})).toBeVisible()
})

test('contrato LLM sem nota preserva evidências e mostra abstenção em vez de zero', async ({page,request}) => {
  // Real local classifier; contextual response below is an explicitly mocked API contract.
  const response = await request.post('http://127.0.0.1:8011/api/analyze', {form:{
    resume_text:'Experiência com Python e SQL.', job_description:'Python SQL AWS', mode:'demo'}})
  expect(response.ok()).toBe(true)
  const data = await response.json() as Analysis
  data.mode = 'live'
  data.llm!.nota_aderencia = null
  data.llm!.abstention_reason = 'score_not_validated'
  data.llm!.resumo = 'Fixture de teste: menções verificadas a Python e SQL.'
  data.warnings.push('Abstenção de pontuação: não significa aderência zero.')
  await page.route('**/api/analyze',route => route.fulfill({json:data}))
  await page.goto('/analise')
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await page.getByRole('checkbox').check()
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page).toHaveURL(/resultado/)
  await expect(page.locator('.score-card')).toContainText('Cobertura total indeterminada')
  await expect(page.getByRole('progressbar')).toHaveCount(0)
  await expect(page.getByRole('heading',{name:'Perguntas para entrevista'})).toHaveCount(0)
  await expect(page.locator('.score-number')).toHaveCount(0)
  await expect(page.getByRole('heading',{name:'Requisitos com evidências'})).toBeVisible()
  await expect(page.getByText('Fixture de teste: menções verificadas a Python e SQL.')).toBeVisible()
  const audit = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()
  expect(audit.violations).toEqual([])
})

test('cobertura documental mostra contagens fórmula e progresso sem nota LLM', async ({page,request}) => {
  const response = await request.post('http://127.0.0.1:8011/api/analyze',{form:{
    resume_text:'Experiência em Python.',job_description:'Requisitos: Python; SQL',mode:'demo'}})
  const data = await response.json() as Analysis
  data.mode='live'; data.llm!.nota_aderencia=null
  data.cobertura_requisitos={status:'calculada',lista_completa:true,com_evidencia:1,
    sem_evidencia:1,indeterminados:0,total:2,percentual:50,formula:'1 / 2 × 100',motivos:[],
    requisitos:[{id:'req_python',texto:'Python',componentes:['Python'],referencias_vaga:['Requisitos: Python; SQL'],
      estado:'evidencia_verificada',evidencias:['Experiência em Python.'],motivo:null}]}
  await page.route('**/api/analyze',route=>route.fulfill({json:data}))
  await page.goto('/analise')
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await page.getByRole('checkbox').check()
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  const card=page.locator('.score-card')
  await expect(card).toContainText('1 de 2 requisitos com evidência')
  await expect(card).toContainText('50,0% de cobertura documental')
  await expect(card).toContainText('Sem pesos')
  await expect(card).toContainText('Não comprova competências nem representa chance de contratação')
  await expect(page.getByRole('progressbar')).toHaveAttribute('aria-valuenow','50')
  await card.getByText('Conferir requisitos e evidências').click()
  await expect(card.getByText('Experiência em Python.',{exact:true})).toBeVisible()
  const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()
  expect(audit.violations).toEqual([])
})

test('métricas correspondem ao CSV, com escalas e limitações explícitas', async ({page}) => {
  await page.goto('/experimentos')
  const rows = readFileSync('../models/comparacao_modelos.csv','utf8').trim().split(/\r?\n/).slice(1)
  for (const line of rows) {
    const [name, accuracy, f1] = line.split(',')
    const row = page.getByRole('row').filter({has: page.getByRole('rowheader',{name: new RegExp(modelName(name).replace(/[()]/g,'\\$&'))})})
    await expect(row.getByRole('cell',{name:`${(Number(accuracy)*100).toFixed(2).replace('.',',')}%`,exact:true})).toBeVisible()
    await expect(row.getByRole('cell',{name:Number(f1).toFixed(4).replace('.',','),exact:true})).toBeVisible()
  }
  await expect(page.getByText('Escala: 0% a 100%',{exact:true})).toBeVisible()
  await expect(page.getByText('Escala: 0 a 1',{exact:true})).toBeVisible()
  await expect(page.getByText(/O mesmo teste foi usado para selecionar e avaliar/)).toBeVisible()
  await expect(page.getByText(/Precision e recall não foram salvos: estão indisponíveis/)).toBeVisible()
  await capture(page, 'test-results/experiments-desktop.png')
})

for (const path of ['/', '/analise', '/comparacao', '/experimentos', '/etica']) {
  test(`acessibilidade automática: ${path}`, async ({page}) => {
    await page.goto(path)
    await expect(page.getByText('Classificador disponível',{exact:true})).toBeVisible()
    if (path === '/experimentos') await expect(page.getByRole('cell',{name:'0,6896',exact:true})).toBeVisible()
    const audit = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()
    expect(audit.violations.map(v => ({id:v.id,nodes:v.nodes.map(n=>({html:n.html,summary:n.failureSummary}))})), path).toEqual([])
  })
}
test('acessibilidade do resultado demonstrativo', async ({page}) => {
  await page.goto('/demonstracao')
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await capture(page, 'test-results/analysis-desktop.png')
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page).toHaveURL(/resultado/)
  await expect(page.getByText(/Não avaliada no modo demonstrativo/)).toBeVisible()
  const audit = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()
  expect(audit.violations.map(v => ({id:v.id,nodes:v.nodes.map(n=>({html:n.html,summary:n.failureSummary}))}))).toEqual([])
})

test('menu móvel mantém foco, fecha com Escape e reflow em 320px', async ({page}) => {
  await page.setViewportSize({width:320,height:740})
  await page.goto('/demonstracao')
  await expect(page.getByRole('navigation',{name:'Navegação principal'})).toBeHidden()
  const open = page.getByRole('button',{name:'Abrir navegação'})
  await open.click()
  await expect(page.getByRole('button',{name:'Fechar menu'})).toBeFocused()
  await page.getByRole('link',{name:'Conheça os princípios'}).focus()
  await page.keyboard.press('Tab')
  await expect(page.locator('.brand')).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(page.getByRole('link',{name:'Conheça os princípios'})).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(open).toHaveAttribute('aria-expanded','false')
  await expect(open).toBeFocused()
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await capture(page, 'test-results/analysis-mobile.png')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page).toHaveURL(/resultado/)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.goto('/experimentos')
  await expect(page.getByRole('cell',{name:'0,6896',exact:true})).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await capture(page, 'test-results/experiments-320px.png')
})

test('falhas de imagem e envio inválido têm feedback sem interromper a tela', async ({page}) => {
  await page.route('**/api/models/confusion-matrix',route => route.fulfill({status:503,body:'unavailable'}))
  await page.goto('/experimentos')
  await expect(page.getByText(/Não foi possível carregar a matriz/)).toBeVisible()
  await expect(page.getByRole('cell',{name:'0,6896',exact:true})).toBeVisible()
  await page.goto('/demonstracao')
  await page.getByLabel('Enviar currículo',{exact:true}).setInputFiles({name:'arquivo.exe',mimeType:'application/octet-stream',buffer:Buffer.from('example')})
  await expect(page.getByRole('alert').filter({hasText:'Use PDF ou TXT'})).toBeVisible()
})

test('dashboard real, análise simulada, relatório e limpeza', async ({page}) => {
  const crashes:string[] = []
  page.on('pageerror',e => crashes.push(e.message))
  await page.goto('/')
  await expect(page.locator('.stat-value').filter({hasText:'75,05%'})).toBeVisible()
  await expect(page.getByText('Random Forest', {exact:true}).first()).toBeVisible()
  await capture(page, 'test-results/dashboard-desktop.png')
  await page.getByRole('link',{name:'Nova análise',exact:true}).first().click()
  await page.goto('/demonstracao')
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page).toHaveURL(/resultado/)
  await expect(page.getByText('Demonstração simulada.',{exact:true})).toBeVisible()
  await expect(page.getByRole('heading',{name:'Requisitos com evidências'})).toBeVisible()
  await expect(page.getByRole('heading',{name:'Indicador ilustrativo'})).toBeVisible()
  await expect(page.getByText('“Python”',{exact:true})).toBeVisible()
  await capture(page, 'test-results/result-desktop.png')
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button',{name:'Baixar relatório'}).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('talentmatch-relatorio.json')
  const report = JSON.parse(readFileSync(await download.path(),'utf8'))
  expect(report.mode).toBe('demo')
  expect(report.ml.model_name).toBe('RandomForestClassifier')
  expect(report.llm.resumo).toContain('SIMULADA')
  expect(report.privacy.stored_permanently).toBe(false)
  await page.getByRole('button',{name:'Limpar',exact:true}).click()
  await page.goto('/resultado')
  await expect(page.getByRole('heading',{name:'Vamos começar pelo contexto.'})).toBeVisible()
  expect(crashes).toEqual([])
})

test('upload, falha de LLM e comparação sem ranking', async ({page}) => {
  await page.goto('/analise')
  await page.getByLabel('Enviar currículo',{exact:true}).setInputFiles({name:'curriculo.txt',mimeType:'text/plain',buffer:Buffer.from('Nome: Pessoa Exemplo\nPython SQL development projects')})
  await page.getByLabel('Descrição da vaga',{exact:true}).fill('Python SQL AWS')
  await page.getByRole('checkbox').check()
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page.getByText('Análise contextual indisponível.',{exact:true})).toBeVisible()
  await expect(page.getByRole('heading',{name:'Classificação profissional'})).toBeVisible()
  await page.getByRole('link',{name:'Comparar currículos'}).click()
  await page.goto('/demonstracao/comparacao')
  await page.getByLabel('Enviar currículos').setInputFiles(['../docs/exemplos/candidato-a.txt', '../docs/exemplos/candidato-b.txt'])
  await page.getByLabel('Descrição da vaga',{exact:true}).fill(readFileSync('../docs/exemplos/vaga.txt','utf8'))
  await page.getByRole('button',{name:'Comparar evidências'}).click()
  await expect(page.getByRole('region',{name:'Resultados da comparação'})).toBeVisible()
  await expect(page.getByRole('columnheader',{name:/Candidato 1/})).toBeVisible()
  await expect(page.getByRole('columnheader',{name:/Candidato 2/})).toBeVisible()
  await page.locator('.candidate-details summary').first().click()
  await expect(page.getByRole('heading',{name:'Leitura do perfil'})).toBeVisible()
  await expect(page.getByRole('cell',{name:'Não avaliada na simulação',exact:true})).toHaveCount(2)
  const audit = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()
  expect(audit.violations.map(v => ({id:v.id,nodes:v.nodes.map(n=>({html:n.html,summary:n.failureSummary}))}))).toEqual([])
  await capture(page, 'test-results/comparison-desktop.png')
})

test('experimentos, privacidade e responsividade em 390px', async ({page}) => {
  await page.setViewportSize({width:390,height:844})
  await page.goto('/')
  await expect(page.locator('.stat-value').filter({hasText:'75,05%'})).toBeVisible()
  await capture(page, 'test-results/dashboard-mobile.png')
  await page.getByRole('button',{name:'Abrir navegação'}).click()
  await page.getByRole('link',{name:'Experimentos de ML'}).click()
  await expect(page.getByRole('cell',{name:'0,6896'})).toBeVisible()
  await expect(page.getByAltText(/Matriz de confusão original do classificador/)).toBeVisible()
  await capture(page, 'test-results/experiments-mobile.png')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.getByRole('button',{name:'Abrir navegação'}).click()
  await page.getByRole('link',{name:'Ética e transparência',exact:true}).click()
  await expect(page.getByRole('heading',{name:'Minimizar antes de transmitir'})).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.getByRole('button',{name:'Abrir navegação'}).click()
  await page.getByRole('link',{name:'Nova análise',exact:true}).click()
  await page.goto('/demonstracao')
  await page.getByRole('button',{name:'Usar exemplo fictício'}).click()
  await page.getByRole('button',{name:'Analisar currículo',exact:true}).click()
  await expect(page).toHaveURL(/resultado/)
  await capture(page, 'test-results/result-mobile.png')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})
