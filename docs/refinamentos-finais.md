# Refinamentos finais de análise e experiência

## Classificador e perfil contextual separados

O Random Forest mantém as 24 classes e todas as probabilidades originais para
vetores não vazios. `llm.perfil_profissional`, quando disponível, contém
`descricao` e `evidencia`. A designação profissional deve ocorrer na passagem
completa citada do currículo minimizado. A origem LLM e a origem ML aparecem
separadamente no resultado e na comparação. Não há substituição da categoria ML.

Por segurança, o perfil não é uma síntese livre: não se infere Backend apenas
por encontrar APIs REST, nem senioridade por anos ou tecnologias. Se não existir
designação citável, retorna-se null. Perfil com estrutura válida mas sem apoio
literal é omitido e registrado por código, sem conteúdo textual. Erros do
contrato JSON continuam gerando abstenção contextual.

## Viabilidade do índice de cobertura — não implementado

O contrato existente contém `requisitos_atendidos` e `requisitos_sem_evidencia`.
Ele não contém requisito obrigatório/desejável, evidência dessa classificação
na vaga, inventário completo ou estado indeterminado por requisito. A lista é
extraída pelo LLM e pode omitir itens. O denominador não é verificável.

Por isso **não se implementou número, pesos ou fórmula de cobertura ao vivo**.
A interface distingue associações com evidência, itens sem evidência informada
e cobertura total indeterminada. A contagem de nomes únicos com evidência é
descritiva, não um numerador ponderado ou denominador completo. Pesos, numerador
ponderado e denominador são explicitamente não estabelecidos. Não se inventou
obrigatoriedade com base em tecnologias citadas ou na palavra “Requisitos”.

Uma etapa futura precisa de inventário revisado, prioridade expressa e citada
na vaga, deduplicação de conceitos e estados encontrado/sem evidência/indeterminado.
Uma eventual fórmula ponderada deve apresentar todos os termos e pesos
ilustrativos configuráveis e abster-se se a identificação não for suficiente.
Isso exigiria avaliação e não foi incluído como funcionalidade nesta entrega.
O indicador legado da demo continua isolado e rotulado como simulação.

## Escopo final simplificado

As perguntas foram removidas. O contrato e a integração final com Structured Outputs
são descritos em [estabilizacao-llm.md](estabilizacao-llm.md).

## Fluxo principal e demonstração offline

- `/analise` e `/comparacao`: somente LLM + classificador local, sem escolha de
  modo; envio externo exige a confirmação já existente no formulário.
- `/demonstracao` e `/demonstracao/comparacao`: acesso direto documentado, fora
  do menu principal, sem chamada ao provedor e com avisos explícitos.
- Endpoints aceitam `mode=demo` explicitamente para testes/offline; o padrão
  foi alterado para `live`. Clientes que usavam o padrão antigo devem enviar
  `mode=demo` se precisarem de simulação.
- Preencher exemplo fictício não altera o fluxo. Falha do LLM preserva o ML e
  informa o erro; não produz resposta simulada automaticamente.

## Limitações acadêmicas

O perfil citável é propositalmente limitado e não equivale a uma classificação
contextual validada. As listas de requisitos não são avaliação de competência,
probabilidade de contratação ou catálogo completo. O classificador original
continua com as limitações de idioma/dataset do relatório anterior.

Os testes usam fixtures fictícias e mocks locais. Não houve inferência externa,
retreinamento, alteração de credenciais, commit ou push. Avaliar a qualidade do
novo prompt na Groq exige uma execução real autorizada, com revisão humana dos
perfis, citações e abstenções.
