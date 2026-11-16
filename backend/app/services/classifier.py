from functools import lru_cache
import logging
import joblib
from preprocess import limpar_texto
from backend.app.core.config import MODEL_DIR
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import MLResult, CategoryProbability, MLCoverage

logger = logging.getLogger('talentmatch.classifier')


@lru_cache(maxsize=1)
def load_model():
    try:
        model = joblib.load(MODEL_DIR / 'classificador.joblib')
        if not hasattr(model, 'predict_proba') or not hasattr(model, 'classes_'):
            raise ValueError('invalid pipeline')
        return model
    except Exception:
        raise ServiceError('model_unavailable', 'Classificador indisponível. Verifique o artefato e a versão do scikit-learn.', 503) from None


def predict(text: str) -> MLResult:
    model = load_model()
    cleaned = limpar_texto(text)
    try:
        vectorizer = model.named_steps['tfidf']
        features = vectorizer.transform([cleaned])
        unigrams = {term for term in vectorizer.build_analyzer()(cleaned) if ' ' not in term}
        known = len(unigrams & vectorizer.vocabulary_.keys())
        total = len(unigrams)
        coverage = MLCoverage(active_features=features.nnz, analyzed_unigrams=total,
                              known_unigrams=known, unknown_unigrams=total-known,
                              unigram_coverage=known/total if total else None,
                              zero_vector=features.nnz == 0)
        logger.info('ml_coverage active_features=%d known_unigrams=%d total_unigrams=%d coverage=%s zero_vector=%s',
                    features.nnz, known, total, coverage.unigram_coverage, coverage.zero_vector)
        if coverage.zero_vector:
            return MLResult(predicted_area='INDETERMINADA', model_name=type(model.named_steps['clf']).__name__,
                            top_categories=[], status='abstained', coverage=coverage,
                            warnings=['Abstenção ML: o TF-IDF gerou um vetor vazio. Nenhuma categoria ou probabilidade foi emitida. A análise contextual permanece independente.'])
        warnings = []
        if known < total:
            warnings.append(f'Cobertura lexical TF-IDF: {known}/{total} unigramas únicos reconhecidos ({100*known/total:.2f}%). '
                            f'{total-known} ignorados. Isto não mede confiança; não há limiar de confiabilidade validado. '
                            'A categoria pode não representar o currículo, especialmente com poucos termos reconhecidos.')
        probabilities = model.named_steps['clf'].predict_proba(features)[0]
        ranked = sorted(zip(model.classes_, probabilities), key=lambda pair: pair[1], reverse=True)[:3]
        return MLResult(predicted_area=str(ranked[0][0]), model_name=type(model.named_steps['clf']).__name__,
                        top_categories=[CategoryProbability(category=str(c), probability=float(p)) for c, p in ranked],
                        coverage=coverage, warnings=warnings)
    except Exception:
        raise ServiceError('prediction_failed', 'Não foi possível executar a classificação.', 503) from None
