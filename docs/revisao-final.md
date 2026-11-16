a# Revisão final — experiência e demonstração acadêmica

## Diagnóstico das telas

| Prioridade | Problema observado no código/telas | Ajuste |
|---|---|---|
| Alta | Acurácia e F1 no mesmo eixo percentual dificultavam interpretar F1 | Dois gráficos, escalas explícitas e valores com unidades originais |
| Alta | Textos de 8–12 px, cores auxiliares claras e família de fonte dependente de variável CSS | Fonte de sistema explícita, textos ampliados e cores com mais contraste |
| Alta | Menu móvel oculto por transformação mantinha links no percurso de teclado | Visibilidade controlada, foco contido no menu, Escape e retorno de foco |
| Alta | Experiência não avaliada na demo aparecia como informação não estabelecida | Explicação específica de que o modo simulado não avalia experiência |
| Média | Limite metodológico só no fim da página de experimentos | Nota junto do resumo e do gráfico na visão geral |
| Média | Exemplo fictício ficava abaixo dos formulários | Ação no cabeçalho e três etapas visíveis antes dos campos |
| Média | Escala do indicador podia parecer probabilidade de compatibilidade | Título ilustrativo no modo demo, badge e fórmula visível |
| Média | Tabela móvel dependia de arraste horizontal sem foco próprio | Região nomeada, foco por teclado e cabeçalhos semânticos |
| Média | Falha da matriz só alterava o texto alternativo da imagem quebrada | Mensagem visível mantendo as métricas disponíveis |
| Média | Células vazias na comparação confundiam ausência e falha do LLM | Mensagens distintas para sem registro, não avaliado e indisponível |
| Baixa | Erro de categorias não aparecia na visão geral | Mensagem específica com opção de tentar novamente |

## Integridade e precisão

Dados originais de `models/comparacao_modelos.csv`:

| Classificador | Acurácia | F1 macro |
|---|---:|---:|
| Regressão logística | 68,61% | 0,6393 |
| Random Forest | 75,05% | 0,6896 |
| MLP | 61,57% | 0,5610 |

Random Forest selecionado pelo maior F1 macro. Nenhuma nova métrica criada.
A imagem da matriz e o classificador continuam originais. Precision, recall,
distribuição e contagens ausentes são declarados, sem gráficos fictícios.
O split 80/20 e a configuração de TF-IDF têm como fonte `train.py`, não o CSV.
Modelo e teste de apresentação não foram retreinados.

## Conferência automatizada e visual

Os testes de navegador incluem comparação da tabela com o CSV, contraste e regras
WCAG A/AA verificáveis pelo axe, fluxo de demonstração, comparação, relatório,
falha de LLM/imagem, upload inválido, menu por teclado e reflow em 320/390 px.
Capturas são produzidas em `frontend/test-results/`. O registro dos comandos e
resultados finais está em [validacao.md](validacao.md).

Uma auditoria automática não certifica acessibilidade. Conferir manualmente leitor
de tela, navegação em outro navegador, legibilidade no projetor, zoom a 200% e o
tempo de fala. O roteiro padrão não precisa de provedor LLM: o modo é explicitamente
simulado. Se a avaliação exigir LLM efetivo, testar separadamente uma chamada ao
provedor com texto fictício autorizado, sem apresentar simulação como IA generativa.

## Escopo das alterações desta revisão

Frontend: `src/App.tsx`, `src/components/common.tsx`, `src/lib/format.ts`,
`src/pages/Dashboard.tsx`, `Experiments.tsx`, `Analyze.tsx`, `Results.tsx`,
`Compare.tsx`, `src/index.css`, `tests/application.spec.ts` e dependência de teste
axe em `package.json`/`package-lock.json`.

Documentação: README, roteiro cronometrado, slides, exemplos fictícios, este relatório
e registro de validação. Sem mudanças de backend, modelos, autenticação, banco,
retreinamento, commits ou push.
