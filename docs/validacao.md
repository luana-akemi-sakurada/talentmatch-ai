# Validação da evolução

## Cobertura documental de requisitos — estado atual (15/11/2026)

Implementação e critérios em [cobertura-requisitos.md](cobertura-requisitos.md).
Resultados: 254 testes Python, 17 testes Playwright e build aprovados, sem
chamadas externas. Casos sintéticos verificaram 100%, 50%, 0%, deduplicação,
requisitos compostos e abstenção por omissões ou evidências inválidas.
Os registros abaixo preservam o histórico das etapas anteriores.

## Correção pontual da evidência de duração — etapa anterior

**227 testes Python aprovados**, incluindo 29 casos em
`test_duration_evidence.py`; dois casos antigos que exigiam falha contextual por
duração sem suporte foram substituídos por verificações de omissão da duração.
Comando: `PYTHON_DOTENV_DISABLED=1` e `python -m pytest -q` usando o ambiente
virtual do projeto. Permanece apenas o aviso conhecido Starlette/httpx.

O prompt já exigia passagem completa e anos explicitamente declarados. O problema
era o uso da validação genérica de citação como erro fatal para esse campo: um
recorte literal era recusado antes da conferência da duração. Somente
`grounding.py` foi alterado na implementação; prompt, schema, frontend, adaptador
e demais módulos foram preservados.

Para `evidencia_anos_experiencia`, uma citação completa é verificada diretamente;
um recorte deve ocorrer literalmente, com limites de palavra/número, em uma
única passagem completa do currículo minimizado. A passagem recuperada é o texto
original, sem normalizar, reconstruir ou inventar conteúdo. Só se aceita a duração
se essa passagem contém o valor informado em anos de experiência, sem negação,
faixas, limites ou durações conflitantes. Não se somam empregos/datas nem se
convertem meses em anos. Recortes ambíguos não são resolvidos por conveniência.

Sem validação, o par interno validado `(anos_experiencia,
evidencia_anos_experiencia)` é `(null, null)`. O contrato público continua igual:
publica `anos_experiencia=null`; a evidência de duração já era interna e não foi
adicionada à API. Não se modifica o objeto original recebido do provedor. A
justificativa informa ausência de duração verificável, sem repetir o número
rejeitado. Resumo e demais campos continuam compostos de evidências independentes.

Os testes cobrem passagem completa, recorte localizável, ausência/invenção,
contradição, negação, faixas, ambiguidade, palavras/números decimais, pontuação,
LF/CRLF/CR e limites numéricos que impedem confundir `2` com `12` ou recorte de
decimal. Regras de citações de habilidades, requisitos e experiência continuam
rejeitando recortes e invenções como antes.

Integração SDK/API com transporte simulado reutiliza o currículo fictício
`software-short-pt` de `scripts/model_cases.json`: a evidência completa e
`dois anos de experiência` produzem o mesmo resultado. A duração inventada é
omitida, `llm_error=null`, e ML, habilidades, experiência, requisitos, pontos
fortes e lacunas permanecem iguais. Logs contêm somente códigos e ação.

**Conclusão:** ausência de duração verificável permite concluir a análise com
as demais evidências válidas. Afirmações sem suporte em outros campos ainda
podem provocar abstenção; tipos/valores fora do contrato JSON continuam sujeitos
à validação estrutural. Não houve chamadas externas, alteração de modelos ou
credenciais, commit ou push. Frontend/build não foram repetidos nesta etapa,
pois não houve alteração de frontend ou contrato.

## Entrega simplificada do LLM — estado atual

**200 testes Python aprovados e 16 testes de navegador aprovados.** O pytest
mantém somente o aviso conhecido de depreciação Starlette/httpx. Build
TypeScript/Vite concluído. Os testes Python usam exclusivamente mocks locais;
houve um problema de isolamento na execução inicial do navegador, descrito abaixo.

Perguntas foram removidas do prompt, schemas, geração, validação, React,
Streamlit e demo. Os testes exclusivos da função removida foram retirados;
os essenciais foram preservados/adaptados. Os campos antigos de perguntas,
caso retornados por um cliente/provedor legado, são descartados antes do
Pydantic e não afetam uma extração essencial válida. Não há substitutos.

`test_llm_stabilization.py` acrescenta 25 casos com SDK real e transporte HTTP
simulado. Usa os exemplos fictícios A/B e a vaga em `docs/exemplos/`, além do
caso insuficiente já existente. Verifica:

