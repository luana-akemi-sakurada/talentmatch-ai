"""Essential analysis only; real SDK with synthetic responses and no network."""
import json

import httpx
import pytest
from openai import OpenAI

import llm
from backend.app.core.config import ROOT
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import GroundedLLMResponse, LLMAnalysis


JOB = (ROOT / 'docs/exemplos/vaga.txt').read_text(encoding='utf-8')
CV_A = (ROOT / 'docs/exemplos/candidato-a.txt').read_text(encoding='utf-8')
CV_B = (ROOT / 'docs/exemplos/candidato-b.txt').read_text(encoding='utf-8')
QUOTE_A = 'Data analyst using Python, SQL and Power BI for reporting.'
QUOTE_B = 'Software developer using Java, React and Git for web applications.'


def extraction(compatible=True, insufficient=False):
    skills = [] if insufficient else ['Python', 'SQL', 'Power BI'] if compatible else ['Java', 'React', 'Git']
    passage = QUOTE_A if compatible else QUOTE_B
    return {'habilidades': [{'habilidade': skill, 'evidencia': passage} for skill in skills],
            'experiencia_profissional': [] if insufficient else [passage],
            'anos_experiencia': None, 'evidencia_anos_experiencia': None,
            'requisitos_atendidos': [{'requisito': skill, 'evidencia': passage} for skill in skills]
                if compatible and not insufficient else [],
            'requisitos_sem_evidencia': ['AWS'] if compatible and not insufficient else ['Python', 'SQL', 'Power BI', 'AWS'],
            'nota_aderencia': None,
            'perfil_profissional': None if insufficient else {
                'descricao': 'Data analyst' if compatible else 'Software developer', 'evidencia': passage}}


@pytest.fixture
def local_groq(monkeypatch):
    reply = {'status': 200, 'content': json.dumps(extraction()), 'finish_reason': 'stop'}
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        if reply.get('timeout'):
            raise httpx.ReadTimeout('synthetic timeout', request=request)
        if reply.get('connection_error'):
            raise httpx.ConnectError('synthetic connection failure', request=request)
        if reply['status'] != 200:
            return httpx.Response(reply['status'], json={'error': {
                'message': 'private-provider-marker', 'code': reply.get('code')}})
        return httpx.Response(200, json={'id': 'synthetic', 'object': 'chat.completion', 'created': 0,
            'model': 'openai/gpt-oss-120b', 'choices': [{'index': 0, 'finish_reason': reply['finish_reason'],
                'message': {'role': 'assistant', 'content': reply['content'], 'refusal': reply.get('refusal')}}]})

    with OpenAI(api_key='local-placeholder-only', base_url='http://mock.invalid/v1', max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(handler))) as sdk:
        monkeypatch.setenv('LLM_API_KEY', 'local-placeholder-only')
        monkeypatch.setenv('LLM_MODEL', 'openai/gpt-oss-120b')
        monkeypatch.setenv('LLM_BASE_URL', 'https://api.groq.com/openai/v1')
        monkeypatch.setattr(llm, '_client', lambda: sdk)
        yield reply, seen


def test_groq_request_uses_closed_required_structured_schema_and_no_interview(local_groq):
    _, seen = local_groq
    llm.analisar(CV_A, JOB, 'IT', .4)
    request = seen[0]
    wire = request['response_format']['json_schema']
    assert request['response_format']['type'] == 'json_schema' and wire['strict'] is True
    assert request['reasoning_effort'] == 'low'
    assert request['max_completion_tokens'] == 3500 and 'max_tokens' not in request
    schema = wire['schema']
    assert schema['properties']['nota_aderencia'] == {'type': 'null'}

    def check(node):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                assert node['additionalProperties'] is False
                assert set(node['required']) == set(node['properties'])
            for value in node.values():
                check(value)
        elif isinstance(node, list):
            for value in node:
                check(value)
    check(schema)
    assert 'perguntas' not in json.dumps(schema)
    assert 'perguntas' not in llm.SYSTEM and 'entrevista' not in llm.SYSTEM
    assert 'perguntas_entrevista' not in LLMAnalysis.model_fields
    assert 'perguntas_contextualizadas' not in GroundedLLMResponse.model_fields


@pytest.mark.parametrize('compatible,insufficient', [(True, False), (False, False), (False, True)])
def test_existing_fictional_inputs_complete_essential_analysis(client, local_groq, compatible, insufficient):
    reply, seen = local_groq
    reply['content'] = json.dumps(extraction(compatible, insufficient))
    resume = 'zzqxv zzqxv' if insufficient else CV_A if compatible else CV_B
    baseline = client.post('/api/analyze', data={'mode': 'demo', 'resume_text': resume, 'job_description': JOB}).json()['ml']
    value = client.post('/api/analyze', data={'mode': 'live', 'resume_text': resume, 'job_description': JOB}).json()
    assert len(seen) == 1 and value['mode'] == 'live'
    assert value['ml'] == baseline and value['llm_error'] is None
    contextual = value['llm']
    assert contextual['nota_aderencia'] is None
    assert 'perguntas_entrevista' not in contextual and 'entrevista_status' not in contextual
    if insufficient:
        assert contextual['habilidades'] == [] and contextual['perfil_profissional'] is None
        assert contextual['abstention_reason'] == 'insufficient_evidence'
    elif compatible:
        assert len(contextual['requisitos_atendidos']) == 3
        assert contextual['perfil_profissional']['descricao'] == 'Data analyst'
        assert contextual['pontos_fortes'] == [QUOTE_A]
    else:
        assert contextual['requisitos_atendidos'] == []
        assert contextual['requisitos_sem_evidencia'] == ['Python', 'SQL', 'Power BI', 'AWS']


