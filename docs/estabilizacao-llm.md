# Entrega final: análise essencial com Groq

Atualização posterior: a [cobertura documental](cobertura-requisitos.md) acrescenta
um indicador determinístico independente. A nota livre do LLM continua ausente.

## Escopo encerrado

Foram removidos geração, validação, schemas e exibição de perguntas de entrevista,
incluindo React, Streamlit e demo. A resposta não possui mais
`perguntas_contextualizadas`, `perguntas_entrevista` ou `entrevista_status`.
Os testes exclusivos da função removida foram retirados; os de perfil,
fundamentação, privacidade, ML e integração continuam ativos.

Se uma resposta legada ainda trouxer esses três campos, o adaptador apenas os
descarta antes da validação, inclusive com valores malformados. Isso não afeta
os demais campos. Outras propriedades desconhecidas continuam proibidas.

## Contrato essencial

O provedor extrai habilidades com citações, experiência explícita, duração
quando declarada, requisitos com evidência, requisitos sem evidência e perfil
profissional citável ou null. Resumo, pontos fortes e lacunas são compostos no
servidor a partir dos dados verificados; não são narrativas livres do provedor.
A categoria e as probabilidades do Random Forest continuam independentes.

A nota ao vivo permanece null. Não há cálculo novo de cobertura ou aderência,
nem uso da lista parcial de requisitos como denominador completo. As proteções
anteriores permanecem: citação completa literal, negação/ausência, duração
explícita, requisito existente na vaga, verificação independente das associações
e omissão limitada de nomes de habilidades ausentes da própria citação válida.

## Structured Outputs