| Cenário | Resultado local observado |
|---|---|
| Currículo A compatível | Perfil Data analyst, evidências Python/SQL/Power BI, AWS sem evidência, nota null |
| Currículo B incompatível | Contexto Java/React/Git preservado; nenhum requisito da vaga demonstrado; sem erro técnico |
| Informações insuficientes | Abstenção explícita, sem habilidades/perfil inventados ou nota |
| Falha externa | Códigos distintos para autenticação, permissão, modelo, limites/quota, timeout, conexão, serviço e recusa; ML preservado |
| JSON inválido/estrutura/truncamento | `invalid_llm_response` com diagnóstico específico; ML preservado |
| Evidência inventada ou requisito sem suporte | `unsupported_evidence`, sem publicação contextual |

O request do SDK foi inspecionado em memória: `json_schema`, `strict=true`,
todos os campos obrigatórios e objetos fechados, sem perguntas, nota null,
`reasoning_effort=low` e `max_completion_tokens=3500`. Os limites Pydantic
continuam sendo verificados localmente. Não há repetição automática de chamada,
fallback silencioso para simulação ou exposição de mensagem bruta do provedor.

Playwright completo, inicialmente: **16 passed (31.5s), exit code 0**, com servidores
locais gerenciados separadamente. Entretanto, a atribuição de variáveis vazias
no PowerShell podia removê-las e permitir leitura do `.env`: houve duas tentativas
terminadas em `llm_connection_error`, sem resposta da Groq. Faturamento não foi
consultado; não se conclui ausência de cobrança pela ausência de resposta.

O ambiente foi corrigido com `PYTHON_DOTENV_DISABLED=1`, ausência de chave/modelo
e URL LLM apontando exclusivamente para loopback. O gerenciador automático do
Playwright recebeu a mesma proteção. A suíte foi repetida; o primeiro teste agora
exige `llm_not_configured`. A repetição isolada terminou com **16 passed (28.0s),
exit code 0**. As tentativas anteriores não validam a integração real.
Os testes cobrem fluxo principal,
ausência de perguntas, perfil versus categoria ML, evidências/sem pontuação,
upload/falhas, comparação, relatório, acessibilidade e responsividade. O teste
Streamlit também confirmou análise sem perguntas e tratamento da nota ausente.

As métricas e os três artefatos originais não foram modificados. README,
OpenAPI, documentação de API, roteiro e slides refletem o escopo simplificado.
As seções seguintes são registros históricos de etapas anteriores, inclusive
da função de perguntas que já não existe.

**Próximo passo:** reiniciar o backend e executar um teste manual autorizado
com a Groq. A compatibilidade foi conferida na documentação oficial e nos
requests simulados; não se afirma sucesso de uma nova chamada real. Guia,
fontes, códigos de erro e limitações em [estabilizacao-llm.md](estabilizacao-llm.md).
Nenhuma credencial foi alterada, não se autorizou chamada paga e não houve
retreinamento, commit ou push. O incidente de conexão acima permanece registrado.

## Perguntas de entrevista — validação individual e resultado parcial

**199 testes Python aprovados, dois testes de navegador relevantes aprovados
e build TypeScript/Vite concluído.** Permanece apenas o aviso conhecido de
depreciação Starlette/httpx no pytest. Os testes não fizeram inferência externa.

O teste real relatado exibiu `question_invalid` nos índices 3, 4 e 5 e
`interview_not_validated`. Esses logs antigos não identificavam qual condição
falhou. A investigação confirmou que qualquer falha individual eliminava a
lista inteira, e que quantidade/diversidade também bloqueavam perguntas válidas.
Não se atribuiu uma causa textual específica aos itens da Groq sem sua resposta.

Agora cada pergunta passa pelas mesmas verificações de referência, foco,
formulação, pressuposições, pontuação, duplicação e repetição de abertura.
Os rejeitados são descartados; somente aprovados entram nas contagens de
deduplicação/abertura. O log informa o índice original e os códigos em `reasons`,
sem conteúdo textual. O prompt explicita essas regras e admite menos perguntas
quando faltar suporte. Não há preenchimento por templates.

Resultado `parcial`: há perguntas válidas, mas houve descarte, menos de cinco
perguntas ou menos de quatro categorias. Resultado `validada`: metas atingidas e
nenhum descarte. Sem perguntas aprovadas, mantém-se `indisponivel`. Tipos, campos
obrigatórios e máximo de oito itens do contrato JSON continuam sendo exigidos;
a mudança não flexibiliza erros estruturais de resposta.

