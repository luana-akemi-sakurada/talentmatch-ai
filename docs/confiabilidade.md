# Correções de confiabilidade antes de novo treinamento

Atualização final: perguntas de entrevista foram removidas do contrato e das
interfaces. A integração Groq usa Structured Outputs nos modelos compatíveis,
sem dispensar as verificações abaixo. Contrato e erros atuais em
[estabilizacao-llm.md](estabilizacao-llm.md).

Estas correções usam o [diagnóstico anterior](avaliacao-modelo.md) como referência.
O modelo, vocabulário, pré-processamento e resultados experimentais originais
permanecem intactos. As mudanças são validação, abstenção e transparência.

## 1. Contrato de evidências do LLM

O provedor agora extrai dados para `GroundedLLMResponse`, separado do contrato
publicado ao frontend. O servidor não publica resumos, avaliações ou lacunas
livres escritos pelo provedor. Compõe esses campos a partir das
evidências aceitas, mantendo os nomes anteriores da resposta pública.

- Habilidades: `{habilidade, evidencia}` com passagem completa do currículo e
  ocorrência da habilidade com limites de palavra; Java não casa com JavaScript.
  Nome ausente da própria citação válida causa omissão somente desse item, com
  índice no log e quantidade na justificativa. Citação inválida continua fatal;
  outros campos não podem usar a habilidade descartada sem suporte independente.
- Requisitos atendidos: requisito literalmente presente na vaga e na passagem
  citada do currículo. Quando só a redação da vaga diverge, publica-se apenas
  a competência já verificada que ocorre no requisito, na vaga e na citação.
  Qualificadores não sustentados não são confirmados. Não se aceita uma citação
  de Java para justificar AWS. Regras e códigos em [diagnostico-evidencias.md](diagnostico-evidencias.md).
- Experiência: passagens completas, existentes no texto efetivamente transmitido.
  Anos exigem também citação de uma duração explícita em português/inglês.
  Não se somam empregos, não se inferem intervalos de datas, faixas ou limites.
- Frases/linhas/itens separados por ponto e vírgula são unidades de citação.
  O ponto e vírgula pertence ao item anterior e deve ser preservado na citação,
  mesmo sem espaço antes do próximo item. Pontos finais, exclamação e interrogação
  também são preservados; separam frases quando seguidos de espaço ou quebra.
  Quebras LF, CRLF e CR separam linhas; vírgulas permanecem dentro da passagem.
  Espaços nas bordas são ignorados, mas não se normaliza pontuação ou texto interno.
  Recortar apenas uma palavra não permite ocultar uma negação da mesma passagem.
- Negação/ausência/desejo em padrões reconhecidos bloqueiam afirmações positivas.
  A preposição portuguesa “no” não é confundida com “no experience” em inglês.
- Requisitos duplicados, contraditórios ou sem referência à vaga são recusados.
  Uma menção literal positiva não pode ser listada simultaneamente como ausente.
- Resposta fora do schema ou com evidência inválida não publica conclusões ou nota:
  `llm=null`, erro contextual explícito e resultado ML preservado.

Essas regras são conservadoras e literais. Não são um verificador semântico nem
uma comprovação da veracidade do currículo. Podem recusar uma equivalência válida
ou uma passagem que usa negação em outro sentido. Frases completas também podem
conter conteúdo enganoso; o texto continua sendo dado não confiável.

## 2. Abstenção explícita de pontuação

**Decisão temporária: nenhuma nota numérica do LLM é publicada ao vivo**, inclusive
quando algumas evidências forem válidas. Elas continuam sendo mostradas. Não há
método validado para determinar se a lista de requisitos está completa, quais são
seus pesos e como convertê-los em nota. Limitar a nota por um teto arbitrário ou
calcular uma porcentagem sobre uma lista potencialmente incompleta repetiria a falha.

- Sem evidências suficientes: `nota_aderencia=null`,
  `abstention_reason="insufficient_evidence"` e resumo de abstenção.
- Com evidências textuais verificadas: preservá-las, mas `nota_aderencia=null` e
  `abstention_reason="score_not_validated"`.
- Notas do provedor como 80, 95 ou 100 não atravessam essa política; não são
  publicadas nem substituídas por uma nota criada no backend.
- O frontend e o Streamlit exibem “sem pontuação”/abstenção, nunca convertem null
  para zero. A ausência da nota não significa baixa aderência.
- O modo **demo** mantém sua fórmula literal ilustrativa e o rótulo de simulação.
  Seu resultado não é uma nota validada de contratação e não prova uso de LLM.

O schema continua aceitando um número devolvido pelo provedor para que esse caso
seja testado e descartado com segurança; o prompt pede explicitamente null.
Resumos livres extras são recusados pelo schema, não usados para completar a tela.

## 3. Cobertura TF-IDF sem limiar de confiança arbitrário

O serviço transforma o texto uma vez com o TF-IDF original e mede:

| Campo em `ml.coverage` | Significado |
|---|---|
| active_features | Atributos não nulos, incluindo unigramas e bigramas |
| analyzed_unigrams | Unigramas únicos após o analisador e stop list atuais |
| known_unigrams | Unigramas presentes no vocabulário aprendido |
| unknown_unigrams | Analisados menos conhecidos |
| unigram_coverage | Conhecidos/analisados; null se o denominador é zero |
| zero_vector | Nenhum atributo TF-IDF não nulo |

