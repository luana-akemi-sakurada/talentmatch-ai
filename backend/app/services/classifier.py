from functools import lru_cache
import joblib
import numpy as np
from sklearn.preprocessing import normalize
from preprocess import limpar_texto
from backend.app.core.config import MODEL_DIR
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import MLResult, CategoryProbability, MLCoverage


@lru_cache(maxsize=1)
def _load_artifacts():
    try:
        area = joblib.load(MODEL_DIR / 'classificador_area.joblib')
        am = joblib.load(MODEL_DIR / 'ml_metadata_area.joblib')
        match = joblib.load(MODEL_DIR / 'classificador_compatibilidade.joblib')
        mm = joblib.load(MODEL_DIR / 'ml_metadata_compatibilidade.joblib')
        if not am.get('run_id') or am['run_id'] != mm.get('run_id'):
            raise ValueError('Artefatos de execuções diferentes ou antigos.')
        return area, am, match, mm
    except Exception:
        raise ServiceError('model_unavailable', 'Artefatos indisponíveis ou antigos. Execute o novo train.py com scikit-learn >= 1.6 e reinicie o backend.', 503) from None


def load_model():
    return _load_artifacts()[0]


def _vectorizer(model):
    estimator = model.calibrated_classifiers_[0].estimator
    base = getattr(estimator, 'estimator', estimator)
    return base.named_steps['tfidf']


def _uncertainty(model, text):
    p = model.predict_proba([text])[0]
    order = np.argsort(-p)
    positive = p[p > 0]
    entropy = float(-(positive * np.log(positive)).sum() / np.log(len(p))) if len(p) > 1 else 0.0
    return p, order, {'probabilidade_calibrada': float(p[order[0]]), 'margem_top1_top2': float(p[order[0]] - p[order[1]]) if len(p) > 1 else 1.0, 'entropia_normalizada': entropy, 'nivel_confianca': 'não validada'}


def predict(text: str) -> MLResult:
    model = load_model()
    cleaned = limpar_texto(text)
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


def build_ml_context(texto_curriculo: str, requisitos: list[str], texto_vaga: str) -> dict:
    area, metadata, match, _ = _load_artifacts()
    resume = limpar_texto(texto_curriculo)
    job = limpar_texto(texto_vaga)
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
        req = normalize(vectorizer.transform([limpar_texto(r) for r in requisitos]))
        values = (x @ req.T).toarray().ravel()
        ranked = sorted([{'requisito': r, 'similaridade_cosseno': float(v)} for r, v in zip(requisitos, values)], key=lambda row: row['similaridade_cosseno'], reverse=True)
    combined = resume + ' [SEP] ' + job
    mv = _vectorizer(match)
    match_available = bool(mv.transform([resume]).nnz and mv.transform([job]).nnz)
    if not match_available:
        return {'disponivel': False, 'motivo': 'Currículo ou vaga sem atributos reconhecidos para o matching.'}
    mp, mo, mu = _uncertainty(match, combined)
    labels = {'compatibilidade_fraca': 'Fraca', 'compatibilidade_media': 'Média', 'compatibilidade_forte': 'Forte'}
    compatibility = {'disponivel': True, 'rotulo_bruto': str(match.classes_[mo[0]]), 'compatibilidade_prevista': labels.get(str(match.classes_[mo[0]]), str(match.classes_[mo[0]])), **mu, 'alternativas': [{'compatibilidade': labels.get(str(match.classes_[i]), str(match.classes_[i])), 'probabilidade_calibrada': float(mp[i])} for i in mo[1:]]}
    return {'disponivel': True, 'area_prevista': str(area.classes_[order[0]]), 'probabilidade_area_prevista': uncertainty['probabilidade_calibrada'], 'nivel_confianca': uncertainty['nivel_confianca'], 'margem_top1_top2': uncertainty['margem_top1_top2'], 'entropia_normalizada': uncertainty['entropia_normalizada'], 'alternativas': [{'area': str(area.classes_[i]), 'probabilidade_calibrada': float(p[i])} for i in order[1:3]], 'deteccao_fora_distribuicao': {'possivel_ood': bool(similarities[nearest] < metadata['ood_threshold']), 'similaridade_ao_centroide_mais_proximo': float(similarities[nearest]), 'classe_centroide_mais_proxima': metadata['classes'][nearest], 'limiar_validado': float(metadata['ood_threshold']), 'validado_externamente': False}, 'compatibilidade_curriculo_vaga': compatibility, 'requisitos_priorizados': ranked, 'interpretacao': 'Faixas de confiança não validadas. OOD é alerta empírico experimental; similaridade não prova requisito. Compatibilidade reproduz rótulos do dataset, não chance de contratação.'}
