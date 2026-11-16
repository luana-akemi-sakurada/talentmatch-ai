import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock
import numpy as np
import pytest
import llm
from backend.app.core.errors import ServiceError
from backend.app.core.config import ROOT
from backend.app.services.classifier import load_model, predict
from backend.app.services.analysis import analyze
from backend.app.services.grounding import duration_supported


RESUME = 'Experiência com Python e SQL.'
JOB = 'Python, SQL e AWS.'


def draft():
    return {'habilidades': [{'habilidade': 'Python', 'evidencia': RESUME}],
            'experiencia_profissional': [RESUME], 'anos_experiencia': None,
            'evidencia_anos_experiencia': None,
            'requisitos_atendidos': [{'requisito': 'Python', 'evidencia': RESUME}],
            'requisitos_sem_evidencia': ['AWS'], 'nota_aderencia': None}


def provider(monkeypatch, data):
    fake = MagicMock()
    fake.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content=json.dumps(data, ensure_ascii=False)))])
    monkeypatch.setenv('LLM_API_KEY', 'test-only')
    monkeypatch.setenv('LLM_MODEL', 'test-only')
    monkeypatch.setattr(llm, '_client', lambda: fake)
    return fake


@pytest.mark.parametrize('text', ['zzqxv zzqxv', 'the and or', 'C++ C#', '12345'])
def test_zero_vector_does_not_publish_arbitrary_probabilities(text):
    result = predict(text)
    assert result.status == 'abstained'
    assert result.predicted_area == 'INDETERMINADA'
    assert result.top_categories == []
    assert result.coverage.active_features == 0 and result.coverage.zero_vector
    assert 'Abstenção ML' in result.warnings[0]


def test_zero_vector_never_calls_the_forest(monkeypatch):
    fake = MagicMock(side_effect=AssertionError('Must not predict for zero vector'))
    monkeypatch.setattr(load_model().named_steps['clf'], 'predict_proba', fake)
    assert predict('zzqxv').status == 'abstained'
    fake.assert_not_called()


def test_coverage_is_measured_without_confidence_threshold_or_private_logs(caplog):
    caplog.set_level(logging.INFO, logger='talentmatch.classifier')
    result = predict('java privatezzqxv software')
    coverage = result.coverage
    assert coverage.known_unigrams == 2
    assert coverage.known_unigrams + coverage.unknown_unigrams == coverage.analyzed_unigrams
    assert coverage.unigram_coverage == coverage.known_unigrams / coverage.analyzed_unigrams
    assert result.status == 'predicted' and len(result.top_categories) == 3
    assert 'não há limiar de confiabilidade validado' in result.warnings[0]
    assert 'ml_coverage' in caplog.text and 'privatezzqxv' not in caplog.text


def test_nonempty_probabilities_remain_the_original_model_output():
    model = load_model()
    expected = model.predict_proba(['java software'])[0]
    result = predict('java software')
    mapping = dict(zip(model.classes_, expected))
    assert all(np.isclose(item.probability, mapping[item.category]) for item in result.top_categories)
    assert result.coverage.unigram_coverage == 1 and result.warnings == []


def test_extremely_sparse_diagnostic_case_is_reported_without_an_invented_cutoff():
    cases = json.loads((ROOT / 'scripts/model_cases.json').read_text(encoding='utf-8'))['cases']
    text = next(case['text'] for case in cases if case['id'] == 'finance-medium-pt')
    result = predict(text)
    assert result.coverage.known_unigrams == 1
    assert result.coverage.analyzed_unigrams == 46
    assert result.coverage.unigram_coverage == pytest.approx(1/46)
    assert result.status == 'predicted' and result.predicted_area == 'BUSINESS-DEVELOPMENT'
    assert '1/46' in result.warnings[0]


@pytest.mark.parametrize('score', [0, 80, 95, 100])
def test_no_evidence_scores_always_become_explicit_abstention(monkeypatch, score):
    data = draft()
    data.update(habilidades=[], experiencia_profissional=[], requisitos_atendidos=[], nota_aderencia=score)
    provider(monkeypatch, data)
    response = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    assert response.llm.nota_aderencia is None
    assert response.llm.abstention_reason == 'insufficient_evidence'
    assert response.llm.habilidades == []
    assert 'Abstenção' in response.llm.resumo
    assert any('Não significa aderência zero' in warning for warning in response.warnings)


@pytest.mark.parametrize('score', [80, 95, 100])
def test_partial_evidence_does_not_justify_provider_score(monkeypatch, score):
    data = draft()
    data['nota_aderencia'] = score
    provider(monkeypatch, data)
    result = llm.analisar(RESUME, JOB, 'BUSINESS-DEVELOPMENT', .58)
    assert result['nota_aderencia'] is None
    assert result['abstention_reason'] == 'score_not_validated'
    assert result['habilidades'] == ['Python']
    assert result['requisitos_atendidos'][0]['evidencia'] == RESUME
    assert result['requisitos_sem_evidencia'] == ['AWS']


@pytest.mark.parametrize('change', ['unrelated_requirement', 'clipped_quote', 'contradiction'])
def test_unsupported_claims_are_not_published(monkeypatch, change):
    data = draft()
    if change == 'unrelated_requirement':
        data['requisitos_atendidos'][0]['requisito'] = 'AWS'
    elif change == 'clipped_quote':
        data['habilidades'][0]['evidencia'] = 'Python'
    else:
        data['requisitos_sem_evidencia'] = ['Python']
    provider(monkeypatch, data)
    result = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    assert result.llm is None and result.llm_error == 'unsupported_evidence'
    assert result.ml.top_categories


