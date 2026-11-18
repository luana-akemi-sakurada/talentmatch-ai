"""Treino auditavel. Requer scikit-learn >= 1.6 (FrozenEstimator).
Execute: python train.py --data-dir data
A interface antiga de metricas deve ser migrada para evaluation.json.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, log_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import normalize
from preprocess import limpar_texto

ROOT = Path(__file__).resolve().parent
SEED = 42
LABELS = {'weak_positive': 'compatibilidade_fraca', 'medium_positive': 'compatibilidade_media', 'strong_positive': 'compatibilidade_forte'}


def column(df, choices):
    for name in choices:
        if name in df:
            return name
    raise ValueError(f'Colunas esperadas: {choices}; recebidas: {list(df.columns)}')


def read(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
    return df


def split_groups(df):
    ids = sorted(df['group'].unique())
    train, rest = train_test_split(ids, test_size=.40, random_state=SEED)
    cal, rest = train_test_split(rest, test_size=.625, random_state=SEED)
    val, test = train_test_split(rest, test_size=.60, random_state=SEED)
    groups = dict(train=set(train), calibration=set(cal), validation=set(val), test=set(test))
    names = list(groups)
    for i, name in enumerate(names):
        for other in names[i + 1:]:
            if groups[name] & groups[other]:
                raise ValueError('Vazamento entre conjuntos.')
    return groups


def scores(matrix):
    matrix = np.asarray(matrix, dtype=float)
    tp = np.diag(matrix)
    denom = matrix.sum(axis=0) + matrix.sum(axis=1)
    f1 = np.divide(2 * tp, denom, out=np.zeros_like(tp), where=denom > 0)
    return np.array([tp.sum() / matrix.sum(), f1.mean()])


def evaluate(model, base, frame, classes, iterations):
    y = frame['target'].to_numpy()
    p = model.predict_proba(frame['text'])
    pred = model.classes_[p.argmax(axis=1)]
    matrix = confusion_matrix(y, pred, labels=classes)
    lookup = {c: i for i, c in enumerate(classes)}
    yt = np.array([lookup[c] for c in y])
    yp = np.array([lookup[c] for c in pred])
    group_codes, unique = pd.factorize(frame['group'])
    k = len(classes)
    counts = np.zeros((len(unique), k * k), dtype=np.int64)
    np.add.at(counts, (group_codes, yt * k + yp), 1)
    rng = np.random.default_rng(SEED)
    sampled = np.empty((iterations, 2))
    for i in range(iterations):
        selected = rng.integers(0, len(unique), size=len(unique))
        sampled[i] = scores(counts[selected].sum(axis=0).reshape(k, k))
    point = scores(matrix)
    intervals = {}
    for i, name in enumerate(['accuracy', 'f1_macro']):
        low, high = np.percentile(sampled[:, i], [2.5, 97.5])
        intervals[name] = {'point': float(point[i]), 'low': float(low), 'high': float(high)}
    onehot = (y[:, None] == np.asarray(classes)[None, :]).astype(float)
    def probability_metrics(prob):
        return {'log_loss': float(log_loss(y, prob, labels=classes)), 'multiclass_brier': float(np.mean(np.sum((prob - onehot) ** 2, axis=1)))}
    return {'metrics': intervals, 'bootstrap': {'method': 'percentile_cluster_resume', 'iterations': iterations, 'confidence': .95, 'scope': 'Modelo fixo; nao inclui variacao do retreino; vagas podem ser compartilhadas.'}, 'probability_quality': {'uncalibrated': probability_metrics(base.predict_proba(frame['text'])), 'calibrated': probability_metrics(p)}, 'classification_report': classification_report(y, pred, labels=classes, output_dict=True, zero_division=0), 'confusion_matrix': {'labels': list(classes), 'counts': matrix.tolist()}}


def fit_task(frame, groups, features, iterations):
    parts = {name: frame[frame['group'].isin(ids)].copy() for name, ids in groups.items()}
    classes = sorted(frame['target'].unique())
    if len(classes) < 2:
        raise ValueError('A tarefa precisa de pelo menos duas classes.')
    for name, part in parts.items():
        if set(part['target']) != set(classes):
            raise ValueError(f'{name}: falta uma classe. Reavalie o tamanho dos conjuntos, sem escolher seed usando resultados de teste.')
    base = Pipeline([('tfidf', TfidfVectorizer(max_features=features, ngram_range=(1, 2), stop_words='english', sublinear_tf=True)), ('clf', LogisticRegression(C=1, max_iter=2000, random_state=SEED))])
    base.fit(parts['train']['text'], parts['train']['target'])
    calibrated = CalibratedClassifierCV(FrozenEstimator(base), method='sigmoid')
    calibrated.fit(parts['calibration']['text'], parts['calibration']['target'])
    report = {'classes': classes, 'model': 'TF-IDF + LogisticRegression + sigmoid holdout', 'splits': {name: {'rows': len(part), 'resume_groups': int(part['group'].nunique()), 'candidates': int(part['candidate_id'].nunique()), 'class_counts': {str(c): int(n) for c, n in part['target'].value_counts().items()}} for name, part in parts.items()}, 'evaluation': evaluate(calibrated, base, parts['test'], classes, iterations)}
    return calibrated, base, parts, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--output-dir', type=Path, default=None)
    parser.add_argument('--bootstrap', type=int, default=1000)
    args = parser.parse_args()
    if args.bootstrap < 100:
        parser.error('--bootstrap deve ser pelo menos 100.')
    cv, jobs, pairs = [read(args.data_dir / name) for name in ['cv.csv', 'job.csv', 'matches.csv']]
    resume_col = column(cv, ['resume_text', 'resume', 'cv_text', 'text', 'resume_str'])
    job_col = column(jobs, ['job_text', 'description', 'job_description', 'text', 'description_text'])
    category_col = column(jobs, ['category', 'job_category'])
    label_col = column(pairs, ['label_strength'])
    cv = cv[['candidate_id', resume_col]].dropna().rename(columns={resume_col: 'resume'})
    jobs = jobs[['job_id', job_col, category_col]].dropna().rename(columns={job_col: 'job', category_col: 'category'})
    if cv['candidate_id'].duplicated().any() or jobs['job_id'].duplicated().any():
        raise ValueError('IDs duplicados: resolva os registros antes do treino.')
    cv['resume'] = cv['resume'].map(limpar_texto)
    jobs['job'] = jobs['job'].map(limpar_texto)
    cv = cv[cv['resume'].str.strip().ne('')].copy()
    jobs = jobs[jobs['job'].str.strip().ne('')].copy()
    cv['group'] = cv['resume'].map(lambda text: hashlib.sha256(text.encode()).hexdigest())
    pairs = pairs[['candidate_id', 'job_id', label_col]].dropna().copy()
    pairs['target'] = pairs[label_col].map(LABELS)
    if pairs['target'].isna().any():
        raise ValueError('Rotulo nao reconhecido; nao sera descartado silenciosamente.')
    if pairs.groupby(['candidate_id', 'job_id'])['target'].nunique().gt(1).any():
        raise ValueError('Rotulos conflitantes para o mesmo par.')
    pairs = pairs.drop_duplicates(['candidate_id', 'job_id'])
    pairs = pairs.merge(cv, on='candidate_id', validate='many_to_one').merge(jobs, on='job_id', validate='many_to_one')
    if pairs.empty:
        raise ValueError('Nenhum par valido apos os joins.')
    groups = split_groups(cv[cv['candidate_id'].isin(pairs['candidate_id'])])
    rank = {'compatibilidade_fraca': 0, 'compatibilidade_media': 1, 'compatibilidade_forte': 2}
    pairs['rank'] = pairs['target'].map(rank)
    best = pairs[pairs['rank'].eq(pairs.groupby('candidate_id')['rank'].transform('max'))]
    categories_per_candidate = best.groupby('candidate_id')['category'].agg(lambda values: sorted(set(values)))
    unambiguous = categories_per_candidate[categories_per_candidate.map(len).eq(1)].map(lambda values: values[0])
    area = cv.merge(unambiguous.rename('target'), on='candidate_id', validate='one_to_one')
    area['text'] = area['resume']
    pairs['text'] = pairs['resume'] + ' [SEP] ' + pairs['job']
    print('Treinando area derivada...', flush=True)
    area_model, area_base, area_parts, area_report = fit_task(area, groups, 8000, args.bootstrap)
    print('Treinando matching...', flush=True)
    match_model, _, _, match_report = fit_task(pairs, groups, 12000, args.bootstrap)
    vectorizer = area_base.named_steps['tfidf']
    x = normalize(vectorizer.transform(area_parts['train']['text']))
    centroid_matrix = np.vstack([np.asarray(x[area_parts['train']['target'].eq(c).to_numpy()].mean(axis=0)).ravel() for c in area_model.classes_])
    centroid_matrix = normalize(centroid_matrix)
    val = normalize(vectorizer.transform(area_parts['validation']['text']))
    threshold = float(np.percentile(np.asarray(val @ centroid_matrix.T).max(axis=1), 5))
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    limitations = ['Rotulos de compatibilidade sao os do dataset; origem e validacao humana nao verificadas.', 'Area e rotulo derivado das vagas de maior nivel de match; empates entre categorias foram excluidos.', 'Vagas podem ocorrer em mais de um conjunto: teste avalia novos curriculos, nao necessariamente novas vagas.', 'Textos identicos apos limpeza ficam juntos; duplicatas aproximadas nao sao detectadas.', 'Ingles; generalizacao para portugues nao validada.', 'Classes apenas weak/medium/strong positive; nao estima rejeicao ou chance de contratacao.', 'Calibracao nao garante confiabilidade fora da distribuicao. Compare log loss e Brier.', 'OOD: percentil empirico da validacao, sem avaliacao com corpus externo OOD.', 'Bootstrap condicional ao modelo fixo, agrupado por curriculo. Nao inclui incerteza de retreino.', 'Matching baseline concatena textos; desempenho nao demonstra compreensao semantica.']
    report = {'schema_version': 2, 'run_id': run_id, 'dataset': 'Shresth786/job-resume-matching', 'sklearn_version': sklearn.__version__, 'seed': SEED, 'split_strategy': 'Hashes de curriculos limpos disjuntos; 60/15/10/15 aproximados para treino/calibracao/validacao/teste.', 'label_provenance': 'not_verified', 'area_candidates_excluded_ambiguous': int(len(categories_per_candidate) - len(unambiguous)), 'tasks': {'area': area_report, 'compatibility': match_report}, 'limitations': limitations}
    metadata_area = {'run_id': run_id, 'classes': list(area_model.classes_), 'class_centroids': {str(c): row.tolist() for c, row in zip(area_model.classes_, centroid_matrix)}, 'ood_threshold': threshold, 'ood_validated': False, 'data_split': area_report['splits'], 'test_metrics': area_report['evaluation']}
    metadata_match = {'run_id': run_id, 'classes': list(match_model.classes_), 'data_split': match_report['splits'], 'test_metrics': match_report['evaluation']}
    output = args.output_dir or ROOT / 'artifacts' / run_id
    output.mkdir(parents=True, exist_ok=False)
    artifacts = {'classificador_area.joblib': area_model, 'ml_metadata_area.joblib': metadata_area, 'classificador_compatibilidade.joblib': match_model, 'ml_metadata_compatibilidade.joblib': metadata_match}
    for name, value in artifacts.items():
        joblib.dump(value, output / name)
    (output / 'evaluation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    models = ROOT / 'models'
    models.mkdir(exist_ok=True)
    for name in artifacts:
        temp = models / (name + '.tmp')
        temp.write_bytes((output / name).read_bytes())
        temp.replace(models / name)
    temp = models / 'evaluation.json.tmp'
    temp.write_bytes((output / 'evaluation.json').read_bytes())
    temp.replace(models / 'evaluation.json')
    print(f'Concluido: {output}. Modelos publicados em {models}. Reinicie o backend.')


if __name__ == '__main__':
    main()