Os nove novos casos em `test_partial_interview.py` cobrem a mistura de três
válidas/três inválidas, um a quatro itens aprovados, duplicação normalizada,
item inválido que não bloqueia posterior válido, ausência de aprovadas e
integração SDK/API. Comparam o resultado ML e os requisitos antes/depois e
verificam a ausência de texto sensível nos logs. Testes anteriores de rejeição
integral foram ajustados para verificar preservação apenas dos itens aprovados.

Playwright executou as variantes completa e parcial do cenário de perfil e
perguntas, incluindo a indicação visual de três perguntas, invariância da
apresentação de cobertura, reflow e axe. Foram usados servidores locais de teste
com credenciais vazias e `E2E_EXTERNAL_SERVERS=true` (procedimento abaixo),
com término limpo: **2 passed, exit code 0**. A suíte completa de navegador não
foi repetida nesta mudança pontual.

Frontend alterado somente no tipo do status e no aviso da seção de entrevista.
Classificador, artefatos, credenciais e cobertura de requisitos preservados.
Não houve chamada paga, commit ou push. A qualidade semântica e os motivos
exatos dos itens do teste real ainda precisam de uma nova execução autorizada,
agora com diagnósticos específicos. Regras em [refinamentos-finais.md](refinamentos-finais.md).

## Refinamentos finais de análise e experiência — execução mais recente

**190 testes Python aprovados, 16 testes de navegador aprovados e build
TypeScript/Vite concluído.** O pytest mantém apenas o aviso conhecido de
depreciação Starlette/httpx. Os três hashes SHA-256 dos artefatos originais foram
novamente conferidos e permanecem iguais. Nenhuma inferência externa foi feita.

Os 21 novos testes Python em `test_contextual_refinements.py` verificam perfil
citável, rejeição de designações/experiências inventadas, 5–8 perguntas, diversidade,
duplicação, referências/foco, formulação hipotética, abstenção do bloco inválido,
compatibilidade de respostas antigas e independência da categoria ML. Incluem
SDK real com transporte HTTP simulado e endpoints reais via TestClient.

Os 14 testes de navegador anteriores foram preservados/adaptados para acesso
offline explícito. Dois novos cenários verificam o fluxo principal sem seletor,
exemplo que não ativa demo, falha sem fallback, perfil separado da categoria ML,
seis perguntas referenciadas e cobertura indeterminada sem percentual. Incluem
checagens axe e reflow em 390 px para o novo resultado. As demais checagens de
acessibilidade, upload, relatórios, comparação, privacidade e 320 px passaram.

### Encerramento dos servidores de teste no Windows

O comando inicial apresentou `ok` nos 16 casos, mas travou ao encerrar os
servidores. A suíte foi repetida com os mesmos servidores locais de teste
(portas 8011/5179, credenciais LLM explicitamente vazias) e a opção
`E2E_EXTERNAL_SERVERS=true`, que desativa o gerenciamento de servidores pelo
Playwright. Essa repetição terminou com **16 passed (28.2s), exit code 0**.
O processo inicial e seus servidores foram encerrados separadamente.

Para reproduzir essa alternativa, inicie manualmente os dois serviços nas
portas acima com `PYTHON_DOTENV_DISABLED=1`, sem chave/modelo LLM, URL LLM
`http://127.0.0.1:9/v1` e proxy Vite apontando para 8011,
depois execute no diretório frontend:

```powershell
$env:E2E_EXTERNAL_SERVERS = 'true'
npm run test:e2e
Remove-Item Env:E2E_EXTERNAL_SERVERS
```

Essa opção é exclusiva para servidores locais controlados de teste: não deve
apontar para instância configurada com credenciais reais. Sem a variável, o
gerenciamento automático anterior permanece como padrão.

O índice numérico não foi implementado: faltam obrigatoriedade/desejabilidade e
completude verificável no contrato. A limitação aparece na interface e em
[refinamentos-finais.md](refinamentos-finais.md). Perfil e perguntas do teste
são fixtures fictícias; sua qualidade no provedor real ainda requer revisão
humana e chamada autorizada. README, contrato OpenAPI, slides e roteiro atualizados.

## Teste B — currículo incompatível

**Origem do registro manual:** resultado informado pela pessoa responsável pelo
teste real com a Groq. Não foi repetida chamada externa nem armazenada resposta
bruta ou passagem do currículo nesta etapa.

