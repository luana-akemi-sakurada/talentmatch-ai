import { Notice, PageHeading } from '@/components/common'
import '../results.css'
import '../ethics.css'

interface Principle { title: string; takeaway: string; points: string[] }
const pledges = [
  ['Decisão final humana', 'O sistema não contrata, rejeita nem ordena pessoas.'],
  ['Evidência não é prova', 'Trechos citados mostram o que está escrito, não o que a pessoa sabe fazer.'],
  ['Sem armazenamento permanente', 'Textos são processados em memória para cada solicitação.'],
]
const sections: {title: string; intro: string; items: Principle[]}[] = [
  {title: 'O que o sistema faz e não faz', intro: 'Papel das previsões dentro do processo.', items: [
    {title: 'Pessoas conduzem a decisão', takeaway: 'O sistema organiza evidências; quem decide é a equipe de recrutamento.', points: [
      'Não contrata, rejeita nem ordena pessoas automaticamente.',
      'Ausência de evidência no currículo não significa ausência de habilidade.',
      'Confirme as informações com a pessoa candidata.']},
    {title: 'O que os modelos estimam', takeaway: 'Reproduzem padrões de um dataset, não o valor de uma pessoa.', points: [
      'A compatibilidade estima o score e as faixas fraca, média e forte do dataset Shresth786/job-resume-matching. Não foi verificado se recrutadores validaram esses rótulos.',
      'A previsão não mede chance de contratação, desempenho no trabalho ou valor profissional.',
      'A área é derivada das vagas associadas no dataset; não foi anotada diretamente no currículo.']},
  ]},
  {title: 'Quanto confiar nos números', intro: 'Limites das métricas, das evidências e da tecnologia.', items: [
    {title: 'Avaliação e probabilidades', takeaway: 'Os números valem para dados parecidos com os do teste.', points: [
      'No matching, currículos e vagas de teste são inéditos. Ainda assim o ganho sobre chutar a faixa mais comum é modesto (veja “Modelos e validação”).',
      'Intervalos de confiança (bootstrap) dependem do modelo treinado e não incluem a variação de um novo treino.',
      'As probabilidades de faixa vêm da distribuição dos erros em dados inéditos. Não há faixas de confiança alta, média ou baixa validadas.',
      'Calibração não garante confiabilidade em outras populações ou idiomas.']},
    {title: 'Incerteza e evidências', takeaway: 'Similaridade e citação literal não comprovam competência.', points: [
      'O alerta de vocabulário atípico compara a distância lexical com um percentil da validação, sem comprovação em corpus externo.',
      'Similaridade TF-IDF não prova atendimento a requisitos.',
      'A citação literal demonstra presença textual, não veracidade, competência ou interpretação correta.',
      'A cobertura documental não é nota de aderência.']},
    {title: 'Limites técnicos', takeaway: 'O LLM pode errar; por isso cada citação é verificada no texto.', points: [
      'O LLM pode alucinar. Estrutura e citações são verificadas, mas isso não garante imunidade a prompt injection.',
      'Vetores TF-IDF vazios causam abstenção; poucos termos reconhecidos não comprovam confiabilidade.',
      'PDFs digitalizados não têm OCR. Textos longos podem ser truncados na análise contextual, com aviso.',
      'Logs da infraestrutura e políticas do provedor devem ser avaliados separadamente.']},
  ]},
  {title: 'Pessoas e dados', intro: 'Vieses, representatividade e privacidade.', items: [
    {title: 'Vieses e representatividade', takeaway: 'Equidade entre grupos e desempenho em português não foram validados.', points: [
      'O dataset está em inglês e a distribuição entre áreas é desigual (a maioria dos currículos é de TI).',
      'Textos em português são traduzidos automaticamente antes do ML.',
      'Instruir o LLM a ignorar atributos pessoais não elimina vieses nem indicadores indiretos.']},
    {title: 'Privacidade e transmissão', takeaway: 'Revise o texto antes de enviar: a remoção de dados pessoais é limitada.', points: [
      'O aplicativo não foi projetado para reter currículos e resultados. Há processamento em memória e pode haver arquivo temporário durante a leitura.',
      'A minimização por regras não garante anonimização.',
      'No modo ao vivo, o provedor do LLM recebe textos minimizados e aplica as próprias políticas. No modo demonstração não há chamada ao LLM.']},
  ]},
]

export default function Ethics() {
  return <><PageHeading eyebrow="ÉTICA E TRANSPARÊNCIA" title="Limites explícitos, revisão humana.">Interprete previsões como apoio à organização de evidências, não como decisão de recrutamento.</PageHeading>
    <div className="rs et">
      <ul className="et-pledges">{pledges.map(([title, text]) => <li key={title}><strong>{title}</strong><span>{text}</span></li>)}</ul>
      {sections.map(section => <section key={section.title} className="et-section">
        <header><h2>{section.title}</h2><p>{section.intro}</p></header>
        <div className="et-grid">{section.items.map(item => <article key={item.title} className="rs-card et-card">
          <h3>{item.title}</h3>
          <p className="et-takeaway">{item.takeaway}</p>
          <ul>{item.points.map(point => <li key={point}>{point}</li>)}</ul>
        </article>)}</div>
      </section>)}
      <Notice warning>Uso local e acadêmico, sem autenticação nesta versão. Não exponha a API com dados reais. Antes de uso organizacional, avalie acesso, retenção, base legal, licença e procedência dos dados, segurança, políticas do provedor e vieses.</Notice>
    </div></>
}
