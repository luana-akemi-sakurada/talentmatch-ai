# Auditoria técnica — TalentMatch AI 2.0

## Estado inicial

Protótipo Python/Streamlit: `app.py` extrai PDF/TXT, reutiliza a limpeza de
`preprocess.py`, executa um pipeline scikit-learn e chama `llm.py`. Sem banco,
autenticação, API, frontend separado ou testes. Dataset ausente nesta cópia.

## Prioridades

| Prioridade | Constatação inicial | Ação |
|---|---|---|
| Crítica | `txt` indefinido após resposta do LLM | Ler message.content e validar o contrato |
| Alta | Dados pessoais enviados sem remoção | Minimizar currículo e vaga antes da chamada; testar payload |
| Alta | JSON sem validação de campos/tipos | Pydantic, limites e mensagens de erro seguras |
| Alta | Arquivo sem limite e PDF sem tratamento de falhas | Validar extensão, MIME, assinatura, tamanho e conteúdo |
| Alta | Modelo joblib sem versão de ambiente documentada | Inspecionar e testar o artefato confiável local |
| Média | Sem timeout explícito/testes | Timeout, sem repetição automática paga e testes sem API real |
| Média | Métricas incompletas | Expor somente o disponível; exportação opcional futura |
| Média | Relatório mínimo e UI única | API e frontend incrementais; manter Streamlit |

## Artefatos preservados

`models/classificador.joblib` (86.100.821 bytes),
`models/comparacao_modelos.csv`, `models/matriz_confusao.png`.
O pickle registra scikit-learn 1.9.1. Joblib/pickle só deve carregar artefatos
confiáveis: não oferecer upload de modelos.

| Algoritmo | Acurácia | F1 macro |
|---|---:|---:|
| LogisticRegression | 0,6861 | 0,6393 |
| RandomForest | 0,7505 | 0,6896 |
| MLP | 0,6157 | 0,5610 |

A imagem original da matriz pode ser exibida diretamente. Não há precision,
recall, matriz numérica, suporte por classe ou contagens do dataset salvos.
As classes podem ser recuperadas do classificador, mas não sua distribuição.
O script registra split estratificado 80/20, random_state=42, TF-IDF de até
8.000 atributos e unigramas/bigramas. Quantidades efetivas não são conhecidas.
A seleção usa F1 no mesmo teste usado para relatar desempenho: isso limita a
independência da avaliação, e deve ser explicitado.

## Arquitetura e sequência

1. Corrigir LLM compartilhado, criar validação/minimização e testes; carregar
   o modelo sem retreinar ou sobrescrever os artefatos.
2. FastAPI com serviços de ML, arquivos e experimentos; contratos separados de
   ML e LLM; análise multipart e comparação sem ordenação de candidatos.
3. React/TypeScript/Vite, Tailwind, shadcn/ui e Recharts; navegação responsiva,
   formulários e relatório na memória da sessão.
4. Métricas reais e imagem original; indicar dados ausentes e oferecer processo
   de treinamento reproduzível com exportação para outro diretório.
5. Testar falhas e privacidade, build, documentar execução e roteiro de 10 slides.

## Riscos e dependências

Python compatível com scikit-learn 1.9.1, dependências instaláveis, Node e provedor
compatível com Chat Completions. A API real não será chamada nos testes. Regex
de minimização reduz exposição, mas não garante anonimização de texto livre.
Separação de instruções, schema e validação de evidências reduzem prompt injection,
sem prometer imunidade. Sem OCR, dataset em inglês, score heurístico e revisão
humana permanecem limitações. Sem publicação, commits ou push nesta execução.