Vetor vazio é uma condição estrutural, não um limiar estatístico. Nesse caso,
`ml.status="abstained"`, `predicted_area="INDETERMINADA"` e `top_categories=[]`.
Não se executa a floresta nem se apresenta a saída arbitrária de 62,67% para BD.
O modelo serializado mantém esse comportamento bruto; a proteção está no serviço.
Uma categoria não é substituída pela interpretação de outro modelo.

**Toda cobertura parcial recebe aviso com os valores observados**, incluindo os
casos extremamente esparsos. Exemplo reproduzido do relatório: finanças PT tem
1/46 unigramas reconhecidos (aproximadamente 2,17%). A previsão é preservada com
aviso; não criamos um corte para chamar essa saída de confiável ou não confiável.
Para o currículo Java original, a previsão continua BD 58%, com 5/22 unigramas
reconhecidos, cinco atributos ativos e 17 unigramas ignorados.

Os indicadores são retornados no JSON/relatório e registrados pelo logger
`talentmatch.classifier` no nível INFO, sem texto, termos, nome de arquivo ou chaves.
Para coletar esses eventos em produção, configure esse logger no seu coletor;
nesta versão não se cria um arquivo de histórico. A interface mostra os avisos
diretamente no resultado, além das informações de transparência.

A cobertura usa a stop list inglesa e o vocabulário atual: não é comparação
linguística neutra, medida de competência, calibração ou garantia de acerto.
Mesmo cobertura integral de unigramas não garante contexto adequado.

## 4. Independência entre ML e LLM: opção testável, padrão preservado

```env
LLM_INCLUDE_ML_CONTEXT=true
```

O padrão continua incluindo `area_ml` e `confianca_ml` quando há previsão válida,
como antes. O prompt continua dizendo que a categoria não prova competência.
O resultado público informa `llm.ml_context_included`.

Com `false`, esses dois campos são omitidos. Testes compararam o mesmo currículo
e vaga com duas categorias/probabilidades diferentes: os payloads enviados são
idênticos quando a opção está desligada. Portanto, o caminho consegue funcionar
sem depender da categoria ML. Isso **não mede** qualidade ou viés de um LLM real.

Quando o ML se abstém por vetor vazio, não há categoria válida para enviar: o
contexto é omitido mesmo no padrão. O LLM pode extrair evidências do texto original
minimizado, pois seu vocabulário não é o TF-IDF. Falha do classificador por artefato
indisponível continua sendo erro de serviço, não resposta simulada.

Configuração diferente de true/false é recusada antes de qualquer chamada. O `.env`
real não foi modificado; só o exemplo documenta a opção. Não há motivo experimental
suficiente para alterar o padrão nesta etapa. Comparação futura deverá avaliar
contexto correto/incorreto/omitido com revisão humana e chamadas autorizadas.

## 5. Compatibilidade e implantação local

Endpoints e campos anteriores foram preservados. A diferença de tipo necessária
é `llm.nota_aderencia`, agora `integer | null`, com motivo explícito de abstenção.
O frontend incluído foi atualizado para tratar null e listas ML vazias; Streamlit
também usa o serviço protegido. Clientes externos que assumiam nota sempre numérica
devem aceitar null. `ml.status`, `ml.coverage`, `ml.warnings`,
`llm.abstention_reason` e `llm.ml_context_included` são campos adicionais.

O contrato de extração do **provedor** mudou para exigir as evidências; não se
confunde com o JSON de saída da aplicação. O mock HTTP local foi atualizado junto
com o adaptador. O [OpenAPI](openapi.json) registra a saída pública atual.

## 6. O que ainda exige avaliação experimental

1. Definir catálogo de requisitos, completude, pesos e uma regra de pontuação
   auditável antes de voltar a publicar notas ao vivo.
2. Medir falsos positivos/negativos das regras de evidência, negação, tokenização
   e duração em currículos reais autorizados, com anotação independente.
3. Avaliar a influência do contexto ML em um LLM real; mocks só provam isolamento
   do payload e tratamento local de respostas.
4. Calibrar e validar limiares para cobertura parcial, se forem usados futuramente
   para abstenção. Não adotar percentuais de confiança ou cobertura por intuição.
5. Recuperar o dataset e melhorar representação/treinamento de forma consistente.
   Esta etapa não ensina PostgreSQL, Docker ou português ao modelo preservado.
6. Avaliar ataques semânticos, redações ambíguas, projetos acadêmicos versus
   experiência profissional, idiomas adicionais e formatos de PDF. As verificações
   literais não resolvem essas distinções ou garantem anonimização.

## Arquivos e verificações

- Backend: schemas, `services/classifier.py`, novo `services/grounding.py`,
  `services/analysis.py`, `llm.py`, `app.py` e testes.
- Frontend: tipos, apresentação de avisos/nota ausente em `Results.tsx`, texto
  de limitações em `Ethics.tsx` e testes de compatibilidade; sem novas telas ou
  fluxo complexo.
- Configuração/documentação: `.env.example`, README, API/OpenAPI, este documento,
  notas de atualização no relatório histórico e registro de validação.
- Mock: `postman/mocks/llm/handler.js`, verificador HTTP e contexto da simulação.

Nenhum artefato em `models/`, função `limpar_texto`, código de treinamento ou
resultado do diagnóstico histórico foi modificado. Não houve chamada paga,
retreinamento, commit ou push. Resultados finais dos testes em [validacao.md](validacao.md).