| Dimensão | Classificação | Evidência relatada |
|---|---|---|
| Execução ML | Executada normalmente | Random Forest produziu resultado e a aplicação o preservou |
| Controle de segurança | **Aprovado para o controle exercitado** | Uma passagem listada como experiência foi bloqueada por `nonpositive_evidence` |
| Análise contextual | **Não concluída — abstenção** | O resultado contextual não foi publicado após a rejeição; isso não equivale à aprovação funcional da análise |

Diagnóstico informado: `rule=nonpositive_evidence`,
`field=experiencia_profissional`, `source=curriculo`, `category=support`,
`index=1`. O índice é base zero: **segundo item** de experiência retornado.
O fluxo esperado mantém `llm_error=unsupported_evidence`, `llm=null` e o
resultado ML. Não se publica nota nem conclusão contextual parcial dessa falha.

### Verificação local e interpretação

Foram adicionados quatro testes em `backend/tests/test_incompatible_resume.py`,
com currículo fictício de finanças/Excel e vaga Java/Spring Boot. O SDK real usa
somente `httpx.MockTransport`, sem requisições ao provedor:

1. Três variantes incluem uma primeira experiência positiva literal e um segundo
   item literal de negação, ausência ou desejo de aprender Java. Todas reproduzem
   o diagnóstico `nonpositive_evidence` em `experiencia_profissional`, índice 1;
   a API retorna a abstenção contextual e o mesmo resultado ML da execução direta.
2. No controle com o mesmo currículo incompatível, o provedor simulado lista
   somente a experiência positiva e os requisitos sem evidência. A análise
   contextual é aceita, sem requisitos atendidos e com nota null.

Execução: `.\.venv\Scripts\python.exe -m pytest -q` — **169 testes aprovados**,
incluindo os quatro novos casos. Permanece apenas o aviso conhecido de
depreciação Starlette/httpx. Frontend/build não foram repetidos: nenhuma regra,
contrato ou implementação foi alterada; somente testes e este relatório.

Portanto, a abstenção relatada é esperada **pela passagem não positiva incluída
como experiência**, não por uma regra que rejeite todo currículo incompatível.
Um currículo incompatível pode receber uma análise fundamentada que explicite
os requisitos não demonstrados. O teste B comprova o bloqueio exercitado e a
preservação do ML; não comprova conclusão da análise, acurácia do classificador
ou qualidade geral do LLM.

### Limitação registrada

A experiência é validada de forma conservadora e integral: um único item não
positivo impede publicar toda a análise contextual, mesmo que existam outras
passagens válidas. A omissão recuperável de nomes de habilidades não se aplica
a `experiencia_profissional`. O verificador usa padrões lexicais de negação,
ausência e desejo, sem interpretação semântica completa; pode recusar uma frase
válida quando a negação se refere a outro aspecto. Sem a passagem original, o
registro manual não permite distinguir esse falso positivo de uma exclusão
correta de experiência não demonstrada. Não se deduz que a citação era inventada:
uma passagem literal também pode ser inadequada como evidência positiva.

As regras de implementação foram preservadas. Nenhuma chamada paga, alteração
de credenciais ou modelos, commit ou push foi realizada. Os exemplos sintéticos
não constituem avaliação estatística representativa do desempenho.

## Omissão de habilidade sem correspondência — etapa anterior

**165 testes Python aprovados**, incluindo 15 novos testes em
`backend/tests/test_skill_omission.py`. Um caso contém sete habilidades e apenas
o índice 6 sem correspondência: os seis itens válidos são preservados, o nome
inválido não aparece nos campos derivados e a justificativa registra a omissão.
O log informa código, índice e ação, sem valores de entrada.

As regressões verificam dependências em requisitos, experiência e duração;
requisito inventado; citação inventada, recortada ou negativa; apoio independente
em outra passagem; todas as habilidades omitidas; duplicatas e tentativa de
reintroduzir a afirmação por resumo livre. A abstenção de nota é preservada.
SDK real com transporte local simulado e `/api/analyze` verificaram tanto a
resposta parcial segura quanto a falha fatal por dependência sem suporte,
mantendo o ML. Dois testes antigos foram ajustados à política recuperável; a
rejeição de Java como habilidade extraída de JavaScript continua verificada.

Nenhuma chamada externa de inferência, alteração de frontend, credenciais ou
artefatos ML. Permanece apenas o aviso conhecido de depreciação Starlette/httpx.
Os testes de navegador não foram repetidos nesta etapa, que não altera o contrato
público nem o frontend. Regras e limites em
[diagnostico-evidencias.md](diagnostico-evidencias.md).

