# Português e inglês no baseline ML

## Implementação

O pré-processamento compartilhado `limpar_texto` remove links/e-mails, detecta português ou inglês e traduz entradas detectadas como português para inglês antes da limpeza lexical. A tradução usa Marian/OPUS-MT (`Helsinki-NLP/opus-mt-ROMANCE-en`) localmente. A mesma função é usada no treino e na inferência. Isto não transforma o TF-IDF em um encoder semântico multilíngue: é normalização de idioma antes do baseline inglês.

Currículo e vaga são processados separadamente antes de combinar seus textos. Requisitos também passam pela função. Não há API externa de tradução: apenas o primeiro download dos pesos exige acesso ao Hugging Face. O código não persiste textos nem traduções em cache; os pesos e arquivos de configuração são armazenados pelo Hugging Face. O backend deve continuar minimizando dados antes de chamar o ML.

O LLM recebe os textos minimizados originais; tradução nunca pode ser apresentada como citação literal do currículo. Esta mudança não permite validar automaticamente equivalências semânticas em requisitos: a verificação de evidências continua conservadora.

## Instalação e atualização obrigatória

Na raiz, com o ambiente virtual ativado:

```powershell
python -m pip install -r requirements-training.txt
python ml_language.py
python train.py
```

Pare o backend antes de publicar os modelos. Não combine este pré-processamento com modelos antigos: refaça o treino e reinicie o backend após o sucesso. Instale as mesmas dependências no ambiente de inferência. Não envie pesos ao GitHub.

Para funcionamento sem rede após baixar os pesos:

```powershell
$env:HF_HUB_OFFLINE='1'
python -m uvicorn backend.app.main:app --reload --port 8000
```

## Limites que permanecem

- O detector distingue apenas português e inglês; textos em outros idiomas não são suportados por esta integração. Documentos mistos e curtos podem ser identificados incorretamente. Termos com menos de quatro palavras não são traduzidos.
- Tradução pode alterar siglas, tecnologias, negações ou nuances. Divisão em blocos pode perder contexto entre blocos. Os textos originais devem ser revisados.
- Falha de carregamento ou tradução não recua silenciosamente para uma previsão sobre português cru.
- Processamento em CPU pode ser lento; o primeiro download e carregamento dos pesos podem demorar. O health check não comprova que a tradução foi carregada.
- Treinar/calibrar em inglês não valida automaticamente probabilidades para português traduzido. O aviso da interface permanece intencionalmente até haver avaliação específica.
- Os rótulos de matching continuam sendo os do dataset. Tradução não corrige rótulos, desbalanceamento nem as limitações da concatenação TF-IDF.

## Avaliação necessária

Reserve pares PT/PT, PT/EN, EN/PT e EN/EN revisados por humanos e que não apareçam no treino. Compare recall e F1 por classe, log loss e Brier. Compare também pares equivalentes traduzidos manualmente para medir sensibilidade ao idioma. Não reutilize os resultados do teste inglês como validação bilíngue e não ajuste o sistema para favorecer um currículo específico.

## Testes locais

```powershell
python -m pytest backend/tests/test_ml_language.py backend/tests/test_quote_recovery.py
```

Os testes de roteamento usam mocks, não avaliam a qualidade linguística do modelo. O treino, a tradução real e o frontend exigem validação integrada separada.
