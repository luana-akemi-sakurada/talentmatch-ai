"""Treina classificadores de área e compatibilidade currículo-vaga.

Dataset: Shresth786/job-resume-matching
Arquivos esperados em data/:
- cv.csv: currículos
- job.csv: vagas
- matches.csv: pares currículo-vaga e rótulos de compatibilidade

Métodos estatísticos:
- Split estratificado por candidate_id em treino, validação e teste
- Calibração sigmoidal das probabilidades
- Detecção OOD por similaridade de cosseno a centróides TF-IDF
- Intervalo de confiança bootstrap para F1 macro e acurácia
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import normalize

from preprocess import limpar_texto

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RANDOM_STATE = 42
BOOTSTRAP_ITERATIONS = 1000

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
parser.add_argument(
    "--output-dir",
    type=Path,
    default=ROOT / "artifacts" / datetime.now().strftime("%Y%m%d-%H%M%S-%f"),
)
args = parser.parse_args()


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df


def escolher_coluna(df: pd.DataFrame, candidatos: list[str], nome: str) -> str:
    for coluna in candidatos:
        if coluna in df.columns:
            return coluna

    raise ValueError(
        f"Coluna '{nome}' não encontrada. "
        f"Colunas disponíveis: {list(df.columns)}"
    )


def bootstrap_metric(y_true, y_pred, metric_fn, iterations=BOOTSTRAP_ITERATIONS):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    rng = np.random.default_rng(RANDOM_STATE)
    valores = []

    for _ in range(iterations):
        indices = rng.integers(0, n, size=n)
        valores.append(metric_fn(y_true[indices], y_pred[indices]))

    return {
        "ponto": float(metric_fn(y_true, y_pred)),
        "ic95_inferior": float(np.percentile(valores, 2.5)),
        "ic95_superior": float(np.percentile(valores, 97.5)),
        "iteracoes": iterations,
    }


def dividir_por_candidato(df: pd.DataFrame, alvo: str):
    candidatos = df[["candidate_id", alvo]].drop_duplicates()

    treino, temporario = train_test_split(
        candidatos,
        test_size=0.30,
        stratify=candidatos[alvo],
        random_state=RANDOM_STATE,
    )

    validacao, teste = train_test_split(
        temporario,
        test_size=0.50,
        stratify=temporario[alvo],
        random_state=RANDOM_STATE,
    )

    ids_treino = set(treino["candidate_id"])
    ids_validacao = set(validacao["candidate_id"])
    ids_teste = set(teste["candidate_id"])

    return (
        df[df["candidate_id"].isin(ids_treino)].copy(),
        df[df["candidate_id"].isin(ids_validacao)].copy(),
        df[df["candidate_id"].isin(ids_teste)].copy(),
    )


args.output_dir.mkdir(parents=True, exist_ok=False)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

cv_path = args.data_dir / "cv.csv"
job_path = args.data_dir / "job.csv"
matches_path = args.data_dir / "matches.csv"

for caminho in (cv_path, job_path, matches_path):
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo obrigatório não encontrado: {caminho}. "
            "Baixe cv.csv, job.csv e matches.csv do dataset "
            "Shresth786/job-resume-matching e coloque-os em data/."
        )

cv = normalizar_colunas(pd.read_csv(cv_path))
jobs = normalizar_colunas(pd.read_csv(job_path))
matches = normalizar_colunas(pd.read_csv(matches_path))

coluna_curriculo = escolher_coluna(
    cv,
    ["resume_text", "resume", "cv_text", "text", "resume_str"],
    "texto do currículo",
)

coluna_vaga = escolher_coluna(
    jobs,
    ["job_text", "description", "job_description", "text", "description_text"],
    "texto da vaga",
)

coluna_categoria = escolher_coluna(
    jobs,
    ["category", "job_category", "role", "position", "title"],
    "categoria da vaga",
)

coluna_rotulo = escolher_coluna(
    matches,
    ["label_strength", "label", "match_label", "compatibility_label"],
    "rótulo de compatibilidade",
)

if "candidate_id" not in cv.columns or "candidate_id" not in matches.columns:
    raise ValueError("cv.csv e matches.csv devem conter candidate_id.")

if "job_id" not in jobs.columns or "job_id" not in matches.columns:
    raise ValueError("job.csv e matches.csv devem conter job_id.")

cv = cv[["candidate_id", coluna_curriculo]].dropna().drop_duplicates("candidate_id")
jobs = jobs[["job_id", coluna_vaga, coluna_categoria]].dropna().drop_duplicates("job_id")
matches = matches[["candidate_id", "job_id", coluna_rotulo]].dropna()

matches = matches.merge(
    cv.rename(columns={coluna_curriculo: "texto_curriculo"}),
    on="candidate_id",
    how="inner",
)

matches = matches.merge(
    jobs.rename(
        columns={
            coluna_vaga: "texto_vaga",
            coluna_categoria: "categoria_vaga",
        }
    ),
    on="job_id",
    how="inner",
)

matches["texto_curriculo"] = matches["texto_curriculo"].map(limpar_texto)
matches["texto_vaga"] = matches["texto_vaga"].map(limpar_texto)
matches["texto_combinado"] = (
    matches["texto_curriculo"] + " [SEP] " + matches["texto_vaga"]
)

rotulos_validos = {
    "weak_positive": "compatibilidade_fraca",
    "medium_positive": "compatibilidade_media",
    "strong_positive": "compatibilidade_forte",
}

matches["rotulo_compatibilidade"] = matches[coluna_rotulo].map(rotulos_validos)
matches = matches.dropna(subset=["rotulo_compatibilidade"])

ordem_rotulos = {
    "compatibilidade_fraca": 0,
    "compatibilidade_media": 1,
    "compatibilidade_forte": 2,
}

matches["ordem_compatibilidade"] = matches["rotulo_compatibilidade"].map(
    ordem_rotulos
)

area_por_candidato = (
    matches.sort_values(
        ["candidate_id", "ordem_compatibilidade"],
        ascending=[True, False],
    )
    .groupby("candidate_id", as_index=False)
    .first()[["candidate_id", "categoria_vaga"]]
    .rename(columns={"categoria_vaga": "area_predominante"})
)

dados_area = cv.merge(area_por_candidato, on="candidate_id", how="inner")
dados_area = dados_area.dropna(subset=["area_predominante"])

print("Distribuição das áreas predominantes:")
print(dados_area["area_predominante"].value_counts())

print("\nDistribuição dos rótulos de compatibilidade:")
print(matches["rotulo_compatibilidade"].value_counts())

treino_area, validacao_area, teste_area = dividir_por_candidato(
    dados_area,
    "area_predominante",
)

treino_match, validacao_match, teste_match = dividir_por_candidato(
    matches,
    "rotulo_compatibilidade",
)

vetorizador_area = TfidfVectorizer(
    max_features=8000,
    ngram_range=(1, 2),
    stop_words="english",
    sublinear_tf=True,
)

vetorizador_match = TfidfVectorizer(
    max_features=12000,
    ngram_range=(1, 2),
    stop_words="english",
    sublinear_tf=True,
)

modelo_area = CalibratedClassifierCV(
    estimator=Pipeline(
        [
            ("tfidf", vetorizador_area),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    C=10,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    ),
    method="sigmoid",
    cv=5,
)

modelo_compatibilidade = CalibratedClassifierCV(
    estimator=Pipeline(
        [
            ("tfidf", vetorizador_match),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    C=10,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    ),
    method="sigmoid",
    cv=5,
)

print("\nTreinando classificador de área...")
modelo_area.fit(
    treino_area["texto_curriculo"],
    treino_area["area_predominante"],
)

pred_area_validacao = modelo_area.predict(validacao_area["texto_curriculo"])
f1_area_validacao = f1_score(
    validacao_area["area_predominante"],
    pred_area_validacao,
    average="macro",
    zero_division=0,
)

print(f"F1 macro da área na validação: {f1_area_validacao:.4f}")

print("\nTreinando classificador de compatibilidade...")
modelo_compatibilidade.fit(
    treino_match["texto_combinado"],
    treino_match["rotulo_compatibilidade"],
)

pred_match_validacao = modelo_compatibilidade.predict(
    validacao_match["texto_combinado"]
)
f1_match_validacao = f1_score(
    validacao_match["rotulo_compatibilidade"],
    pred_match_validacao,
    average="macro",
    zero_division=0,
)

print(f"F1 macro da compatibilidade na validação: {f1_match_validacao:.4f}")

pred_area_teste = modelo_area.predict(teste_area["texto_curriculo"])
pred_match_teste = modelo_compatibilidade.predict(teste_match["texto_combinado"])

metricas_area = {
    "f1_macro": bootstrap_metric(
        teste_area["area_predominante"],
        pred_area_teste,
        lambda y_true, y_pred: f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
    ),
    "acuracia": bootstrap_metric(
        teste_area["area_predominante"],
        pred_area_teste,
        accuracy_score,
    ),
}

metricas_match = {
    "f1_macro": bootstrap_metric(
        teste_match["rotulo_compatibilidade"],
        pred_match_teste,
        lambda y_true, y_pred: f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        ),
    ),
    "acuracia": bootstrap_metric(
        teste_match["rotulo_compatibilidade"],
        pred_match_teste,
        accuracy_score,
    ),
}

print("\nMétricas finais no teste:")
print(f"Área — F1 macro: {metricas_area['f1_macro']['ponto']:.4f}")
print(
    f"Área — IC 95% F1 macro: "
    f"[{metricas_area['f1_macro']['ic95_inferior']:.4f}, "
    f"{metricas_area['f1_macro']['ic95_superior']:.4f}]"
)
print(f"Compatibilidade — F1 macro: {metricas_match['f1_macro']['ponto']:.4f}")
print(
    f"Compatibilidade — IC 95% F1 macro: "
    f"[{metricas_match['f1_macro']['ic95_inferior']:.4f}, "
    f"{metricas_match['f1_macro']['ic95_superior']:.4f}]"
)

vetorizador_area_treinado = modelo_area.calibrated_classifiers_[0].estimator.named_steps["tfidf"]
vetores_treino = vetorizador_area_treinado.transform(treino_area["texto_curriculo"])
vetores_treino_normalizados = normalize(vetores_treino)

classes_area = list(modelo_area.classes_)
centroides = {}

for categoria in classes_area:
    mascara = np.asarray(treino_area["area_predominante"] == categoria)

    if mascara.any():
        centroide = np.asarray(
            vetores_treino_normalizados[mascara].mean(axis=0)
        ).ravel()
        centroides[str(categoria)] = centroide.tolist()

vetores_validacao = vetorizador_area_treinado.transform(
    validacao_area["texto_curriculo"]
)
vetores_validacao_normalizados = normalize(vetores_validacao)
matriz_centroides = np.vstack(
    [centroides[categoria] for categoria in classes_area]
)
similaridades_validacao = np.max(
    vetores_validacao_normalizados @ matriz_centroides.T,
    axis=1,
)
limiar_ood = float(np.percentile(similaridades_validacao, 5))

metadata_area = {
    "classes": classes_area,
    "class_centroids": centroides,
    "ood_threshold": limiar_ood,
    "ood_threshold_definition": (
        "5º percentil da similaridade máxima ao centróide no conjunto de validação"
    ),
    "calibration": {
        "method": "sigmoid",
        "cross_validation_folds": 5,
    },
    "data_split": {
        "estrategia": "split_por_candidate_id",
        "treino": int(len(treino_area)),
        "validacao": int(len(validacao_area)),
        "teste": int(len(teste_area)),
        "random_state": RANDOM_STATE,
    },
    "test_metrics": metricas_area,
}

metadata_match = {
    "classes": list(modelo_compatibilidade.classes_),
    "calibration": {
        "method": "sigmoid",
        "cross_validation_folds": 5,
    },
    "data_split": {
        "estrategia": "split_por_candidate_id",
        "treino": int(len(treino_match)),
        "validacao": int(len(validacao_match)),
        "teste": int(len(teste_match)),
        "random_state": RANDOM_STATE,
    },
    "test_metrics": metricas_match,
}

joblib.dump(modelo_area, MODELS_DIR / "classificador_area.joblib")
joblib.dump(metadata_area, MODELS_DIR / "ml_metadata_area.joblib")
joblib.dump(
    modelo_compatibilidade,
    MODELS_DIR / "classificador_compatibilidade.joblib",
)
joblib.dump(
    metadata_match,
    MODELS_DIR / "ml_metadata_compatibilidade.joblib",
)

joblib.dump(modelo_area, args.output_dir / "classificador_area.joblib")
joblib.dump(metadata_area, args.output_dir / "ml_metadata_area.joblib")
joblib.dump(
    modelo_compatibilidade,
    args.output_dir / "classificador_compatibilidade.joblib",
)
joblib.dump(
    metadata_match,
    args.output_dir / "ml_metadata_compatibilidade.joblib",
)

relatorio_area = classification_report(
    teste_area["area_predominante"],
    pred_area_teste,
    output_dict=True,
    zero_division=0,
)

relatorio_match = classification_report(
    teste_match["rotulo_compatibilidade"],
    pred_match_teste,
    output_dict=True,
    zero_division=0,
)

(args.output_dir / "relatorio_area.json").write_text(
    json.dumps(relatorio_area, indent=2),
    encoding="utf-8",
)

(args.output_dir / "relatorio_compatibilidade.json").write_text(
    json.dumps(relatorio_match, indent=2),
    encoding="utf-8",
)

(args.output_dir / "metricas_bootstrap.json").write_text(
    json.dumps(
        {
            "area": metricas_area,
            "compatibilidade": metricas_match,
        },
        indent=2,
    ),
    encoding="utf-8",
)

(args.output_dir / "dataset_summary.json").write_text(
    json.dumps(
        {
            "dataset": "Shresth786/job-resume-matching",
            "candidatos": int(cv["candidate_id"].nunique()),
            "vagas": int(jobs["job_id"].nunique()),
            "pares": int(len(matches)),
            "area_treino": int(len(treino_area)),
            "area_validacao": int(len(validacao_area)),
            "area_teste": int(len(teste_area)),
            "match_treino": int(len(treino_match)),
            "match_validacao": int(len(validacao_match)),
            "match_teste": int(len(teste_match)),
            "limiar_ood": limiar_ood,
            "limitacao": (
                "A detecção OOD usa similaridade lexical TF-IDF e identifica "
                "distância estatística em relação aos dados de treino; não mede "
                "qualidade semântica do currículo."
            ),
        },
        indent=2,
    ),
    encoding="utf-8",
)

print(f"\nModelos finais salvos automaticamente em: {MODELS_DIR}")
print(f"Artefatos de auditoria salvos em: {args.output_dir}")
