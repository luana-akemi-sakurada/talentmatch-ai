# Dataset, experimentos e reprodução

Dataset original: [Resume Dataset / snehaanbhawal](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset).
Colunas `Resume_str` ou `Resume`, com `Category`. O CSV não está nesta cópia.

O pipeline remove nulos e duplicatas, converte texto para minúsculas, remove URLs,
e-mails e caracteres, preservando alguns símbolos técnicos. Usa TF-IDF com até
8.000 atributos, unigramas/bigramas, stop words em inglês e frequência sublinear.
Split estratificado: 80% treino / 20% teste; random_state=42.

| Modelo | Configuração principal | Acurácia original | F1 macro original |
|---|---|---:|---:|
| Regressão logística | max_iter=2000, C=10 | 0,6861 | 0,6393 |
| Random Forest | 300 árvores, random_state=42 | 0,7505 | 0,6896 |
| MLP | camadas 256/64, early stopping | 0,6157 | 0,5610 |

Selecionado: Random Forest por maior F1 macro, confirmado pelo tipo do classificador
carregado. São 24 categorias. Nenhum retreinamento foi executado na evolução 2.0.
As probabilidades são saídas do classificador, sem estudo de calibração disponível.

Precision, recall, distribuição por classe, contagens de treino/teste e matriz
numérica não foram preservados no experimento original. A imagem PNG está disponível.
A interface apresenta essas lacunas, sem preencher com valores artificiais.

## Limitação metodológica

O mesmo teste foi usado para selecionar e relatar o melhor modelo. A estimativa
não equivale a avaliação independente após seleção. A divisão reproduzível não
elimina essa limitação. Desempenho em português e justiça entre grupos não foram
medidos. O indicador de aderência do LLM não foi validado por essas métricas.

## Nova execução opcional, preservando o original

Baixe o dataset separadamente e coloque em `data/Resume.csv`. Instale também
matplotlib e seaborn (incluídos em `requirements.txt` da raiz). Execute:

```powershell
.\.venv\Scripts\python.exe train.py --output-dir artifacts/novo-experimento
```

O diretório deve ser novo. `models/` é rejeitado como destino para proteger o
original. A nova execução mantém os três algoritmos e exporta:

- pipeline, CSV com acurácia/F1/precision/recall macro e imagem da matriz;
- `matriz_confusao.json`, `relatorio_classificacao.json` e `dataset_summary.json`.

Os novos artefatos não substituem automaticamente os exibidos no dashboard. Uma
troca futura exige revisão conjunta do modelo e suas métricas. Contagens do dataset
são agregadas; não são exportados currículos no relatório de treinamento.

## Integridade dos originais (SHA-256)

```text
classificador.joblib    6EAB51BF59878BE2C57F158581F1247580B05E33A98EB973075CF3A8B2AE6294
comparacao_modelos.csv  DAA5B064887386F4256A0514609968237B8CEFDA54339507818A97BE6E127566
matriz_confusao.png     C8B8C5AA62C1909BE9634029F9647465A8C35D9A4F0E061FEFDF6B98B5EFD37C
```
