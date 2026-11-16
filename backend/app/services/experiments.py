import csv
from backend.app.core.config import MODEL_DIR
from backend.app.core.errors import ServiceError
from backend.app.services.classifier import load_model


def metrics() -> dict:
    try:
        with (MODEL_DIR / 'comparacao_modelos.csv').open(encoding='utf-8-sig') as file:
            rows = [{'name': row['modelo'], 'accuracy': float(row['acuracia']),
                     'f1_macro': float(row['f1_macro']), 'precision_macro': None,
                     'recall_macro': None} for row in csv.DictReader(file)]
        best = max(rows, key=lambda row: row['f1_macro'])
    except (OSError, ValueError, KeyError):
        raise ServiceError('metrics_unavailable', 'Não foi possível ler as métricas originais.', 503) from None
    return {'models': rows, 'selected_model': best['name'],
            'selection_criterion': 'F1 macro no conjunto de teste original',
            'source': 'models/comparacao_modelos.csv',
            'dataset': {'name': 'Resume Dataset — Kaggle / snehaanbhawal',
                        'train_fraction': 0.8, 'test_fraction': 0.2, 'random_state': 42,
                        'stratified': True, 'train_count': None, 'test_count': None,
                        'available_locally': (MODEL_DIR.parent / 'data/Resume.csv').exists()},
            'limitations': ['Precision e recall não foram salvos nos artefatos originais.',
                           'Contagens de treino, teste e categorias não estão registradas.',
                           'Seleção e avaliação no mesmo teste: desempenho sem conjunto independente final.',
                           'Métricas classificam área profissional; não validam aderência à vaga.']}


def categories() -> dict:
    return {'categories': [str(c) for c in load_model().classes_], 'counts': None,
            'distribution_available': False,
            'notice': 'Classes recuperadas do modelo. Frequências indisponíveis; não inferidas das probabilidades.'}
