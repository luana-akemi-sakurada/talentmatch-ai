# TalentMatch AI 2.0

Plataforma local de apoio à análise de currículos e compatibilidade com vagas.
Evolução incremental do TDE2 de Sistemas de Informação Inteligentes / PUCPR.
Combina o classificador scikit-learn original com análise contextual por LLM.
**A decisão é sempre humana; não há ranking definitivo ou rejeição automática.**

## Implementado

- React + TypeScript + Vite, Tailwind, shadcn/ui e Recharts.
- FastAPI com validação Pydantic e documentação OpenAPI.
- Upload PDF/TXT ou texto; classificação local e análise contextual separadas.
- Perfil, competências, experiência explícita, requisitos/evidências, lacunas e relatório JSON.
- Perfil profissional contextual citável, separado das 24 categorias do ML.
- Cobertura documental calculada no backend, com contagens, fórmula e abstenção
  quando a lista ou as avaliações forem incompletas ([critérios](docs/cobertura-requisitos.md)).
- Integração Groq GPT-OSS com saída JSON estruturada e validação local de evidências.
- Comparação de 2–5 currículos, na ordem de envio, com falhas individuais visíveis.
- Dashboard com métricas reais e matriz de confusão original.
- Demonstração offline em rotas próprias, fora da navegação principal: ML real e
  contexto simulado, sem API externa.
- Minimização antes do LLM, conferência de citações e mensagens de erro seguras.
- Sem banco, login ou armazenamento permanente de currículos.

As [proteções de confiabilidade](docs/confiabilidade.md) acrescentam cobertura
TF-IDF e abstenção para vetor vazio. No modo ao vivo, evidências textuais verificadas
continuam disponíveis, mas a nota fica **indisponível (null)** até validar um método
de pontuação. Isso não significa aderência zero. A nota ilustrativa da demo permanece.

As perguntas de entrevista foram removidas para simplificar e estabilizar a entrega.
Consulte [estabilizacao-llm.md](docs/estabilizacao-llm.md) para o contrato essencial,
erros diferenciados e o teste manual final com dados fictícios.

## Executar no Windows

Requer Python 3.11+ compatível com scikit-learn 1.9.1 e Node 22.12+.
Ambiente validado: Python 3.14.5 e Node 24.13.0. Não é necessário baixar dataset
ou retreinar para executar: `models/` já contém o pipeline original.

Na raiz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Em outro terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abra **http://127.0.0.1:5173**. API: **http://127.0.0.1:8000/docs**.
No Linux/macOS use `.venv/bin/python` no lugar de `.venv\Scripts\python.exe`.
O backend deve ser iniciado a partir da raiz. O frontend usa proxy `/api` para
porta 8000, inclusive em `npm run preview`. O build estático sozinho não executa
Python: é necessário manter a API disponível e configurar proxy/origem ao hospedar.

## Configurar LLM (opcional para demonstração)

Use `.env.example` como referência e crie ou edite seu `.env` local. Nunca copie
esse arquivo para o frontend ou publique suas chaves.

