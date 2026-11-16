"""Test B reproduction with fictitious inputs; no claim about provider accuracy."""
import pytest

from backend.app.services.classifier import predict
from backend.tests.test_evidence_passages import sdk_response


FINANCE = 'Atuei em finanças com Excel.'
JOB = 'Buscamos experiência com Java e Spring Boot.'


def provider_result(experience):
    return {'habilidades': [{'habilidade': 'Excel', 'evidencia': FINANCE}],
            'experiencia_profissional': experience, 'anos_experiencia': None,
            'evidencia_anos_experiencia': None, 'requisitos_atendidos': [],
            'requisitos_sem_evidencia': ['Java', 'Spring Boot'], 'nota_aderencia': 100}


@pytest.mark.parametrize('nonpositive', [
    'Não tenho experiência com Java.',
    'Sem experiência com Java.',
    'Pretendo aprender Java.',
])
def test_b_nonpositive_second_experience_abstains_and_preserves_ml(client, sdk_response, nonpositive):
    response, sent = sdk_response
    resume = FINANCE + '\n' + nonpositive
    response.update(provider_result([FINANCE, nonpositive]))
    expected_ml = predict(resume).model_dump(mode='json')
    result = client.post('/api/analyze', data={
        'mode': 'live', 'resume_text': resume, 'job_description': JOB})
    assert result.status_code == 200 and len(sent) == 1
    data = result.json()
    assert data['ml']['status'] == 'predicted'
    assert data['ml'] == expected_ml
    assert data['llm'] is None and data['llm_error'] == 'unsupported_evidence'
    assert data['llm_diagnostic'] == {'rule': 'nonpositive_evidence',
        'field': 'experiencia_profissional', 'source': 'curriculo', 'category': 'support', 'index': 1}
    assert any('negação ou ausência' in warning for warning in data['warnings'])


def test_incompatibility_alone_does_not_require_abstention(client, sdk_response):
    response, _ = sdk_response
    resume = FINANCE + '\nNão tenho experiência com Java.'
    # The provider lists only positive, literal professional experience. Missing
    # requirements remain missing, without treating the negative quote as experience.
    response.update(provider_result([FINANCE]))
    result = client.post('/api/analyze', data={
        'mode': 'live', 'resume_text': resume, 'job_description': JOB})
    data = result.json()
    assert result.status_code == 200 and data['llm_error'] is None
    assert data['llm_diagnostic'] is None
    assert data['llm']['habilidades'] == ['Excel']
    assert data['llm']['experiencia_profissional'] == [FINANCE]
    assert data['llm']['requisitos_atendidos'] == []
    assert data['llm']['requisitos_sem_evidencia'] == ['Java', 'Spring Boot']
    assert data['llm']['nota_aderencia'] is None
