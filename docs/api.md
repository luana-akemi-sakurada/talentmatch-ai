# Contrato REST

Backend local: `http://127.0.0.1:8000`. Swagger: `/docs`; contrato: `/openapi.json`.
O snapshot `docs/openapi.json` contém schemas e campos completos. Sem credenciais
de provedor no frontend. CORS restrito a origens configuradas; Vite usa proxy `/api`.

| Endpoint | Entrada / saída |
|---|---|
| GET /api/health | 200 com estado do classificador; 503 se indisponível |
| POST /api/analyze | multipart: job_description, mode, file OU resume_text |
| POST /api/compare | multipart: job_description, mode, files repetido 2–5 vezes |
| GET /api/models/metrics | Métricas lidas do CSV, seleção, metodologia e limitações |
| GET /api/models/categories | Classes do modelo; counts=null, distribuição ausente |
| GET /api/models/confusion-matrix | Imagem PNG original |

`mode`: `live` (padrão, provedor externo) ou `demo` (contexto simulado explícito).
Em ambos os modos o classificador é real. Enviar arquivo e texto juntos é erro.

## Cobertura e abstenção

`cobertura_requisitos` contém lista com IDs estáveis, referências literais,
componentes, estados, evidências, contagens, fórmula e percentual nullable.
`status=calculada` exige lista completa e todos os itens avaliados validamente.
O denominador não diminui quando o LLM omite um requisito; sem pesos.
Ver [critérios e limitações](cobertura-requisitos.md). Não é nota de aderência.

Os campos existentes permanecem. `ml.status`, `ml.coverage` e `ml.warnings` foram
acrescentados. Sem atributos TF-IDF, status é `abstained`, área `INDETERMINADA`
e top_categories é uma lista vazia, sem probabilidades inventadas.

`llm.nota_aderencia` aceita **null**. No modo ao vivo não são publicadas notas até
existir regra de pontuação validada, mesmo quando as evidências textuais forem aceitas.
`llm.abstention_reason` distingue `insufficient_evidence` e `score_not_validated`.
Null não significa zero. A resposta demo mantém seu indicador ilustrativo numérico.
`llm.ml_context_included` informa se o contexto ML foi enviado ao provedor.

O frontend e Streamlit incluídos tratam esses estados. Outros clientes precisam
aceitar nota nula e lista ML vazia. Ver [regras e limitações](confiabilidade.md).

## Limites e erros

- Arquivo PDF/TXT de até 5 MB, MIME compatível. TXT UTF-8, sem conteúdo binário.
- PDF textual com assinatura válida, sem senha, até 30 páginas. Não há OCR.
- Currículo: 1–40.000 caracteres; vaga: 1–16.000 caracteres (sem espaços isolados).
- Até 5 currículos por comparação; até 25 MB mais 100 KB de corpo total.
- JSON de erro: `{"error":{"code":"...","message":"..."}}`.
- 413: tamanho; 415: formato/MIME; 422: entrada inválida, PDF ilegível ou vazio;
  503: classificador indisponível; 404: imagem ausente; 500: falha interna segura.

## Resultado parcial é explícito

Uma classificação bem-sucedida retorna ML mesmo que o provedor falhe:

```json
{
  "candidate_id": "Candidato 1",
  "mode": "live",
  "ml": {"predicted_area": "...", "model_name": "...", "top_categories": []},
  "llm": null,
  "llm_error": "llm_unavailable",
  "warnings": ["Mensagem de indisponibilidade; revisão humana obrigatória"],
  "privacy": {"minimized": true, "stored_permanently": false}
}
```

Exemplo estrutural abreviado, não resultado real. Erros contextuais:
`llm_not_configured`, `llm_unavailable`, `invalid_llm_response`,
`unsupported_evidence`, `invalid_llm_config`, `llm_auth_error`,
`llm_permission_denied`, `llm_model_not_found`, `llm_rate_limited`,
`llm_quota_exceeded`, `llm_timeout`, `llm_connection_error`, `llm_request_rejected`
e `llm_refused`. HTTP 200 indica que o processamento
retornou seus estados, não que as duas análises produziram conclusões: o próprio ML
pode estar em abstenção por vetor vazio. Nenhum score é criado na falha.

O campo adicional `llm_diagnostic` é null quando não há diagnóstico local ou
contém somente `rule`, `field`, `source`, `category` e, para listas, `index`
(base zero). Não contém valores extraídos nem respostas do provedor. Consulte
[diagnostico-evidencias.md](diagnostico-evidencias.md) para regras, exemplo
fictício e limites da correspondência literal. Clientes existentes podem ignorá-lo.

Na comparação, `results` e `failures` mantêm os identificadores da ordem de envio;
alguns ou todos os documentos podem falhar. O frontend exibe essas falhas.

## Reexportar o contrato

Contrato final simplificado: `mode` assume `live`; `demo` precisa ser explícito.
`llm.perfil_profissional` pode ser null ou conter designação/citação verificável.
Campos de perguntas e status de entrevista foram removidos da resposta pública.
Erros de autenticação, permissão, modelo, limites/quota, timeout e conexão agora
possuem códigos distintos. Veja a tabela e o contrato do provedor em
[estabilizacao-llm.md](estabilizacao-llm.md).

Da raiz, em Python:

```python
import json
from pathlib import Path
from backend.app.main import app
Path('docs/openapi.json').write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding='utf-8')
```
