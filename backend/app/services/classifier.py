from functools import lru_cache
import joblib
import numpy as np
from sklearn.preprocessing import normalize
from preprocess import limpar_texto
from backend.app.core.config import MODEL_DIR
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import MLResult, CategoryProbability, MLCoverage

BAND_LABELS = {'compatibilidade_fraca': 'Fraca', 'compatibilidade_media': 'Média', 'compatibilidade_forte': 'Forte'}
EDUCATION_LABELS = {0: 'não identificada', 1: 'técnico / ensino médio', 2: 'graduação', 3: 'pós-graduação / mestrado', 4: 'doutorado'}


@lru_cache(maxsize=1)
def _load_artifacts():
    try:
        area = joblib.load(MODEL_DIR / 'classificador_area.joblib')
        am = joblib.load(MODEL_DIR / 'ml_metadata_area.joblib')
        match = joblib.load(MODEL_DIR / 'classificador_compatibilidade.joblib')
        mm = joblib.load(MODEL_DIR / 'ml_metadata_compatibilidade.joblib')
        if not am.get('run_id') or am['run_id'] != mm.get('run_id'):
            raise ValueError('Artefatos de execuções diferentes ou antigos.')
        if not hasattr(match, 'predict_pair'):
            raise ValueError('Modelo de compatibilidade em formato antigo.')
        return area, am, match, mm
    except Exception:
        raise ServiceError('model_unavailable', 'Artefatos indisponíveis ou antigos. Execute o novo train.py com scikit-learn >= 1.6 e reinicie o backend.', 503) from None


def load_model():
    return _load_artifacts()[0]


@lru_cache(maxsize=128)
def _clean(text: str) -> str:
    # A tradução PT->EN é cara: currículo e vaga são limpos uma única vez por análise.
    return limpar_texto(text)


def _vectorizer(model):
    estimator = model.calibrated_classifiers_[0].estimator
    base = getattr(estimator, 'estimator', estimator)
    return base.named_steps['tfidf']


def _uncertainty(model, text):
    p = model.predict_proba([text])[0]
    return p, np.argsort(-p), _summary(p)


def _summary(p):
    order = np.argsort(-p)
    positive = p[p > 0]
    entropy = float(-(positive * np.log(positive)).sum() / np.log(len(p))) if len(p) > 1 else 0.0
    return {'probabilidade_calibrada': float(p[order[0]]), 'margem_top1_top2': float(p[order[0]] - p[order[1]]) if len(p) > 1 else 1.0, 'entropia_normalizada': entropy, 'nivel_confianca': 'não validada'}


def predict(text: str) -> MLResult:
    model = load_model()
    cleaned = _clean(text)
    vectorizer = _vectorizer(model)
    features = vectorizer.transform([cleaned])
    terms = {t for t in vectorizer.build_analyzer()(cleaned) if ' ' not in t}
    known = len(terms.intersection(vectorizer.vocabulary_))
    coverage = MLCoverage(active_features=features.nnz, analyzed_unigrams=len(terms), known_unigrams=known, unknown_unigrams=len(terms)-known, unigram_coverage=known/len(terms) if terms else None, zero_vector=features.nnz == 0)
    warnings = ['Área derivada das vagas associadas no dataset; não comprova profissão ou competência.', 'Probabilidades calibradas não são chance de contratação. Faixas de confiança não foram validadas.']
    if features.nnz == 0:
        return MLResult(predicted_area='INDETERMINADA', model_name='LogisticRegression calibrada', status='abstained', top_categories=[], coverage=coverage, warnings=[*warnings, 'Abstenção: vetor TF-IDF vazio.'])
    p, order, _ = _uncertainty(model, cleaned)
    return MLResult(predicted_area=str(model.classes_[order[0]]), model_name='LogisticRegression calibrada', top_categories=[CategoryProbability(category=str(model.classes_[i]), probability=float(p[i])) for i in order[:3]], coverage=coverage, warnings=warnings)


