# TalentMatch AI

Sistema de apoio à análise de currículos para processos de recrutamento.

O projeto combina Machine Learning e LLM:

- O **ML** classifica a área predominante do currículo, estima a compatibilidade entre currículo e vaga, calcula incerteza estatística e prioriza requisitos por similaridade TF-IDF.
- O **LLM** interpreta o contexto, extrai habilidades e valida requisitos apenas com evidências literais do currículo.
- O sistema não recomenda contratação, rejeição nem ranking automático de candidatos.

## Dataset

O projeto usa o dataset público **[Shresth786/job-resume-matching](https://huggingface.co/datasets/Shresth786/job-resume-matching)**.

Baixe os três arquivos e coloque-os em `data/`:

```text
data/
├── cv.csv
├── job.csv
└── matches.csv
```

## Treinamento

```powershell
python train.py --data-dir data
```

O script salva automaticamente em `models/`:

```text
models/
├── classificador_area.joblib
├── ml_metadata_area.joblib
├── classificador_compatibilidade.joblib
├── ml_metadata_compatibilidade.joblib
└── evaluation.json
```

## Execução

1. Copie `.env.example` para `.env` e preencha `LLM_API_KEY` (o exemplo usa o Groq, que é gratuito).
2. Back-end (na raiz do projeto, com o ambiente virtual ativado):

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

3. Front-end (em outro terminal):

```powershell
cd frontend
npm install
npm run dev
```

4. Abra http://localhost:5173. Para testar a conexão com o LLM: `python scripts/testar_llm.py`.

## Ética

O ML fornece sinais quantitativos de apoio. O LLM não pode usá-los como prova de competência nem transformá-los em decisão automática. Toda conclusão deve estar ancorada em evidências literais do currículo e a decisão final permanece humana.