A documentação oficial da Groq lista `openai/gpt-oss-120b` e `openai/gpt-oss-20b`
como compatíveis com `json_schema` e `strict: true`. Exige todos os campos em
`required` e `additionalProperties: false` nos objetos; valores sem informação
são representados por null. Fontes:
[Structured Outputs](https://console.groq.com/docs/structured-outputs) e
[GPT-OSS 120B](https://console.groq.com/docs/model/openai/gpt-oss-120b).

Para esses dois modelos no endpoint `api.groq.com/openai/v1`, o adaptador agora
envia `response_format` com schema fechado/obrigatório, incluindo objetos
aninhados. `nota_aderencia` é null no schema transmitido. A designação de perfil
é campo obrigatório na saída estruturada, mas seu valor pode ser null.

O schema transmitido usa tipos, arrays, objetos, referências e uniões com null.
Restrições de tamanho e intervalos continuam no Pydantic local, sem depender
de suporte do decodificador a essas restrições. A transformação não altera
as classes originais de validação. O mesmo schema é descrito no payload para
evitar instruções contraditórias.

Usa-se `reasoning_effort=low`, `max_completion_tokens=3500`, timeout de 45 s e
nenhuma repetição automática. A remoção das perguntas reduz o volume solicitado.
Interrupção por limite de saída tem diagnóstico próprio; não há tentativa
automática de ampliar tokens ou repetir chamadas. Para outros modelos Groq,
usa-se JSON Object Mode, que não garante aderência ao schema. Outros provedores
mantêm seu caminho anterior, sem presumir suporte a Structured Outputs.

Saída estruturada controla formato, não veracidade ou fundamento. Pydantic e
conferência das evidências continuam obrigatórios. Essa compatibilidade foi
verificada na documentação e no payload serializado pelo SDK em transporte
simulado; ainda falta confirmar a aceitação e a qualidade na conta real.

## Erros diferenciados e seguros

| Código público | Situação |
|---|---|
| `llm_not_configured` | Chave ou modelo ausente no processo |
| `llm_auth_error` | HTTP 401, autenticação recusada |
| `llm_permission_denied` | HTTP 403, permissão recusada |
| `llm_model_not_found` | HTTP 404, modelo ou endpoint não encontrado |
| `llm_rate_limited` | HTTP 429 sem indicação inequívoca de quota financeira; limite de requisições/tokens/quota |
| `llm_quota_exceeded` | HTTP 429 com código explícito de quota insuficiente informado pelo provedor |
| `llm_timeout` | Tempo limite excedido |
| `llm_connection_error` | Falha de conexão |
| `llm_request_rejected` | HTTP 400/422, parâmetros ou schema rejeitados |
| `llm_unavailable` | Falhas de serviço, como HTTP 503, ou erro não classificado do SDK |
| `llm_refused` | Recusa explícita do provedor |
| `invalid_llm_response` | JSON/estrutura inválidos, resposta ausente ou interrompida por limite |
| `unsupported_evidence` | Resposta estruturalmente válida sem fundamento verificável |

`llm_diagnostic.rule` separa `json_invalid`, `schema_invalid`,
`response_truncated`, `completion_missing` e erros de evidências. Quando o
provedor informa falha de geração/validação JSON, usa-se `provider_json_rejected`.
HTTP 429 sozinho não comprova falta de créditos; não se inventa esse diagnóstico.
Referência: [erros da Groq](https://console.groq.com/docs/errors).

Não são retornados ou registrados mensagens brutas do provedor, cabeçalhos,
credenciais ou textos completos. FastAPI preserva ML e retorna HTTP 200 com
`llm=null`, `llm_error` e aviso seguro para falha contextual. Streamlit também
preserva o ML e exibe erro seguro. Não há fallback silencioso para simulação.

## Testes locais

Foram reutilizados `docs/exemplos/candidato-a.txt`, `candidato-b.txt` e `vaga.txt`,
com respostas fictícias do provedor, e o caso insuficiente `zzqxv zzqxv` já usado
nos testes de confiabilidade. O SDK real foi exercitado com `httpx.MockTransport`;
nesses testes não há transporte de rede para o provedor.

### Correção do isolamento no navegador

Na execução inicial do Playwright com servidores iniciados manualmente no
PowerShell, atribuir `''` às variáveis LLM removeu essas variáveis. Isso podia
permitir que `load_dotenv` carregasse a configuração real. O servidor registrou
duas tentativas terminadas em `llm_connection_error`, sem resposta do provedor.
Não foi consultado faturamento; ausência de resposta não comprova ausência de
cobrança. Essas tentativas não devem ser tratadas como validação real da Groq.

O isolamento foi corrigido: `PYTHON_DOTENV_DISABLED=1`, credenciais/modelo
removidos e URL LLM restrita ao loopback de teste. O gerenciador automático do
Playwright também define essas proteções. A suíte foi repetida nesse ambiente;
o teste principal agora exige especificamente `llm_not_configured`, em vez de
aceitar qualquer indisponibilidade. Não houve alteração no `.env` ou na chave.

- Compatível: evidências verificadas para Python/SQL/Power BI e lacuna AWS.
- Incompatível: experiência Java/React/Git aceita como contexto, sem requisitos
  da vaga demonstrados; não se transforma incompatibilidade em erro técnico.
- Insuficiente: abstenção explícita, sem nota nem perfil inventado.
- Falhas: autenticação, permissão, modelo, limites/quota, timeout, conexão,
  serviço, recusa, JSON/estrutura, truncamento e evidências inventadas/sem suporte.
- Compatibilidade: perguntas legadas malformadas são ignoradas; validação dos
  campos essenciais e seus limites permanecem estritos.

Os testes sintéticos não medem qualidade estatística do LLM ou do classificador.
Resultados finais e comandos em [validacao.md](validacao.md).

## Teste manual final autorizado

1. Reinicie o backend e confirme o classificador disponível. Não exiba o `.env`
   em terminal compartilhado ou apresentação.
2. Abra `/analise`, use o conteúdo de `candidato-a.txt` e `vaga.txt`, confirme a
   autorização de envio e execute uma única análise com o provedor configurado.
3. Confira ML separado do perfil/contexto, habilidades, experiência, citações,
   requisitos e lacunas. A nota deve estar ausente e não deve haver perguntas.
4. Repita com `candidato-b.txt` somente se desejar e autorizar outra chamada.
   Resultado ML incorreto não deve ser substituído pelo LLM.
5. Se falhar, consulte apenas os códigos seguros. Para `llm_request_rejected`,
   confirmar suporte e aceitação do schema na conta; para limites, observar
   política/quota no console do provedor. Não desativar validação para apresentar.

O sistema está preparado localmente para esse teste; não se afirma que a chamada
real foi aprovada. Ela pode ter custo e não foi executada nesta entrega.
Ainda podem ocorrer limitações/quota, falhas de rede, truncamento ou abstenções
por citações divergentes, negação ambígua e PDFs com quebras artificiais.
O perfil só aparece com designação literal citável. Não há garantia de conclusão
em todos os currículos ou de estabilidade do serviço externo.

Nenhum modelo, métrica, credencial ou código de treinamento foi alterado.
Não houve commit ou push.
