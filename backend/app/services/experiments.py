import json
from backend.app.core.config import MODEL_DIR
from backend.app.core.errors import ServiceError
from backend.app.services.classifier import _load_artifacts, load_model


def metrics() -> dict:
    try:
        report = json.loads((MODEL_DIR / 'evaluation.json').read_text(encoding='utf-8'))
        if report['schema_version'] != 2 or set(report['tasks']) != {'area', 'compatibility'}:
            raise ValueError('schema')
        _, area, _, match = _load_artifacts()
        if not report.get('run_id') or report['run_id'] != area.get('run_id') or report['run_id'] != match.get('run_id'):
            raise ValueError('run_mismatch')
        for task in report['tasks'].values():
            task['evaluation']['metrics']['accuracy']['point']
            task['evaluation']['metrics']['f1_macro']['point']
        return report
    except (OSError, ValueError, KeyError, TypeError, ServiceError):
        raise ServiceError('evaluation_unavailable', 'Avaliação atual indisponível ou incompatível com os modelos. Execute o novo train.py e reinicie o backend. Métricas antigas não serão utilizadas.', 503) from None


def categories() -> dict:
    return {'categories': [str(c) for c in load_model().classes_], 'counts': None, 'distribution_available': False, 'notice': 'Áreas derivadas das vagas associadas no dataset, não rótulos profissionais anotados diretamente nos currículos.'}
