# TalentMatch AI 2.0 — textos para dez slides

Material para montar os slides; não é uma apresentação renderizada.
A demonstração prática tem roteiro separado de **4min30s** em
[demonstracao.md](demonstracao.md). Não é necessário ler todos os textos na tela.

## 1. O problema: analisar sem perder contexto

**Texto do slide**
- Currículos apresentam experiências em formatos diferentes.
- Requisitos da vaga precisam de evidências, não apenas palavras-chave.
- Sinais automáticos exigem interpretação humana.

**Visual sugerido:** currículo → requisitos → evidências; sem estatísticas ilustrativas.
**Tela:** Visão geral (`/`), recorte do fluxo de trabalho.

## 2. Objetivo: apoiar a triagem inicial

**Texto do slide**
- Identificar a provável área profissional com Machine Learning.
- Organizar competências, experiência e evidências em relação à vaga.
- Apoiar decisões humanas, sem rejeição ou ranking automático.

**Visual sugerido:** três etapas do formulário.
**Tela:** Nova análise (`/analise`).
**Nota de fala:** TDE2 / Sistemas de Informação Inteligentes / PUCPR.

## 3. A solução em um fluxo

**Texto do slide**
- Entrada: PDF/TXT ou texto + descrição da vaga.
- Processamento: minimização, classificação ML e contexto.
- Saída: categoria ML, perfil contextual citável, evidências e lacunas.
- Cobertura documental: requisitos evidenciados ÷ identificados, sem pesos;
  sem percentual quando a lista ou as avaliações forem indeterminadas.

**Visual sugerido:** diagrama entrada → processamento → saída.
**Tela:** `/analise` e `/resultado`, após executar exemplo fictício.
**Nota de fala:** o perfil contextual não substitui a categoria ML. Se não houver
designação profissional citável no currículo, ele fica indeterminado.

## 4. Arquitetura incremental

**Texto do slide**
- React/TypeScript para a interface; FastAPI/Pydantic para a API.
- Pipeline scikit-learn original reutilizado no backend.
- Sem banco ou retenção permanente de currículos nesta versão.

**Visual sugerido:** diagrama de [arquitetura.md](arquitetura.md), com ramo demo/LLM.
**Tela:** diagrama, sem expor arquivos de configuração ou chaves.

## 5. Dataset e transformação do texto

**Texto do slide**
- Resume Dataset, do Kaggle: currículos em inglês.
- Limpeza + TF-IDF: até 8.000 atributos, palavras e pares de palavras.
- Divisão estratificada definida no script: 80% treino / 20% teste.

**Visual sugerido:** fluxo texto → TF-IDF → categoria, já disponível no sistema.
**Tela:** Experimentos (`/experimentos`), seção de processamento e dataset.
**Nota de fala:** dataset e contagens originais ausentes nesta cópia; não criar gráfico de distribuição.

## 6. Três classificadores comparados

**Texto do slide**
- Regressão logística: referência linear.
- Random Forest: combinação de 300 árvores.
- MLP: rede neural com camadas de 256 e 64 neurônios.

**Visual sugerido:** três cartões com os nomes, sem notas inventadas.
**Tela:** `/experimentos`, tabela dos classificadores.
**Nota de fala:** fonte das configurações: `train.py`; critério de escolha: F1 macro.

## 7. Resultados reais e seus limites

**Texto do slide**

| Classificador | Acurácia | F1 macro |
|---|---:|---:|
| Regressão logística | 68,61% | 0,6393 |
| **Random Forest** | **75,05%** | **0,6896** |
| MLP | 61,57% | 0,5610 |

- Mesmo teste usado para seleção e avaliação; sem teste final independente.

**Visual sugerido:** dois gráficos de barras: acurácia em % e F1 entre 0 e 1.
**Tela:** `/experimentos`, resumo + gráficos + tabela. Matriz PNG original como apoio.
**Nota de fala:** fonte `models/comparacao_modelos.csv`. Precision/recall indisponíveis.
Esses resultados classificam área; não validam a aderência à vaga.

## 8. Análise contextual essencial

**Texto do slide**
- Classificação profissional: modelo ML real.
- Perfil contextual: designação do currículo, com citação e origem LLM separada.
- Perfil, habilidades, experiência, requisitos, pontos fortes e lacunas fundamentados.
- JSON estruturado na Groq, validação Pydantic e conferência literal das citações.
- Comparação na ordem de envio, sem ranking.

**Visual sugerido:** resultado com categoria ML, perfil contextual e evidências;
usar captura de teste apenas se identificada como fixture, nunca como LLM real.
**Tela:** `/analise` → `/resultado` → `/comparacao`, com os textos de `docs/exemplos/`.
**Nota de fala:** fluxo principal usa LLM; não há seletor. Demo offline por acesso
direto a `/demonstracao`, fora do menu. Não há fallback silencioso na falha.

## 9. Ética e limitações

**Texto do slide**
- Minimização reduz exposição; não garante anonimização.
- Dataset em inglês e LLM podem produzir vieses e erros.
- Sem índice numérico: obrigatoriedade e completude dos requisitos não estão estabelecidas.
- Perguntas e evidências exigem revisão; correspondência literal não prova competência.

**Atualização:** a nota ilustrativa existe apenas no modo demo. No modo ao vivo,
o sistema publica evidências verificadas e abstenção de pontuação; vetor TF-IDF
vazio também gera abstenção ML, sem categoria/probabilidades.

**Visual sugerido:** três princípios, sem percentuais de redução de risco.
**Tela:** Ética e transparência (`/etica`).
**Nota de fala:** sem OCR; ausência de evidência não prova ausência de habilidade.

## 10. Conclusão: apoio explicável, com limites visíveis

**Texto do slide**
- Fluxo fullstack funcional com artefatos originais preservados.
- Resultados separados por origem e limitações declaradas.
- Próximos estudos: avaliação independente, idioma e vieses.

**Visual sugerido:** fluxo final + uma pergunta para discussão.
**Tela:** `/resultado`, perfil, evidências e lacunas; sem perguntas geradas.
**Nota de fala:** os estudos futuros não foram executados. Reportar testes conforme
[validacao.md](validacao.md), sem generalizar mocks para qualidade do LLM real.
