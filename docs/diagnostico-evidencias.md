# Diagnóstico de unsupported_evidence

## Regra identificada e alcance do diagnóstico

A mensagem anterior juntava duas condições: `contains(requisito, vaga)` e
`contains(requisito, evidencia)`. Ela era posterior à validação da estrutura e
da citação. Portanto, a mensagem identifica essa regra, mas não qual das duas
condições falhou, nem qual item da resposta real foi recusado.

Reprodução fictícia confirmada antes da mudança:

- Vaga: `Experiência com Java.`
- Currículo: `Desenvolvi sistemas em Java.`
- Habilidade extraída: `Java`, com a frase completa acima como evidência.
- Requisito extraído: `Experiência com Java`, com a mesma citação.

O requisito existia na vaga, a citação era literal e a habilidade estava nos dois
textos, mas a frase inteira da vaga não existia no currículo. O caso era recusado.
Não foi recuperada nem registrada a resposta da Groq da execução relatada: a
condição exata daquela execução só será conhecida ao repetir com os novos códigos.

## Correção limitada

O requisito continua precisando ocorrer literalmente na vaga, com limites de
palavra. Se também ocorre na citação, mantém-se o comportamento anterior.
Se somente a redação da vaga difere, procuram-se competências já validadas em
`habilidades`, presentes literalmente no requisito, na vaga e na citação completa
associada. Publicam-se **apenas essas competências**, com a citação original.

No exemplo, publica-se `Java`, não a frase inteira da vaga. Um requisito que pede
cinco anos de experiência avançada com Java e AWS não ganha esses qualificadores
por uma simples menção a Java. A justificativa pública explicita essa restrição.
Não há inferência de sinônimos: `JUnit` não comprova automaticamente o requisito
`Testes automatizados`. Requisito ausente da vaga ou competência sem apoio no
currículo continuam gerando abstenção. Sem uma habilidade verificada comum, uma
frase divergente também é recusada. O prompt recomenda termos curtos da vaga.

## Contrato e correspondência

| Campo | Verificação |
|---|---|
| `habilidades[].evidencia` | Uma passagem completa exata do currículo minimizado e limitado, incluindo pontuação |
| `habilidades[].habilidade` | Ocorrência com limites de palavra na própria evidência |
| `experiencia_profissional[]` | Cada item é uma passagem completa literal |
| `evidencia_anos_experiencia` | Passagem literal, obrigatória quando há anos; duração explícita compatível |
| `requisitos_atendidos[].requisito` | Ocorrência literal na vaga; suporte na citação ou redução às competências verificadas comuns |
| `requisitos_atendidos[].evidencia` | Uma passagem completa literal; não uma lista nem várias frases concatenadas |
| `requisitos_sem_evidencia[]` | Termos existentes na vaga, sem contradizer menções positivas ou associações aceitas |

Busca de termos ignora caixa e acentos; preserva pontuação e espaços internos,
sem equivalência de sinônimos. A citação completa é exata: caixa, pontuação e
quebras internas não são normalizadas. Espaços nas bordas são removidos. Frases
separam-se após `. ! ?` seguidos de espaço; itens após `;` (preservado); linhas
LF/CRLF/CR também separam. Vírgulas não criam unidades. A regra de negação,
ausência e desejo continua conservadora.

No contrato do provedor são obrigatórios `habilidades`, `experiencia_profissional`,
`anos_experiencia`, `evidencia_anos_experiencia`, `requisitos_atendidos` e
`requisitos_sem_evidencia`. Os dois campos de anos aceitam null, mas não podem
ser omitidos. `nota_aderencia` é opcional, com padrão null. Campos adicionais
são rejeitados. Campos `requisito`, `habilidade` e `evidencia` são obrigatórios
nos seus respectivos objetos. Listas vazias são válidas e não autorizam nota.

Múltiplas evidências são objetos separados. Preservam-se pares distintos da
mesma competência e citação; pares idênticos são deduplicados. Todo item é
verificado, inclusive duplicatas: um segundo item inválido causa abstenção da
análise contextual inteira, sem publicar resultados parciais. Há limite de 30
associações publicadas, preservando o contrato; excedê-lo gera diagnóstico.

## Diagnósticos seguros

