"""Treina e compara modelos de ML para classificar a area do curriculo.
Dataset: Kaggle 'Resume Dataset' (snehaanbhawal/resume-dataset) -> data/Resume.csv
Colunas: Resume_str, Category (ou Resume, Category)."""
import argparse, json
from datetime import datetime
from pathlib import Path
import pandas as pd, joblib, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix
from preprocess import limpar_texto

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data', type=Path, default=ROOT / 'data/Resume.csv')
parser.add_argument('--output-dir', type=Path, default=ROOT / 'artifacts' / datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
args = parser.parse_args()
if args.output_dir.resolve() == (ROOT / 'models').resolve():
    parser.error('Use outro diretório para preservar os experimentos originais em models/.')
df = pd.read_csv(args.data)
args.output_dir.mkdir(parents=True, exist_ok=False)
col = "Resume_str" if "Resume_str" in df.columns else "Resume"
df = df[[col, "Category"]].dropna().drop_duplicates()          # limpeza (Aula 02)
df["texto"] = df[col].map(limpar_texto)
print(df["Category"].value_counts())

Xtr, Xte, ytr, yte = train_test_split(df["texto"], df["Category"], test_size=0.2,
                                      stratify=df["Category"], random_state=42)
tfidf = lambda: TfidfVectorizer(max_features=8000, ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
modelos = {
    "LogisticRegression": LogisticRegression(max_iter=2000, C=10),
    "RandomForest": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
    "MLP (Perceptron multicamada)": MLPClassifier(hidden_layer_sizes=(256, 64), early_stopping=True, max_iter=200, random_state=42),
}
res, melhor, melhor_f1 = [], None, -1
for nome, clf in modelos.items():
    pipe = Pipeline([("tfidf", tfidf()), ("clf", clf)]).fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    acc, f1 = accuracy_score(yte, pred), f1_score(yte, pred, average="macro")
    res.append({"modelo": nome, "acuracia": round(acc, 4), "f1_macro": round(f1, 4),
                "precision_macro": round(precision_score(yte, pred, average='macro', zero_division=0), 4),
                "recall_macro": round(recall_score(yte, pred, average='macro', zero_division=0), 4)})
    print(nome, acc, f1)
    if f1 > melhor_f1: melhor, melhor_f1, melhor_nome, melhor_pred = pipe, f1, nome, pred

pd.DataFrame(res).to_csv(args.output_dir / 'comparacao_modelos.csv', index=False)
print("\nMELHOR:", melhor_nome); print(classification_report(yte, melhor_pred))
labels = sorted(df["Category"].unique())
plt.figure(figsize=(12, 10))
sns.heatmap(confusion_matrix(yte, melhor_pred, labels=labels), xticklabels=labels, yticklabels=labels, cmap="Blues")
plt.title(f"Matriz de confusao - {melhor_nome}"); plt.tight_layout(); plt.savefig(args.output_dir / 'matriz_confusao.png', dpi=150)
joblib.dump(melhor, args.output_dir / 'classificador.joblib')
(args.output_dir / 'matriz_confusao.json').write_text(json.dumps({'labels': labels, 'matrix': confusion_matrix(yte, melhor_pred, labels=labels).tolist()}, indent=2), encoding='utf-8')
(args.output_dir / 'relatorio_classificacao.json').write_text(json.dumps(classification_report(yte, melhor_pred, output_dict=True, zero_division=0), indent=2), encoding='utf-8')
(args.output_dir / 'dataset_summary.json').write_text(json.dumps({
    'total_after_cleaning': len(df), 'train_count': len(Xtr), 'test_count': len(Xte),
    'category_counts': {str(k): int(v) for k, v in df['Category'].value_counts().items()},
    'random_state': 42, 'test_fraction': .2, 'stratified': True, 'selected_model': melhor_nome,
    'limitation': 'Model selection and reporting share the same test set.'}, indent=2), encoding='utf-8')
print('Artefatos desta execução:', args.output_dir)
