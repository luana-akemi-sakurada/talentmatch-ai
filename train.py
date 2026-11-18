"""Treino auditavel. Requer scikit-learn >= 1.6 (FrozenEstimator).
Execute: python train.py --data-dir data

Duas tarefas:
  * area: classifica a area derivada do curriculo (TF-IDF + regressao logistica calibrada).
  * compatibility: estima o SCORE de matching curriculo-vaga a partir de features de relacao
    (similaridade, habilidades em comum, area, cargo, anos, formacao) e converte o score nas
    faixas do dataset (fraca < 0,58 <= media < 0,68 <= forte).

Avaliacao do matching com curriculos E vagas disjuntos entre treino, calibracao, validacao e teste.
Isso reproduz o uso real (curriculo e vaga que o modelo nunca viu). O protocolo anterior separava
so curriculos e as mesmas vagas apareciam no treino e no teste, o que inflava as metricas.

Os textos do dataset estao em ingles: a traducao PT->EN so e aplicada na inferencia. Use
--detect-language para rodar a deteccao de idioma tambem no treino.
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
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.frozen import FrozenEstimator
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, log_loss
from sklearn.model_selection import cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import normalize

import matching_features as mf
import preprocess
from preprocess import limpar_texto

ROOT = Path(__file__).resolve().parent
SEED = 42
RANK = {'weak_positive': 0, 'medium_positive': 1, 'strong_positive': 2}


def column(df, choices):
    for name in choices:
        if name in df:
            return name
    raise ValueError(f'Colunas esperadas: {choices}; recebidas: {list(df.columns)}')


def read(path, drop=('embedding',)):
    df = pd.read_csv(path, usecols=lambda c: c.strip().lower() not in drop)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
    return df


def split_groups(df):
    ids = sorted(df['group'].unique())
    train, rest = train_test_split(ids, test_size=.40, random_state=SEED)
    cal, rest = train_test_split(rest, test_size=.625, random_state=SEED)
    val, test = train_test_split(rest, test_size=.60, random_state=SEED)
    groups = dict(train=set(train), calibration=set(cal), validation=set(val), test=set(test))
    check_disjoint(groups)
    return groups


def split_jobs(job_ids):
    ids = sorted(job_ids)
    train, rest = train_test_split(ids, test_size=.40, random_state=SEED)
    cal, rest = train_test_split(rest, test_size=.60, random_state=SEED)
    val, test = train_test_split(rest, test_size=.50, random_state=SEED)
    groups = dict(train=set(train), calibration=set(cal), validation=set(val), test=set(test))
    check_disjoint(groups)
    return groups


def check_disjoint(groups):
    names = list(groups)
    for i, name in enumerate(names):
        for other in names[i + 1:]:
            if groups[name] & groups[other]:
                raise ValueError('Vazamento entre conjuntos.')


def scores(matrix):
    matrix = np.asarray(matrix, dtype=float)
    tp = np.diag(matrix)
    denom = matrix.sum(axis=0) + matrix.sum(axis=1)
    f1 = np.divide(2 * tp, denom, out=np.zeros_like(tp), where=denom > 0)
    return np.array([tp.sum() / matrix.sum(), f1.mean()])


def text_pipeline(features, C=1):
    return Pipeline([('tfidf', TfidfVectorizer(max_features=features, ngram_range=(1, 2), stop_words='english', sublinear_tf=True)),
                     ('clf', LogisticRegression(C=C, max_iter=2000, random_state=SEED))])


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
    return {'metrics': intervals, 'bootstrap': {'method': 'percentile_cluster_resume', 'iterations': iterations, 'confidence': .95, 'scope': 'Modelo fixo; nao inclui variacao do retreino.'},
            'probability_quality': {'uncalibrated': probability_metrics(base.predict_proba(frame['text'])), 'calibrated': probability_metrics(p)},
            'classification_report': classification_report(y, pred, labels=classes, output_dict=True, zero_division=0),
            'confusion_matrix': {'labels': list(classes), 'counts': matrix.tolist()}}


def fit_area(frame, groups, iterations):
    parts = {name: frame[frame['group'].isin(ids)].copy() for name, ids in groups.items()}
    classes = sorted(frame['target'].unique())
    for name, part in parts.items():
        if set(part['target']) != set(classes):
            raise ValueError(f'{name}: falta uma classe. Reavalie o tamanho dos conjuntos, sem escolher seed usando resultados de teste.')
    base = text_pipeline(8000)
    base.fit(parts['train']['text'], parts['train']['target'])
    calibrated = CalibratedClassifierCV(FrozenEstimator(base), method='sigmoid')
    calibrated.fit(parts['calibration']['text'], parts['calibration']['target'])
    report = {'classes': classes, 'model': 'TF-IDF + LogisticRegression + sigmoid holdout',
              'splits': {name: {'rows': len(part), 'resume_groups': int(part['group'].nunique()), 'candidates': int(part['candidate_id'].nunique()), 'class_counts': {str(c): int(n) for c, n in part['target'].value_counts().items()}} for name, part in parts.items()},
              'evaluation': evaluate(calibrated, base, parts['test'], classes, iterations)}
    return calibrated, base, parts, report


# ----------------------------------------------------------------------------- matching

def cluster_metrics(y, pred_score, jobs, iterations):
    """Metricas com IC bootstrap agrupado por VAGA (o agrupamento mais conservador)."""
    lab = np.digitize(y, mf.THRESHOLDS)
    plab = np.digitize(pred_score, mf.THRESHOLDS)
    codes, unique = pd.factorize(jobs)
    k = 3
    conf = np.zeros((len(unique), k * k))
    np.add.at(conf, (codes, lab * k + plab), 1)
    n = np.bincount(codes).astype(float)
    sy = np.bincount(codes, weights=y)
    syy = np.bincount(codes, weights=y * y)
    se = np.bincount(codes, weights=(y - pred_score) ** 2)
    sa = np.bincount(codes, weights=np.abs(y - pred_score))

    def compute(sel):
        N = n[sel].sum()
        ss_tot = syy[sel].sum() - sy[sel].sum() ** 2 / N
        acc, f1 = scores(conf[sel].sum(axis=0).reshape(k, k))
        return np.array([acc, f1, 1 - se[sel].sum() / ss_tot, sa[sel].sum() / N])
    point = compute(np.arange(len(unique)))
    rng = np.random.default_rng(SEED)
    sampled = np.array([compute(rng.integers(0, len(unique), len(unique))) for _ in range(iterations)])
    out = {}
    for i, name in enumerate(['accuracy', 'f1_macro', 'r2', 'mae']):
        low, high = np.percentile(sampled[:, i], [2.5, 97.5])
        out[name] = {'point': float(point[i]), 'low': float(low), 'high': float(high)}
    return out, conf.sum(axis=0).reshape(k, k)


def matching_task(cv, jobs, pairs, resume_groups, area_base, area_labels, iterations):
    names = list(mf.CLASS_NAMES)
    job_groups = split_jobs(jobs['job_id'])
    split_names = ['train', 'calibration', 'validation', 'test']
    res_split = {s: cv['group'].isin(resume_groups[s]).to_numpy() for s in split_names}
    job_split = {s: jobs['job_id'].isin(job_groups[s]).to_numpy() for s in split_names}
    cv_index = {c: i for i, c in enumerate(cv['candidate_id'])}
    job_index = {j: i for i, j in enumerate(jobs['job_id'])}
    ri = pairs['candidate_id'].map(cv_index).to_numpy()
    ji = pairs['job_id'].map(job_index).to_numpy()
    masks = {s: res_split[s][ri] & job_split[s][ji] for s in split_names}
    y = pairs['final_score'].to_numpy(float)
    for s, mask in masks.items():
        if mask.sum() < 500:
            raise ValueError(f'{s}: poucos pares ({int(mask.sum())}) para avaliar.')

    train_res = cv[res_split['train']]
    train_jobs = jobs[job_split['train']]
    corpus = pd.concat([train_res['resume'], train_jobs['job']])
    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words='english', sublinear_tf=True, min_df=2).fit(corpus)
    svd = TruncatedSVD(64, random_state=SEED).fit(vectorizer.transform(corpus))
    vocabulary = mf.build_skill_vocabulary([train_res['clean_skills'], train_jobs['clean_skills']])

    # Area da VAGA: classificador proprio (treino so com vagas de treino).
    job_pipe = text_pipeline(8000, C=5)
    job_area = clone(job_pipe).fit(train_jobs['job'], train_jobs['category'])
    if list(job_area.classes_) != list(area_base.classes_):
        raise ValueError('Classes de area de curriculos e vagas diferem.')
    job_probs = job_area.predict_proba(jobs['job'])
    job_probs[job_split['train']] = cross_val_predict(clone(job_pipe), train_jobs['job'], train_jobs['category'], cv=5, method='predict_proba')
    job_acc = {s: float((job_area.predict(jobs.loc[job_split[s], 'job']) == jobs.loc[job_split[s], 'category']).mean()) for s in split_names[1:]}

    # Area do CURRICULO: probabilidades fora-da-amostra para quem treinou o modelo de area.
    resume_probs = area_base.predict_proba(cv['resume'])
    in_area_train = cv['candidate_id'].isin(area_labels.index).to_numpy() & res_split['train']
    labelled = cv[in_area_train]
    resume_probs[in_area_train] = cross_val_predict(clone(area_base), labelled['resume'], labelled['candidate_id'].map(area_labels), cv=5, method='predict_proba')

    featurizer = mf.MatchFeaturizer(vectorizer, svd, vocabulary, area_base, job_area)
    R = featurizer.resume_docs(cv['resume'].tolist(), cv['raw'].tolist(), years=cv['years_experience'].to_numpy(float), area=resume_probs)
    J = featurizer.job_docs(jobs['job'].tolist(), jobs['raw'].tolist(), years=jobs['years_required'].to_numpy(float), area=job_probs)
    X = featurizer.pair_matrix(R, J, ri, ji, title_dropout=.15, seed=SEED)

    # Numero de iteracoes escolhido na validacao (nunca no teste).
    gb = HistGradientBoostingRegressor(max_iter=500, learning_rate=.05, min_samples_leaf=40, l2_regularization=1.0, random_state=SEED)
    gb.fit(X[masks['train']], y[masks['train']])
    val_err = [np.mean(np.abs(p - y[masks['validation']])) for p in gb.staged_predict(X[masks['validation']])]
    best = int(np.argmin(val_err)) + 1
    regressor = HistGradientBoostingRegressor(max_iter=best, learning_rate=.05, min_samples_leaf=40, l2_regularization=1.0, random_state=SEED)
    regressor.fit(X[masks['train']], y[masks['train']])
    residuals = y[masks['calibration']] - regressor.predict(X[masks['calibration']])
    medians = np.nan_to_num(np.nanmedian(X[masks['train']], axis=0), nan=0.0)
    model = mf.MatchModel(featurizer, regressor, residuals, medians)

    test = masks['test']
    p_test = regressor.predict(X[test])
    probs = model.class_probabilities(p_test)
    y_class = np.digitize(y[test], mf.THRESHOLDS)
    pred_class = probs.argmax(axis=1)
    metrics, matrix = cluster_metrics(y[test], p_test, pairs['job_id'].to_numpy()[test], iterations)
    onehot = np.eye(3)[y_class]
    label_names = np.array(names)
    safe = np.clip(probs, 1e-6, 1)
    safe = safe / safe.sum(axis=1, keepdims=True)
    quality = {'log_loss': float(log_loss(y_class, safe, labels=[0, 1, 2])), 'multiclass_brier': float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))}
    low, high = model.interval(0, .8)
    coverage = float(np.mean((y[test] >= p_test + low) & (y[test] <= p_test + high)))

    # Linhas de base sob o MESMO protocolo (curriculo e vaga inedito).
    majority = int(np.bincount(np.digitize(y[masks['train']], mf.THRESHOLDS)).argmax())
    maj_acc = float(np.mean(y_class == majority))
    maj_f1 = float(scores(confusion_matrix(y_class, np.full_like(y_class, majority), labels=[0, 1, 2]))[1])
    concat_train = (pairs.loc[masks['train'], 'resume'] + ' [SEP] ' + pairs.loc[masks['train'], 'job'])
    concat = text_pipeline(12000).fit(concat_train, np.digitize(y[masks['train']], mf.THRESHOLDS))
    concat_pred = concat.predict(pairs.loc[test, 'resume'] + ' [SEP] ' + pairs.loc[test, 'job'])
    concat_matrix = confusion_matrix(y_class, concat_pred, labels=[0, 1, 2])
    baselines = {
        'classe_majoritaria': {'accuracy': maj_acc, 'f1_macro': maj_f1},
        'tfidf_concatenado_logistica': {'accuracy': float(scores(concat_matrix)[0]), 'f1_macro': float(scores(concat_matrix)[1]),
                                        'descricao': 'Modelo anterior (curriculo + vaga concatenados), reavaliado com vagas inéditas.'},
    }
    importance = permutation_importance(regressor, X[masks['validation']], y[masks['validation']], n_repeats=5, random_state=SEED)
    ranking = sorted(zip(featurizer.feature_names, importance.importances_mean, importance.importances_std), key=lambda t: -t[1])
    support = np.bincount(y_class, minlength=3)
    report_dict = classification_report(y_class, pred_class, labels=[0, 1, 2], target_names=names, output_dict=True, zero_division=0)
    splits = {s: {'rows': int(masks[s].sum()), 'resume_groups': int(cv.loc[ri[masks[s]], 'group'].nunique()), 'candidates': int(pairs.loc[masks[s], 'candidate_id'].nunique()),
                  'jobs': int(pairs.loc[masks[s], 'job_id'].nunique()),
                  'class_counts': {n: int(c) for n, c in zip(names, np.bincount(np.digitize(y[masks[s]], mf.THRESHOLDS), minlength=3))}} for s in split_names}
    report = {
        'classes': names, 'model': 'Features de relacao currículo-vaga + HistGradientBoostingRegressor (score) + residuos empiricos (faixas)', 'splits': splits,
        'evaluation': {
            'metrics': {'accuracy': metrics['accuracy'], 'f1_macro': metrics['f1_macro']},
            'regression': {'r2': metrics['r2'], 'mae': metrics['mae'], 'score_std_teste': float(np.std(y[test]))},
            'bootstrap': {'method': 'percentile_cluster_job', 'iterations': iterations, 'confidence': .95, 'scope': 'Modelo fixo; curriculos e vagas de teste inéditos; reamostragem por vaga; nao inclui variacao do retreino.'},
            'probability_quality': {'calibrated': quality},
            'classification_report': report_dict,
            'confusion_matrix': {'labels': names, 'counts': matrix.astype(int).tolist()},
            'baselines': baselines,
            'interval_80_coverage_test': coverage,
            'feature_importance': [{'feature': n, 'label': mf.FEATURE_LABELS.get(n, n), 'importance': float(m), 'std': float(s)} for n, m, s in ranking],
            'job_area_classifier_accuracy': job_acc,
            'iterations_selected_on_validation': best,
        }}
    metadata = {'classes': names, 'thresholds': list(mf.THRESHOLDS), 'data_split': splits, 'test_metrics': report['evaluation'], 'n_residuals': int(len(residuals)),
                'interval_80': [low, high]}
    return model, report, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--output-dir', type=Path, default=None)
    parser.add_argument('--bootstrap', type=int, default=1000)
    parser.add_argument('--detect-language', action='store_true', help='Aplica a deteccao PT/EN tambem no treino (lento; o dataset e em ingles).')
    args = parser.parse_args()
    if args.bootstrap < 100:
        parser.error('--bootstrap deve ser pelo menos 100.')
    if not args.detect_language:
        preprocess.to_english = lambda text: text
    cv, jobs, pairs = [read(args.data_dir / name) for name in ['cv.csv', 'job.csv', 'matches.csv']]
    resume_col = column(cv, ['resume_text', 'resume', 'cv_text', 'text', 'resume_str'])
    job_col = column(jobs, ['job_description', 'description', 'job_text', 'text'])
    category_col = column(jobs, ['category', 'job_category'])
    cv = cv.dropna(subset=['candidate_id', resume_col]).copy()
    jobs = jobs.dropna(subset=['job_id', job_col, category_col]).copy()
    if cv['candidate_id'].duplicated().any() or jobs['job_id'].duplicated().any():
        raise ValueError('IDs duplicados: resolva os registros antes do treino.')
    # 'Target position: X' e um artefato do dataset (derivado do rotulo): usuarios reais nao o enviam.
    position = cv['target_position'].fillna('') if 'target_position' in cv else pd.Series('', index=cv.index)
    cv['raw'] = [text.replace('Target position: ' + str(pos), '', 1).strip() for text, pos in zip(cv[resume_col], position)]
    title = jobs['job_title'].fillna('') if 'job_title' in jobs else pd.Series('', index=jobs.index)
    jobs['raw'] = title.astype(str) + '\n' + jobs[job_col].astype(str)
    cv['resume'] = cv['raw'].map(limpar_texto)
    jobs['job'] = jobs['raw'].map(limpar_texto)
    cv = cv[cv['resume'].str.strip().ne('')].copy()
    jobs = jobs[jobs['job'].str.strip().ne('')].copy()
    jobs = jobs.rename(columns={category_col: 'category'})
    for frame, name in [(cv, 'clean_skills'), (jobs, 'clean_skills')]:
        if name not in frame:
            frame[name] = '[]'
    cv['years_experience'] = pd.to_numeric(cv.get('years_experience'), errors='coerce')
    jobs['years_required'] = pd.to_numeric(jobs.get('years_required'), errors='coerce')
    cv['group'] = cv['resume'].map(lambda text: hashlib.sha256(text.encode()).hexdigest())
    pairs = pairs.dropna(subset=['candidate_id', 'job_id', 'label_strength', 'final_score']).copy()
    if not set(pairs['label_strength']) <= set(RANK):
        raise ValueError('Rotulo nao reconhecido; nao sera descartado silenciosamente.')
    if pairs.duplicated(['candidate_id', 'job_id']).any():
        raise ValueError('Pares duplicados.')
    pairs = pairs.merge(cv[['candidate_id', 'resume']], on='candidate_id', validate='many_to_one').merge(jobs[['job_id', 'job', 'category']], on='job_id', validate='many_to_one')
    if pairs.empty:
        raise ValueError('Nenhum par valido apos os joins.')
    # Coerencia do dataset: a faixa deve seguir os cortes do score.
    expected = pairs['final_score'].map(lambda s: ('weak_positive', 'medium_positive', 'strong_positive')[int(np.digitize(s, mf.THRESHOLDS))])
    mismatched = float((expected != pairs['label_strength']).mean())
    if mismatched > .001:
        raise ValueError(f'Rotulos nao seguem os cortes {mf.THRESHOLDS} do final_score ({mismatched:.1%} divergentes).')

    groups = split_groups(cv[cv['candidate_id'].isin(pairs['candidate_id'])])
    pairs['rank'] = pairs['label_strength'].map(RANK)
    best = pairs[pairs['rank'].eq(pairs.groupby('candidate_id')['rank'].transform('max'))]
    categories_per_candidate = best.groupby('candidate_id')['category'].agg(lambda values: sorted(set(values)))
    unambiguous = categories_per_candidate[categories_per_candidate.map(len).eq(1)].map(lambda values: values[0])
    area = cv.merge(unambiguous.rename('target'), on='candidate_id', validate='one_to_one')
    area['text'] = area['resume']
    print('Treinando area derivada...', flush=True)
    area_model, area_base, area_parts, area_report = fit_area(area, groups, args.bootstrap)
    print('Treinando matching (curriculos e vagas inéditos no teste)...', flush=True)
    match_model, match_report, metadata_match = matching_task(cv, jobs, pairs, groups, area_base, area_parts['train'].set_index('candidate_id')['target'], args.bootstrap)

    vectorizer = area_base.named_steps['tfidf']
    x = normalize(vectorizer.transform(area_parts['train']['text']))
    centroid_matrix = np.vstack([np.asarray(x[area_parts['train']['target'].eq(c).to_numpy()].mean(axis=0)).ravel() for c in area_model.classes_])
    centroid_matrix = normalize(centroid_matrix)
    # A similaridade ao centroide cai em textos curtos: o limiar usa trechos de tamanhos variados.
    rng = np.random.default_rng(SEED)
    def cut(text):
        words = text.split()
        return ' '.join(words[:max(8, int(len(words) * rng.uniform(.25, 1.0)))])
    val = normalize(vectorizer.transform(area_parts['validation']['text'].map(cut)))
    threshold = float(np.percentile(np.asarray(val @ centroid_matrix.T).max(axis=1), 5))
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    limitations = [
        'Rotulos e scores de compatibilidade sao os do dataset (heuristica ponderada); origem e validacao humana nao verificadas.',
        'O dataset concentra currículos de TI (~85%) e as faixas dependem de um score estreito (desvio padrao ~0,04): a separacao fraca/media e intrinsecamente ruidosa.',
        'Faixa "forte" e rara (<1% dos pares): a recall dessa classe e baixa e nao deve ser usada como filtro.',
        'Area e rotulo derivado das vagas de maior nivel de match; empates entre categorias foram excluidos.',
        'Textos identicos apos limpeza ficam juntos; duplicatas aproximadas nao sao detectadas.',
        'Ingles; em portugues o texto e traduzido localmente (Marian) antes do ML e o desempenho nao foi validado.',
        'Anos de experiencia sao extraidos por regras no texto; no treino usam-se as colunas do dataset, entao a extracao pode divergir.',
        'Probabilidades de faixa vem da distribuicao empirica dos residuos (calibracao em curriculos/vagas inéditos); nao sao chance de contratacao.',
        'OOD: percentil empirico da validacao, sem avaliacao com corpus externo OOD.',
        'Bootstrap condicional ao modelo fixo, agrupado por vaga. Nao inclui incerteza de retreino.',
    ]
    report = {'schema_version': 2, 'run_id': run_id, 'dataset': 'Shresth786/job-resume-matching', 'sklearn_version': sklearn.__version__, 'seed': SEED,
              'split_strategy': 'Area: hashes de curriculos limpos disjuntos (60/15/10/15). Matching: curriculos E vagas disjuntos entre treino/calibracao/validacao/teste; so pares dentro do mesmo conjunto.',
              'label_provenance': 'not_verified', 'area_candidates_excluded_ambiguous': int(len(categories_per_candidate) - len(unambiguous)),
              'tasks': {'area': area_report, 'compatibility': match_report}, 'limitations': limitations}
    metadata_area = {'run_id': run_id, 'classes': list(area_model.classes_), 'class_centroids': {str(c): row.tolist() for c, row in zip(area_model.classes_, centroid_matrix)},
                     'ood_threshold': threshold, 'ood_validated': False, 'data_split': area_report['splits'], 'test_metrics': area_report['evaluation']}
    metadata_match = {'run_id': run_id, **metadata_match}
    output = args.output_dir or ROOT / 'artifacts' / run_id
    output.mkdir(parents=True, exist_ok=False)
    artifacts = {'classificador_area.joblib': area_model, 'ml_metadata_area.joblib': metadata_area, 'classificador_compatibilidade.joblib': match_model, 'ml_metadata_compatibilidade.joblib': metadata_match}
    for name, value in artifacts.items():
        joblib.dump(value, output / name, compress=3)
    (output / 'evaluation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    models = ROOT / 'models'
    models.mkdir(exist_ok=True)
    for name in [*artifacts, 'evaluation.json']:
        temp = models / (name + '.tmp')
        temp.write_bytes((output / name).read_bytes())
        temp.replace(models / name)
    print(f'Concluido: {output}. Modelos publicados em {models}. Reinicie o backend.')


if __name__ == '__main__':
    main()
