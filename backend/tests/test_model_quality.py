"""Diagnostic characterization of the preserved model, not population validation.

Some tests intentionally document weak safeguards currently present. A passing
test means the behavior was reproduced, not that the behavior is desirable.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
import llm
from backend.app.core.config import ROOT
from backend.app.services.analysis import analyze, demo_analysis
from backend.app.services.classifier import load_model, predict
from backend.app.services.privacy import minimize
from preprocess import limpar_texto

CASES = json.loads((ROOT / 'scripts/model_cases.json').read_text(encoding='utf-8'))
RESUME = CASES['cases'][0]['text']
JOB = CASES['job']


def probability(text):
    safe, _ = minimize(text, resume=True)
    return load_model().predict_proba([limpar_texto(safe)])[0]


def mock_provider(monkeypatch, result):
    monkeypatch.setenv('LLM_API_KEY', 'local-placeholder-not-real')
    monkeypatch.setenv('LLM_MODEL', 'mock-model')
    fake = MagicMock()
    fake.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content=json.dumps(result, ensure_ascii=False)))])
    monkeypatch.setattr(llm, '_client', lambda: fake)
    return fake


def grounded_response():
    first, second = [part + '.' for part in RESUME.split('. ')[:2]]
    evidence = lambda term: first if term in first else second
    return {'habilidades': [{'habilidade': term, 'evidencia': evidence(term)} for term in ['Java', 'Spring Boot', 'PostgreSQL', 'Git', 'JUnit', 'Docker']],
            'anos_experiencia': 2, 'evidencia_anos_experiencia': first, 'experiencia_profissional': [first],
            'nota_aderencia': 80,
            'requisitos_atendidos': [{'requisito': term, 'evidencia': evidence(term)} for term in ['Java', 'Spring Boot', 'PostgreSQL', 'Git', 'Docker']],
            'requisitos_sem_evidencia': ['Angular', 'AWS', 'metodologias ágeis']}


def test_observed_short_resume_is_reproduced_without_relabeling():
    result = predict(RESUME)
    assert [item.category for item in result.top_categories] == ['BUSINESS-DEVELOPMENT', 'AVIATION', 'CONSULTANT']
    assert [item.probability for item in result.top_categories] == pytest.approx([.58, .06333333333333334, .03666666666666667])
    assert probability(RESUME)[list(load_model().classes_).index('INFORMATION-TECHNOLOGY')] == pytest.approx(.02)


def test_language_and_detail_change_features_but_do_not_guarantee_expected_label():
    model = load_model()
    it = list(model.classes_).index('INFORMATION-TECHNOLOGY')
    pt = next(c['text'] for c in CASES['cases'] if c['id'] == 'software-short-pt')
    en = next(c['text'] for c in CASES['cases'] if c['id'] == 'software-short-en')
    long_en = next(c['text'] for c in CASES['cases'] if c['id'] == 'software-long-en')
    assert probability(pt)[it] < probability(en)[it] < probability(long_en)[it]
    assert predict(long_en).predicted_area == 'BUSINESS-DEVELOPMENT'
    assert np.allclose(probability(pt), probability('\n'.join([pt] * 8)))


def test_known_terms_are_not_equivalent_to_relevant_words_in_resume():
    vectorizer = load_model().named_steps['tfidf']
    assert limpar_texto('Java Spring Boot PostgreSQL APIs REST Git JUnit Docker') == 'java spring boot postgresql apis rest git junit docker'
    assert {'java', 'spring', 'rest'} <= vectorizer.vocabulary_.keys()
    assert not {'postgresql', 'git', 'junit', 'docker', 'spring boot', 'apis rest'} & vectorizer.vocabulary_.keys()
    assert vectorizer.build_analyzer()(limpar_texto('C++ C#')) == []
    assert vectorizer.transform([limpar_texto('zzqxv zzqxv')]).nnz == 0
    result = predict('zzqxv zzqxv')
    assert result.status == 'abstained'
    assert result.top_categories == [] and result.coverage.zero_vector


def test_cleaning_and_minimization_do_not_explain_these_case_differences():
    model = load_model()
    for case in CASES['cases']:
        safe, redactions = minimize(case['text'], resume=True)
        assert redactions == 0
        assert np.allclose(model.predict_proba([case['text']]), model.predict_proba([limpar_texto(safe)]))


def test_wrong_ml_does_not_overwrite_grounded_mock_llm_or_original_label(monkeypatch):
    fake = mock_provider(monkeypatch, grounded_response())
    response = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    assert response.ml.predicted_area == 'BUSINESS-DEVELOPMENT'
    assert response.llm is not None and 'Java' in response.llm.habilidades
    assert response.llm.nota_aderencia is None
    assert response.llm.abstention_reason == 'score_not_validated'
    assert all(item.evidencia in RESUME for item in response.llm.requisitos_atendidos)
    payload = json.loads(fake.chat.completions.create.call_args.kwargs['messages'][1]['content'])
    assert payload['area_ml'] == 'BUSINESS-DEVELOPMENT'
    assert payload['confianca_ml'] == pytest.approx(.58)
    assert 'não prova de competência' in llm.SYSTEM
    # The adapter transmits an ML prior; this does not measure real LLM anchoring.
    direct = llm.analisar(RESUME, JOB, 'INFORMATION-TECHNOLOGY', .58)
    assert direct == response.llm.model_dump()


def test_demo_75_uses_only_four_recognized_job_terms():
    response = demo_analysis(RESUME, JOB)
    assert response.nota_aderencia == 75
    assert {item.requisito for item in response.requisitos_atendidos} == {'Java', 'Git', 'Docker'}
    assert response.requisitos_sem_evidencia == ['AWS']
    assert response.anos_experiencia is None


def test_false_evidence_becomes_partial_result_with_ml_preserved(monkeypatch):
    result = grounded_response()
    result['requisitos_atendidos'].append({'requisito': 'AWS', 'evidencia': 'Experiência comprovada com AWS'})
    mock_provider(monkeypatch, result)
    response = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    assert response.llm is None and response.llm_error == 'unsupported_evidence'
    assert response.ml.predicted_area == 'BUSINESS-DEVELOPMENT'


def test_honest_no_evidence_response_is_supported(monkeypatch):
    result = grounded_response()
    result.update(habilidades=[], anos_experiencia=None, evidencia_anos_experiencia=None,
                  experiencia_profissional=[], nota_aderencia=0,
                  requisitos_atendidos=[], requisitos_sem_evidencia=['Java'])
    mock_provider(monkeypatch, result)
    response = analyze('Documento sem descrição profissional.', JOB, 'live', 'Candidato fictício')
    assert response.llm is not None and response.llm.nota_aderencia is None
    assert response.llm.abstention_reason == 'insufficient_evidence'
    assert not response.llm.requisitos_atendidos


def test_high_score_without_evidence_now_abstains(monkeypatch):
    result = grounded_response()
    result.update(habilidades=[], anos_experiencia=None, evidencia_anos_experiencia=None,
                  experiencia_profissional=[], nota_aderencia=95,
                  requisitos_atendidos=[], requisitos_sem_evidencia=[])
    mock_provider(monkeypatch, result)
    response = analyze(RESUME, JOB, 'live', 'Candidato fictício')
    assert response.llm is not None and response.llm.nota_aderencia is None
    assert 'Abstenção' in response.llm.resumo