def _compatibility(match, resume_clean: str, resume_raw: str, job_clean: str, job_raw: str) -> dict:
    if not resume_clean.strip() or not job_clean.strip():
        return {'disponivel': False, 'motivo': 'Currículo ou vaga sem atributos reconhecidos para o matching.'}
    result = match.predict_pair(resume_clean, resume_raw, job_clean, job_raw)
    probs = np.asarray(result['probabilidades'], dtype=float)
    summary = _summary(probs)
    order = np.argsort(-probs)
    names = list(match.classes_)
    values = result['valores']
    low, high = result['intervalo']
    years_resume, years_job = values.get('resume_years'), values.get('job_years')
    return {
        'disponivel': True,
        'rotulo_bruto': str(names[order[0]]),
        'compatibilidade_prevista': BAND_LABELS[str(names[order[0]])],
        **summary,
        'alternativas': [{'compatibilidade': BAND_LABELS[str(names[i])], 'probabilidade_calibrada': float(probs[i])} for i in order[1:]],
        'score_estimado': result['score'],
        'intervalo_80': [low, high],
        'cortes_faixas': [0.58, 0.68],
        'faixas': [{'faixa': BAND_LABELS[str(n)], 'probabilidade': float(p)} for n, p in zip(names, probs)],
        'sinais': sorted(result['contribuicoes'], key=lambda item: -abs(item['contribuicao'])),
        'habilidades_em_comum': result['habilidades_em_comum'][:20],
        'habilidades_da_vaga_ausentes': result['habilidades_da_vaga_ausentes'][:20],
        'n_habilidades_vaga': int(values.get('n_job_skills') or 0),
        'similaridade_textual': values.get('cos_tfidf'),
        'anos_curriculo': years_resume,
        'anos_vaga': years_job,
        'formacao_curriculo': EDUCATION_LABELS.get(int(values.get('resume_edu') or 0), 'não identificada'),
        'formacao_vaga': EDUCATION_LABELS.get(int(values.get('job_edu') or 0), 'não identificada'),
    }


def build_ml_context(texto_curriculo: str, requisitos: list[str], texto_vaga: str) -> dict:
    area, metadata, match, _ = _load_artifacts()
    resume = _clean(texto_curriculo)
    job = _clean(texto_vaga)
    vectorizer = _vectorizer(area)
    x = normalize(vectorizer.transform([resume]))
    if not x.nnz:
        return {'disponivel': False, 'motivo': 'Vetor TF-IDF vazio.'}
    p, order, uncertainty = _uncertainty(area, resume)
    centroids = normalize(np.vstack([metadata['class_centroids'][c] for c in metadata['classes']]))
    similarities = np.asarray(x @ centroids.T).ravel()
    nearest = int(similarities.argmax())
    ranked = []
    if requisitos:
        req = normalize(vectorizer.transform([_clean(r) for r in requisitos]))
        values = (x @ req.T).toarray().ravel()
        ranked = sorted([{'requisito': r, 'similaridade_cosseno': float(v)} for r, v in zip(requisitos, values)], key=lambda row: row['similaridade_cosseno'], reverse=True)
    compatibility = _compatibility(match, resume, texto_curriculo, job, texto_vaga)
    if not compatibility['disponivel']:
        return compatibility
    return {'disponivel': True, 'area_prevista': str(area.classes_[order[0]]), 'probabilidade_area_prevista': uncertainty['probabilidade_calibrada'], 'nivel_confianca': uncertainty['nivel_confianca'], 'margem_top1_top2': uncertainty['margem_top1_top2'], 'entropia_normalizada': uncertainty['entropia_normalizada'], 'alternativas': [{'area': str(area.classes_[i]), 'probabilidade_calibrada': float(p[i])} for i in order[1:3]], 'deteccao_fora_distribuicao': {'possivel_ood': bool(similarities[nearest] < metadata['ood_threshold']), 'similaridade_ao_centroide_mais_proximo': float(similarities[nearest]), 'classe_centroide_mais_proxima': metadata['classes'][nearest], 'limiar_validado': float(metadata['ood_threshold']), 'validado_externamente': False}, 'compatibilidade_curriculo_vaga': compatibility, 'requisitos_priorizados': ranked, 'interpretacao': 'Faixas de confiança não validadas. OOD é alerta empírico experimental; similaridade não prova requisito. O score de compatibilidade reproduz a heurística do dataset, não chance de contratação.'}
