# Demonstração acadêmica — 4min30s

Objetivo: demonstrar entrada, processamento e saída, os experimentos reais e o uso
responsável. O roteiro padrão usa **ML real + contexto simulado**, sem rede externa
ou cobrança de LLM. API Python e frontend precisam estar iniciados localmente.

**Separação atual:** o roteiro offline abaixo é acessado diretamente por
`/demonstracao` e `/demonstracao/comparacao`, fora do menu principal. `/analise`
e `/comparacao` usam exclusivamente o provedor LLM. O botão de exemplo somente
preenche textos. Não alterna o modo nem autoriza chamadas.

Para demonstrar LLM real com autorização, use `/analise`, confirme o envio e
reserve o trecho de resultados para: categoria ML versus perfil citável do LLM;
habilidades e experiência explícita; requisitos encontrados/sem evidência e cobertura
total indeterminada. O perfil pode não existir se faltar designação citável.
Não há geração de perguntas. Não prometa uma saída nem um índice numérico.

## Preparação antes de apresentar

1. Inicie API e frontend conforme README; confirme o indicador de classificador
   disponível. Abra `/experimentos` e confira que a matriz carregou.
2. Separe os arquivos fictícios [candidato-a.txt](exemplos/candidato-a.txt),
   [candidato-b.txt](exemplos/candidato-b.txt) e [vaga.txt](exemplos/vaga.txt).
3. Execute uma análise demonstrativa e uma comparação antes da apresentação.
   Não é necessário configurar chave para isso. Não use currículos reais.
4. Use zoom e tamanho de janela adequados ao projetor. Deixe os resultados
   importantes visíveis; treine as mudanças de tela sem ler todos os textos.
5. Tenha as capturas geradas pelos testes como apoio, se disponíveis em
   `frontend/test-results/`. Identifique-as como capturas de uma execução anterior.

## Roteiro cronometrado

| Tempo | Tela / ação | Fala sugerida |
|---|---|---|
| 0:00–0:25 | **Visão geral** (`/`) | “O TalentMatch apoia a leitura de currículos em relação à vaga. Ele organiza sinais e evidências; a decisão continua humana.” |
| 0:25–1:10 | **Experimentos** (`/experimentos`), resumo e gráficos | “Comparamos três classificadores. O Random Forest foi escolhido pelo F1 macro: 0,6896, com acurácia de 75,05%. Os dados vêm do CSV original. O mesmo teste foi usado para escolher e avaliar, sem avaliação final independente.” |
| 1:10–1:25 | Matriz e dataset, passagem rápida | “A matriz é a imagem original. Precision, recall e distribuição não foram preservados; por isso não apresentamos números para eles.” |
| 1:25–2:00 | Abrir `/demonstracao` → **Usar exemplo fictício** → **Analisar currículo** | “Este acesso é exclusivo para demonstração offline. O ML é real; o contexto é simulado e não comprova integração com LLM.” |
| 2:00–2:50 | **Resultado**: área, indicador e evidências | “Aqui separamos as probabilidades da área e o indicador ilustrativo. Este indicador só compara termos reconhecidos. Ele não é chance de contratação. A experiência não é avaliada na simulação. As citações mostram o que merece investigação.” |
| 2:50–3:40 | Abrir `/demonstracao/comparacao` → selecionar A e B → colar `vaga.txt` → comparar | “Os dois currículos recebem a mesma vaga. A ordem é a de envio, sem ranking. Comparo competências e trechos; não concluo que uma pessoa é melhor que outra.” |
| 3:40–4:10 | Abrir análise individual na comparação; mostrar lacunas e **Ética** | “Dados passam por minimização, mas ela pode falhar. Ausência de evidência não significa ausência de competência; o resultado exige revisão humana.” |
| 4:10–4:30 | **Visão geral** → **Ver resultado** → **Baixar relatório** | “O relatório identifica o modo de execução e preserva os avisos. A evolução mantém o modelo original e torna seus resultados e limites visíveis.” |

**Versão de 3 minutos:** reserve 20 s para introdução, 40 s para experimentos,
70 s para análise/resultado, 30 s para comparação já preenchida e 20 s para ética.
**Versão de 5 minutos:** use os 30 s restantes para ampliar a matriz e explicar
TF-IDF: palavras e pares de palavras recebem pesos para distinguir áreas.

## Como interpretar sem prometer resultados

- Não prometa uma categoria para o exemplo. Leia a previsão efetivamente retornada.
  Um texto curto ou em outro idioma pode ser mal classificado.
- O indicador demo é termos da vaga encontrados / termos reconhecidos × 100.
  Sem termo reconhecido, o valor é zero e não é interpretável como compatibilidade.
- A nota demo e as lacunas não são resultados de um LLM. O resumo sinaliza
  isso. Os exemplos não são dados do dataset de treinamento.
- Acurácia/F1 medem classificação de área, não qualidade da pessoa ou aderência.
- A comparação não avalia duração de experiência no modo simulado. Consulte o
  currículo original e não apresente uma informação não calculada como ausente.

## Contingências

- **Sem internet/provedor:** mantenha demo; após instalar dependências, esse fluxo
  usa apenas serviços locais. Não altere para o modo ao vivo durante o roteiro.
- **Falha da API local:** verifique os dois processos e a porta antes de começar.
  Se persistir, use capturas como evidência anterior, sem alegar execução ao vivo.
- **Matriz ausente:** a interface informa a falha e mantém a tabela do CSV visível.
- **Provedor indisponível no modo ao vivo:** ML permanece; contexto fica marcado
  como indisponível. Não há fallback silencioso para resposta simulada.
- **Avaliação exige LLM efetivo:** prepare uma demonstração adicional com provedor
  configurado e texto fictício autorizado. Isso pode ter custo; não foi executado
  nos testes desta revisão e não pode ser comprovado pelo modo demonstrativo.

Não atualize a aba entre análise e download: o resultado é temporário. Sair da tela
de comparação apaga seu estado. O resultado individual continua na memória da aba
até limpar ou atualizar; pode ser reaberto pela visão geral durante o roteiro.