## Diagnósticos de fundamentação — etapa anterior

**151 testes Python aprovados**, incluindo 24 novos casos em
`backend/tests/test_requirement_diagnostics.py`. Cobrem a divergência de redação
vaga/currículo com competência literal comum, qualificadores não comprovados,
requisito inventado ou ausente, sinônimos sem prova, pontuação, caixa/acentos,
quebras de linha, múltiplas evidências, limite do contrato e logs sem conteúdo
sensível. As integrações SDK/API usam exclusivamente transporte HTTP simulado
local e verificam também `llm_diagnostic`, ML preservado e nota null.

Os 14 cenários Playwright exibiram `ok`, sem falhas de asserção. Porém, o comando
ficou aguardando o encerramento dos servidores após os testes, sem emitir o
resumo final/exit code. O backend de teste foi encerrado e a execução interrompida;
isso é uma limitação desta execução, não uma conclusão de término limpo da suíte.

O pytest mantém somente o aviso conhecido de depreciação Starlette/httpx.
Os três hashes SHA-256 originais foram novamente conferidos e permanecem iguais.
Não houve alteração de credenciais nem requisição externa de inferência.
Veja [diagnostico-evidencias.md](diagnostico-evidencias.md) para a reprodução
fictícia e a distinção entre causa confirmada no código e execução real pendente.

## Regressão de pontuação nas evidências — etapa anterior

**127 testes Python aprovados**, incluindo 33 novos casos em
`backend/tests/test_evidence_passages.py`. O ponto e vírgula permanece no item
anterior; frases preservam `.`, `!` e `?`, vírgulas não segmentam passagens e
quebras LF/CRLF/CR são reconhecidas. O prompt descreve as mesmas regras.

Os casos incluem citações inventadas, recortadas, com pontuação alterada, unidades
juntadas, negação e remoção de dados pessoais. Integrações com o SDK real sobre
`httpx.MockTransport` e com `/api/analyze` verificam aceitação, falha contextual
com ML preservado e abstenção de nota, inclusive quando o provedor simulado
retorna 100. Nenhuma requisição saiu para um provedor externo. Permanece um aviso
de depreciação Starlette/httpx, sem falhas.

Esta alteração não modifica frontend nem contrato público; os resultados de
navegador/build abaixo pertencem à etapa anterior. Credenciais e artefatos
originais foram preservados.

## Correções de confiabilidade — execução mais recente

Resultado final: **94 testes Python e 14 testes de navegador aprovados**, build
TypeScript/Vite concluído e **três cenários HTTP locais aprovados** com o SDK real
(sucesso, JSON inválido e HTTP 503). O pytest emitiu um aviso de depreciação
da integração Starlette/httpx, sem falhas. Os testes não chamaram um LLM externo.

Consulte [confiabilidade.md](confiabilidade.md) para a política de evidências,
abstenção e cobertura. Esta etapa adiciona testes de vetor vazio, cobertura parcial
e extremamente esparsa, citações inventadas/recortadas, habilidades sem suporte,
negação/desejo, requisitos contraditórios, duração explícita, pontuação sem evidência
e notas altas em respostas parciais. O contexto ML mantém o padrão anterior e tem
modo independente com payload invariável testado.

Os testes de navegador também verificam abstenção de classificação e nota null,
preservando relatório/comparação; o Streamlit foi testado com essas duas abstenções.
O mock HTTP local foi repetido com o SDK real: sucesso, JSON inválido e HTTP 503
produziram os estados esperados. Nenhuma chamada ao provedor externo foi feita.

Os resultados da revisão visual abaixo são históricos. O relatório original de
qualidade em `avaliacao-modelo.md` também foi preservado com uma nota de atualização.

## Executado localmente

Resultado da revisão visual anterior: **43 testes Python e 12 testes E2E aprovados**; build de produção
concluído. Os três hashes SHA-256 originais foram conferidos e permanecem iguais.

- Python 3.14.5, scikit-learn 1.9.1 (mesma versão registrada no pickle).
- Carregamento real do pipeline: RandomForestClassifier; 24 classes.
- Testes pytest: limpeza, minimização, formatos/limites, PDF vazio, predição real,
  JSON inválido, timeout, evidência inexistente, payload de currículo/vaga e SDK
  com transporte HTTP simulado, endpoints, comparação e falhas parciais.
- Doze testes Playwright no Microsoft Edge headless contra API local real e
  classificador original: tabela conferida contra o CSV, análise demo, conteúdo
  do relatório JSON, limpeza, upload, LLM indisponível, comparação preenchida,
  falha da imagem da matriz, upload inválido e reflow em 320/390 px.