@pytest.mark.parametrize('status,provider_code,expected', [
    (401, None, 'llm_auth_error'), (403, None, 'llm_permission_denied'),
    (404, None, 'llm_model_not_found'), (429, 'rate_limit_exceeded', 'llm_rate_limited'),
    (429, 'insufficient_quota', 'llm_quota_exceeded'), (429, {'unexpected': 'value'}, 'llm_rate_limited'),
    (400, None, 'llm_request_rejected'), (400, 'json_generation_failed', 'invalid_llm_response'),
    (422, 'json_validate_failed', 'invalid_llm_response'), (503, None, 'llm_unavailable'),
])
def test_upstream_errors_are_distinct_private_and_do_not_retry_or_simulate(client, local_groq, status, provider_code, expected, caplog):
    reply, seen = local_groq
    reply.update(status=status, code=provider_code)
    result = client.post('/api/analyze', data={'mode': 'live', 'resume_text': CV_A, 'job_description': JOB})
    assert result.status_code == 200
    value = result.json()
    assert len(seen) == 1 and value['llm_error'] == expected
    assert value['llm'] is None and value['ml']['top_categories'] and value['mode'] == 'live'
    assert 'private-provider-marker' not in result.text + caplog.text


@pytest.mark.parametrize('transport,expected', [('timeout', 'llm_timeout'), ('connection_error', 'llm_connection_error')])
def test_transport_errors_are_distinct(local_groq, transport, expected):
    reply, seen = local_groq
    reply[transport] = True
    with pytest.raises(ServiceError) as error:
        llm.analisar(CV_A, JOB, None, None)
    assert error.value.code == expected and len(seen) == 1


@pytest.mark.parametrize('change,expected,rule', [
    ('invalid_json', 'invalid_llm_response', 'json_invalid'),
    ('wrong_schema', 'invalid_llm_response', 'schema_invalid'),
    ('invented_quote', 'unsupported_evidence', 'quote_not_found'),
    ('unsupported_requirement', 'unsupported_evidence', 'requirement_not_in_evidence'),
    ('truncated', 'invalid_llm_response', 'response_truncated'),
])
def test_structure_and_grounding_remain_separate(client, local_groq, change, expected, rule):
    reply, _ = local_groq
    data = extraction()
    if change == 'invalid_json':
        reply['content'] = 'not-json'
    elif change == 'wrong_schema':
        reply['content'] = '{}'
    elif change == 'truncated':
        reply.update(content='{"habilidades":', finish_reason='length')
    else:
        if change == 'invented_quote':
            data['requisitos_atendidos'][0]['evidencia'] = 'Experiência inventada com Python.'
        else:
            data['requisitos_atendidos'][0]['requisito'] = 'AWS'
        reply['content'] = json.dumps(data)
    value = client.post('/api/analyze', data={'mode': 'live', 'resume_text': CV_A, 'job_description': JOB}).json()
    assert value['llm_error'] == expected and value['llm_diagnostic']['rule'] == rule
    assert value['llm'] is None and value['ml']['top_categories']


def test_retired_questions_even_malformed_do_not_affect_essential_response(local_groq):
    reply, _ = local_groq
    payload = extraction()
    payload.update(perguntas_contextualizadas={'invalid': 'ignored'}, perguntas_entrevista=17, entrevista_status='old')
    reply['content'] = json.dumps(payload)
    value = llm.analisar(CV_A, JOB, None, None)
    assert value['habilidades'] == ['Python', 'SQL', 'Power BI']
    assert 'perguntas_contextualizadas' not in value and value['nota_aderencia'] is None


def test_local_limits_remain_enforced_when_wire_schema_is_simplified():
    payload = extraction()
    payload['habilidades'][0]['habilidade'] = 'x' * 201
    with pytest.raises(ServiceError) as error:
        llm.parse_response(json.dumps(payload))
    assert error.value.code == 'invalid_llm_response'


def test_strict_format_not_sent_to_unrelated_providers(monkeypatch):
    monkeypatch.setenv('LLM_BASE_URL', 'https://provider.invalid/v1')
    assert 'response_format' not in llm.completion_options('openai/gpt-oss-120b', llm.provider_schema())


def test_provider_refusal_is_reported_without_exposing_its_text(local_groq):
    reply, _ = local_groq
    reply['refusal'] = 'private-provider-marker'
    with pytest.raises(ServiceError) as error:
        llm.analisar(CV_A, JOB, None, None)
    assert error.value.code == 'llm_refused'
    assert 'private-provider-marker' not in error.value.message