@pytest.mark.parametrize('resume', ['Não tenho experiência com Python e SQL.', 'No experience with Python or SQL.', 'Pretendo aprender Python e SQL.'])
def test_negation_or_desire_is_not_a_positive_skill(monkeypatch, resume):
    data = draft()
    data['habilidades'][0]['evidencia'] = resume
    data['experiencia_profissional'] = []
    data['requisitos_atendidos'] = []
    provider(monkeypatch, data)
    with pytest.raises(ServiceError, match='negação ou ausência'):
        llm.analisar(resume, JOB, None, None)


def test_java_is_not_javascript(monkeypatch):
    data = draft()
    data['habilidades'] = [{'habilidade': 'Java', 'evidencia': 'Experiência com JavaScript.'}]
    data['experiencia_profissional'] = []; data['requisitos_atendidos'] = []
    data['requisitos_sem_evidencia'] = []
    provider(monkeypatch, data)
    result = llm.analisar('Experiência com JavaScript.', 'Java.', None, None)
    assert result['habilidades'] == []
    assert result['nota_aderencia'] is None
    assert result['abstention_reason'] == 'insufficient_evidence'


@pytest.mark.parametrize('years,evidence,expected', [
    (2, 'Desenvolvedora com dois anos de experiência em Java.', True),
    (2, 'Developer with two years of experience in Java.', True),
    (2.5, 'Possuo 2,5 anos de experiência em Python.', True),
    (5, 'Possuo 2 anos de experiência em Python.', False),
    (2, 'Developer from 2020 to 2022.', False),
    (2, 'Tenho mais de dois anos de experiência.', False),
    (2, 'Tenho dois anos de experiência em Java e três anos de experiência em Python.', False),
    (3, 'Tenho 2–3 anos de experiência em Java.', False),
    (3, 'Between two and three years of experience.', False),
])
def test_duration_requires_explicit_verifiable_value(years, evidence, expected):
    assert duration_supported(years, evidence) is expected


def test_independent_mode_payload_is_identical_for_different_ml_predictions(monkeypatch):
    fake = provider(monkeypatch, draft())
    monkeypatch.setenv('LLM_INCLUDE_ML_CONTEXT', 'false')
    first = llm.analisar(RESUME, JOB, 'BUSINESS-DEVELOPMENT', .58)
    first_messages = fake.chat.completions.create.call_args.kwargs['messages']
    second = llm.analisar(RESUME, JOB, 'INFORMATION-TECHNOLOGY', .99)
    second_messages = fake.chat.completions.create.call_args.kwargs['messages']
    assert first_messages == second_messages and first == second
    assert first['ml_context_included'] is False
    payload = json.loads(first_messages[1]['content'])
    assert 'area_ml' not in payload and 'confianca_ml' not in payload


def test_default_mode_preserves_ml_context_and_public_classification(monkeypatch):
    fake = provider(monkeypatch, draft())
    result = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    payload = json.loads(fake.chat.completions.create.call_args.kwargs['messages'][1]['content'])
    assert payload['area_ml'] == result.ml.predicted_area
    assert result.llm.ml_context_included is True


def test_empty_ml_does_not_prevent_independent_contextual_abstention(monkeypatch):
    data = draft()
    data.update(habilidades=[], experiencia_profissional=[], requisitos_atendidos=[])
    fake = provider(monkeypatch, data)
    result = analyze('zzqxv zzqxv', JOB, 'live', 'Candidato fictício')
    assert result.ml.status == 'abstained' and result.llm.nota_aderencia is None
    payload = json.loads(fake.chat.completions.create.call_args.kwargs['messages'][1]['content'])
    assert 'area_ml' not in payload


def test_api_warns_for_empty_features_and_keeps_existing_fields(client):
    result = client.post('/api/analyze', data={'resume_text': 'zzqxv zzqxv', 'job_description': JOB, 'mode': 'demo'})
    assert result.status_code == 200
    data = result.json()
    assert data['ml']['status'] == 'abstained' and data['ml']['top_categories'] == []
    assert data['ml']['coverage']['zero_vector'] is True
    assert any('vetor vazio' in warning for warning in data['warnings'])
    assert data['llm']['resumo'].startswith('DEMONSTRAÇÃO SIMULADA')


def test_invalid_context_config_fails_before_network(monkeypatch):
    fake = provider(monkeypatch, draft())
    monkeypatch.setenv('LLM_INCLUDE_ML_CONTEXT', 'maybe')
    with pytest.raises(ServiceError, match='true ou false'):
        llm.analisar(RESUME, JOB, 'HR', .5)
    fake.chat.completions.create.assert_not_called()


def test_missing_requirement_cannot_contradict_a_positive_literal_mention(monkeypatch):
    data = draft()
    data['requisitos_atendidos'] = []
    data['requisitos_sem_evidencia'] = ['SQL']
    provider(monkeypatch, data)
    with pytest.raises(ServiceError, match='contraditórios'):
        llm.analisar(RESUME, JOB, None, None)


def test_provider_cannot_inject_freeform_summary_into_public_response(monkeypatch):
    data = draft()
    data['resumo'] = 'Pessoa com experiência comprovada em vendas.'
    provider(monkeypatch, data)
    result = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    assert result.llm is None and result.llm_error == 'invalid_llm_response'


def test_portuguese_no_is_not_confused_with_english_no_experience(monkeypatch):
    data = draft()
    passage = 'Atua no desenvolvimento em Python e SQL.'
    data['habilidades'][0]['evidencia'] = passage
    data['experiencia_profissional'] = [passage]
    data['requisitos_atendidos'][0]['evidencia'] = passage
    provider(monkeypatch, data)
    assert llm.analisar(passage, JOB, None, None)['habilidades'] == ['Python']