- Axe: nenhuma violação detectada nas regras WCAG 2 A/AA e 2.1 AA examinadas nas
  cinco páginas, no resultado demonstrativo e na comparação preenchida. Menu
  móvel: foco contido, Tab/Shift+Tab, Escape e retorno ao botão de abertura.
  Isso não constitui certificação nem substitui conferência com leitor de tela.
- O fluxo de comparação foi repetido usando exatamente os três arquivos de
  `docs/exemplos/` citados no roteiro de apresentação.
- Build TypeScript/Vite. Componentes shadcn oficiais, adaptados aos imports locais.
- Na evolução anterior, simulação Postman CLI 1.85.0: três requisições reais do SDK ao mock HTTP local:
  sucesso 200, conteúdo inválido 200 e indisponibilidade 503. Os códigos esperados
  foram observados. O handler confere remoção do nome fictício no payload recebido.
  Essa simulação HTTP não foi repetida nesta revisão visual; os testes Python
  do adaptador com mocks foram executados novamente.

## Evidência da revisão visual

Diagnóstico e arquivos modificados em [revisao-final.md](revisao-final.md).
As capturas atualizadas ficam em `frontend/test-results/`: dashboard, análise,
resultado, comparação e experimentos em desktop; análise/experimentos em 320 px;
dashboard, experimentos e resultado em 390 px. As imagens são capturas de testes,
nunca demonstrações de LLM ao vivo.

Roteiro cronometrado: [4min30s](demonstracao.md). Material de dez slides:
[apresentacao.md](apresentacao.md), com texto, visual sugerido e tela correspondente.
Conferir antes de apresentar: projetor, zoom, leitor de tela, outro navegador e
tempo de fala. Se for mostrar LLM real, validar o provedor separadamente com dados
fictícios autorizados. Nenhuma chamada paga foi feita nesta revisão.

## Repetir

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
npm run test:e2e
```

O teste E2E usa portas 8011 e 5179, inicia e encerra seus servidores e força chave
e modelo vazios. O Edge precisa estar instalado; em outro ambiente altere `channel`
em `playwright.config.ts` ou instale o navegador Playwright apropriado.
As capturas ficam em `frontend/test-results/`, ignoradas pelo Git.

Simulação HTTP (dois terminais, raiz):

```powershell
postman simulation run postman/simulations/llm/llm.sim.yaml --port 4010 --no-history --output ndjson
```

```powershell
.\.venv\Scripts\python.exe backend/tests/check_http_simulation.py
```

Não use `--verbose` com documentos reais. O mock contém apenas fixtures sintéticas.
Encerre o servidor simulado com Ctrl+C. Não exige login ou publicação.

## Limites da evidência

Sem chamada ao provedor externo real, sem custo de LLM. Mocks validam serialização,
contratos e falhas locais; não demonstram qualidade da análise generativa, resistência
universal a prompt injection, justiça do modelo ou políticas de retenção do provedor.
Nenhum retreinamento foi feito: o dataset original não está disponível nesta cópia.
Não há medição de desempenho em português, testes de carga, avaliação de vieses ou
certificação de acessibilidade. Revisão visual e navegação responsiva não substituem
uma auditoria completa de acessibilidade.

O uso do TestClient instalado gera um aviso de depreciação da integração httpx
do Starlette; os testes passam. O lock captura o ambiente efetivamente utilizado.

## Organização das mudanças

- Raiz: `README.md`, `llm.py`, `app.py`, `train.py`, `requirements.txt`, `.env.example`, `ETICA.md`,
  `.gitignore` e `pytest.ini`; limpeza original em `preprocess.py` preservada.
- `backend/app/`: configuração/erros, schemas, serviços e FastAPI.
- `backend/tests/`: testes e verificador HTTP opt-in.
- `backend/requirements*.txt`: dependências e lock do ambiente validado.
- `frontend/`: projeto Vite, componentes, páginas, cliente API e testes E2E.
- `docs/`: auditoria, arquitetura, API/OpenAPI, experimentos, ética, validação,
  demonstração cronometrada, roteiro de apresentação, revisão final e exemplos fictícios.
- `postman/`: contrato mínimo simulado e contexto dos cenários HTTP.
- `models/`: nenhum arquivo alterado; hashes registrados em experimentos.md.
- `.env`: não exibido nem modificado. Sem commits ou push.

