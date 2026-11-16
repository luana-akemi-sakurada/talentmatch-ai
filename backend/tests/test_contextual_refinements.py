import copy
import json
from pathlib import Path

import pytest

from backend.app.schemas.analysis import GroundedLLMResponse
from backend.app.services.grounding import ground
from backend.tests.test_evidence_passages import sdk_response


FIXTURE = json.loads((Path(__file__).parent / 'fixtures/contextual.json').read_text(encoding='utf-8'))


def result(payload=None):
    return ground(GroundedLLMResponse.model_validate(payload or FIXTURE['provider']),
                  FIXTURE['resume'], FIXTURE['job'], False)


def test_grounded_contextual_profile_keeps_essential_results():
    value = result()
    assert value.perfil_profissional.descricao == 'Desenvolvedora Backend Java'
    assert value.nota_aderencia is None


@pytest.mark.parametrize('change', ['invented_profile', 'negative_profile', 'invented_profile_quote'])
def test_profile_cannot_introduce_role_or_seniority_without_literal_support(change):
    data = copy.deepcopy(FIXTURE['provider'])
    if change == 'invented_profile':
        data['perfil_profissional']['descricao'] = 'Arquiteta Sênior Java'
    elif change == 'negative_profile':
        data['perfil_profissional']['evidencia'] = 'Não sou Desenvolvedora Backend Java.'
    else:
        data['perfil_profissional']['evidencia'] = 'Desenvolvedora Backend Java em empresa internacional.'
    value = result(data)
    assert value.perfil_profissional is None


def test_provider_and_api_preserve_actual_ml_category_independent_of_profile(client, sdk_response):
    response, sent = sdk_response
    response.update(copy.deepcopy(FIXTURE['provider']))
    baseline = client.post('/api/analyze', data={'mode': 'demo', 'resume_text': FIXTURE['resume'],
                                                'job_description': FIXTURE['job']}).json()['ml']
    value = client.post('/api/analyze', data={'resume_text': FIXTURE['resume'],
                                            'job_description': FIXTURE['job']}).json()
    assert len(sent) == 1 and value['mode'] == 'live'
    assert value['ml'] == baseline
    assert value['llm']['perfil_profissional']['descricao'] == 'Desenvolvedora Backend Java'
    assert value['llm']['nota_aderencia'] is None


def test_default_is_live_and_never_silently_simulates_on_failure(client):
    value = client.post('/api/analyze', data={'resume_text': FIXTURE['resume'],
                                            'job_description': FIXTURE['job']}).json()
    assert value['mode'] == 'live' and value['llm'] is None
    assert value['llm_error'] == 'llm_not_configured' and value['ml']['top_categories']