```env
LLM_API_KEY=sua_chave
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_INCLUDE_ML_CONTEXT=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

O exemplo utiliza um endpoint compatível com Chat Completions. O modelo precisa
estar disponível no seu provedor. Reinicie o backend após alterar configuração.
**Nova análise** e **Comparar currículos** usam LLM diretamente. Confirme a
autorização de processamento na interface; não há seletor entre modos.
Chamadas ao vivo podem ter custo. Execute os testes com o isolamento descrito
em [validacao.md](docs/validacao.md), sem credenciais e com dotenv desativado
nos servidores de teste. No PowerShell, variáveis vazias podem ser removidas.

`LLM_INCLUDE_ML_CONTEXT=false` permite testar a extração sem enviar categoria e
probabilidade ML ao provedor. O padrão true foi preservado; a influência real desse
contexto ainda precisa de avaliação experimental. O contrato exige citações completas,
com verificações literais conservadoras; não é uma comprovação de competência.

Sem chave, abra explicitamente `/demonstracao` ou `/demonstracao/comparacao`
para apresentação offline. Essas rotas não aparecem no menu principal. O botão
**Usar exemplo fictício** apenas preenche os textos e nunca ativa simulação.
Falhas do LLM preservam ML e informam indisponibilidade, sem fallback para demo.
Simulação não comprova a integração real com LLM exigida na apresentação acadêmica.

Não foi implementado índice numérico de cobertura: o contrato não diferencia
requisitos obrigatórios/desejáveis nem garante inventário completo. A interface
mostra evidências, requisitos sem evidência e cobertura total indeterminada;
não transforma contagens parciais em percentual. Critérios e limites em
[refinamentos-finais.md](docs/refinamentos-finais.md).

## Artefatos e resultados preservados

| Algoritmo | Acurácia | F1 macro |
|---|---:|---:|
| Logistic Regression | 68,61% | 0,6393 |
| **Random Forest** | **75,05%** | **0,6896** |
| MLP | 61,57% | 0,5610 |

Fonte: `models/comparacao_modelos.csv`. Pipeline carregado: RandomForestClassifier,
24 categorias, scikit-learn 1.9.1. Os modelos não foram retreinados nesta evolução.
Precision, recall e distribuição do dataset original não estão disponíveis.
Seleção e avaliação usam o mesmo teste original, limitando sua independência.
Essas métricas não validam o indicador contextual de aderência.

## Estrutura

```text
backend/app/       FastAPI, configuração, schemas e serviços
backend/tests/     Testes Python e verificação HTTP simulada
frontend/src/      Componentes, páginas, hooks, tipos e cliente REST
frontend/tests/    Playwright com API e modelo reais, sem chamadas pagas
models/            Pipeline, CSV e PNG originais, preservados
docs/              Auditoria, arquitetura, contratos e apresentação
postman/           Mock HTTP local do provedor e cenários de verificação
app.py             Interface Streamlit original, com correções de segurança
llm.py             Adaptador LLM compartilhado
preprocess.py      Limpeza original reutilizada
train.py           Reprodução opcional dos experimentos, com exportação ampliada
```

## Testes e build

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm run build
npm run test:e2e
```

E2E usa Microsoft Edge headless, portas 8011/5179 e chave LLM vazia. O navegador
precisa estar instalado. Veja [validação](docs/validacao.md) para simulação HTTP,
capturas de tela e limites do que foi verificado. Testes Streamlit são opcionais
e executados quando as dependências da raiz estão instaladas.

## Streamlit e treinamento

Para a interface original e dependências de treinamento:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

O Streamlit usa o mesmo adaptador corrigido e exige autorização para envio ao LLM.
Para treinamento opcional, baixe `Resume.csv` do Kaggle para `data/` e execute:

```powershell
.\.venv\Scripts\python.exe train.py --output-dir artifacts/novo-experimento
```

O diretório deve ser novo; `models/` é protegido contra sobrescrita pelo script.
Veja [experimentos e reprodução](docs/experimentos.md). Novos resultados não
substituem automaticamente o dashboard original.

## Limites de uso

PDF/TXT até 5 MB; PDF textual sem senha, até 30 páginas. Não há OCR. Até 40.000
caracteres no currículo e 16.000 na vaga; o LLM recebe até 20.000 caracteres
minimizados do currículo, com aviso de truncamento. Até cinco arquivos por comparação.

Minimização por regex não garante anonimização; revise nomes e dados sensíveis.
O LLM pode errar e o dataset é em inglês. Citações literais não comprovam veracidade
ou interpretação correta. O indicador é heurístico, não probabilidade de contratação.
Sem autenticação, esta versão se destina a execução local e demonstração acadêmica.
Políticas de retenção do provedor externo devem ser verificadas antes do uso real.

## Documentação

- [Auditoria técnica](docs/auditoria.md) e [arquitetura](docs/arquitetura.md).
- [Contrato REST e erros](docs/api.md), [OpenAPI](docs/openapi.json).
- [Dataset, métricas e reprodução](docs/experimentos.md).
- [Ética e controles efetivos](docs/etica.md).
- [Validação e arquivos alterados](docs/validacao.md).
- [Revisão final de experiência visual](docs/revisao-final.md).
- [Roteiro de demonstração](docs/demonstracao.md).
- [Textos fictícios para demonstração](docs/exemplos/).
- [Apresentação de 10 slides](docs/apresentacao.md).
- [README original preservado](docs/readme-streamlit-original.md).