O log `talentmatch.evidence` e o campo adicional `llm_diagnostic` da resposta
contêm somente códigos fixos, caminhos de campos conhecidos e índice numérico
base zero. Não incluem valores de requisitos, citações, currículos, dados
pessoais, chave ou resposta bruta. Propriedades desconhecidas do JSON são
identificadas apenas como `unknown`.

Exemplo fictício:

```json
{
  "rule": "requirement_not_in_job",
  "field": "requisitos_atendidos.requisito",
  "source": "vaga",
  "category": "text",
  "index": 1
}
```

| Regra | Significado |
|---|---|
| `requirement_not_in_job` | Requisito informado não foi localizado na vaga |
| `requirement_not_in_evidence` | Não há apoio literal nem habilidade verificada comum na citação |
| `incomplete_passage` | Citação encontrada como recorte de uma passagem maior |
| `quote_not_found` | Citação não coincide com uma unidade; pode ser texto alterado, inventado ou unidades juntadas |
| `nonpositive_evidence` | Passagem contém padrão de negação, ausência ou desejo |
| `skill_not_in_evidence` | Competência não ocorre na própria citação |
| `duration_evidence_missing` / `duration_not_supported` | Duração sem prova ou incompatível |
| `missing_requirement_not_in_job` / `contradictory_requirement` | Item sem evidência inventado ou contraditório |
| `verified_requirements_limit` | Mais de 30 associações após verificação |
| `json_invalid` / `schema_invalid` / `response_size_invalid` | Falha de estrutura da resposta |

Falhas de estrutura mantêm `invalid_llm_response`; falhas de fundamentação
mantêm `unsupported_evidence`. `llm=null`, resultado ML preservado e HTTP 200
com `llm_error` seguem o comportamento existente. `llm_diagnostic=null` significa
que não houve diagnóstico de validação; falhas de transporte continuam separadas.

### Omissão limitada de nomes de habilidades sem correspondência

Exceção recuperável: `skill_not_in_evidence` em `habilidades[].habilidade`.
A citação precisa ter passado primeiro pela validação de passagem completa,
literal e sem padrões de negação/ausência/desejo. Se o nome não ocorre nela,
somente esse item é omitido. O prompt agora exige copiar o termo da respectiva
citação, sem tradução, expansão de siglas, generalização ou sinônimos.
JUnit não vira automaticamente a habilidade `Testes unitários`.

O log usa `evidence_item_omitted`, regra `skill_not_in_evidence`, índice original
e `action=omit`, sem nome ou citação. A justificativa pública registra somente
a quantidade omitida. Não há novo campo no contrato público: uma omissão isolada
não preenche `llm_error` ou `llm_diagnostic`, pois não interrompe a análise.

O resumo usa somente habilidades aceitas e experiências verificadas. Requisitos
com redação diferente só usam a lista filtrada como âncora. Todos os requisitos,
experiências e durações continuam sujeitos às verificações anteriores, de forma
independente. Se um deles depende da habilidade omitida e não tem suporte próprio,
a análise contextual inteira continua em abstenção; não se publica a afirmação
nem um resultado parcial dessa falha. Uma competência pode constar em um requisito
se outra citação comprovar sua ocorrência independentemente: omitir um par incorreto
não invalida evidência correta em outra passagem.

Citações inventadas ou recortadas, experiência sem prova, requisitos ausentes da
vaga e estrutura inválida não se tornam recuperáveis. Se não restar evidência
aceita em nenhum campo, retorna-se abstenção explícita. A nota permanece null
em todos os casos ao vivo, mesmo quando o provedor retorna 100.

## Limitações e validação real pendente

Os testes usam entradas fictícias e SDK com transporte local simulado. Eles
comprovam as regras locais, não a frequência de erros da Groq. Após reiniciar o
backend, repetir uma análise autorizada e observar apenas `rule`, `field`,
`source`, `category` e `index` permitirá distinguir a falha específica.
Nenhuma chamada externa de inferência foi feita nesta correção.

Continuam pendentes equivalência semântica, qualidade das extrações e influência
do contexto ML. Termos genéricos, negações com sentidos ambíguos e PDFs com
quebras artificiais podem exigir revisão humana. Correspondência literal não
comprova experiência, competência ou veracidade. Notas ao vivo permanecem null,
inclusive quando o provedor devolve 100. A lista pode ser incompleta e a associação
não comprova todos os qualificadores da vaga. Não há método de pontuação validado.
