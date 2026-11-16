"""Literal passage regressions; SDK integration uses only an in-memory transport."""
import json

import httpx
import pytest
from openai import OpenAI

import llm
from backend.app.core.errors import ServiceError
from backend.app.services.grounding import passages, quote


@pytest.mark.parametrize('separator', [' ', '', '\n', '\r\n', '\r', '\n\n'])
def test_semicolon_is_part_of_previous_item(separator):
    text = f'Experiência em Python;{separator}Conhecimento em SQL.'
    assert passages(text) == {'Experiência em Python;', 'Conhecimento em SQL.'}
    quote('Experiência em Python;', passages(text))
    with pytest.raises(ServiceError, match='passagem completa'):
        quote('Experiência em Python', passages(text))


@pytest.mark.parametrize('newline', ['\n', '\r\n', '\r', '\n\n', '\r\n\r\n'])
def test_line_breaks_preserve_internal_punctuation(newline):
    text = f'  Experiência em Python, SQL e Java;  {newline}Desenvolvimento de APIs.{newline}Docker'
    assert passages(text) == {'Experiência em Python, SQL e Java;', 'Desenvolvimento de APIs.', 'Docker'}


@pytest.mark.parametrize('ending', ['.', '!', '?'])
def test_sentence_punctuation_is_preserved(ending):
    text = f'Experiência em Python{ending} Conhecimento em SQL.'
    assert passages(text) == {f'Experiência em Python{ending}', 'Conhecimento em SQL.'}
    quote(f'Experiência em Python{ending}', passages(text))
    with pytest.raises(ServiceError):
        quote('Experiência em Python', passages(text))


@pytest.mark.parametrize('evidence', [
    'Python',
    'Experiência em Python',
    'Experiência em Python.',
    'Experiência em Python, SQL e Java',
    'Experiência em Python, SQL e Java.',
    'Experiência em Python SQL e Java;',
    'Experiência em Python,  SQL e Java;',
    'Experiência em Python, SQL e AWS;',
    'Experiência em Python, SQL e Java; Conhecimento em Docker.',
])
def test_invented_clipped_repunctuated_or_joined_passages_are_rejected(evidence):
    with pytest.raises(ServiceError, match='passagem completa'):
        quote(evidence, passages('Experiência em Python, SQL e Java; Conhecimento em Docker.'))


def provider_draft(evidence, score=100):
    return {'habilidades': [{'habilidade': 'Python', 'evidencia': evidence}],
            'experiencia_profissional': [evidence], 'anos_experiencia': None,
            'evidencia_anos_experiencia': None,
            'requisitos_atendidos': [{'requisito': 'Python', 'evidencia': evidence}],
            'requisitos_sem_evidencia': [], 'nota_aderencia': score}


@pytest.fixture
def sdk_response(monkeypatch):
    """Exercise real SDK serialization without using configured credentials/network."""
    sent = []
    response = {}

    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={
            'id': 'synthetic', 'object': 'chat.completion', 'created': 0,
            'model': 'local-test', 'choices': [{'index': 0, 'finish_reason': 'stop',
                'message': {'role': 'assistant', 'content': json.dumps(response, ensure_ascii=False)}}]})

    with OpenAI(api_key='local-test', base_url='http://mock.invalid/v1', max_retries=0,
                http_client=httpx.Client(transport=httpx.MockTransport(handler))) as sdk:
        monkeypatch.setenv('LLM_API_KEY', 'local-test')
        monkeypatch.setenv('LLM_MODEL', 'local-test')
        monkeypatch.setattr(llm, '_client', lambda: sdk)
        yield response, sent


@pytest.mark.parametrize('evidence', [
    'Experiência em Python, SQL;',
    'Experiência em Python, SQL.',
    'Experiência em Python, SQL',
])
def test_sdk_accepts_complete_minimized_quotes_and_still_withholds_score(sdk_response, evidence):
    response, sent = sdk_response
    response.update(provider_draft(evidence))
    result = llm.analisar(f'Nome: Pessoa Fictícia\r\n{evidence}\r\nDesenvolvimento de APIs.',
                         'Python e SQL.', None, None)
    payload = json.loads(sent[0]['messages'][1]['content'])
    assert 'Pessoa Fictícia' not in payload['curriculo']
    assert evidence in passages(payload['curriculo'])
    assert result['habilidades'] == ['Python']
    assert result['requisitos_atendidos'][0]['evidencia'] == evidence
    assert result['experiencia_profissional'] == [evidence]
    assert result['nota_aderencia'] is None
    assert result['abstention_reason'] == 'score_not_validated'


@pytest.mark.parametrize('source,evidence', [
    ('Experiência em Python, SQL;', 'Experiência em Python, SQL'),
    ('Experiência em Python, SQL.', 'Experiência em Python, SQL'),
    ('Python, sem experiência profissional;', 'Python'),
    ('Python, sem experiência profissional;', 'Python, sem experiência profissional;'),
    ('Não tenho experiência em Python;', 'Não tenho experiência em Python;'),
    ('Experiência em SQL;', 'Experiência em Python;'),
])
def test_api_rejects_unsupported_quotes_without_losing_ml(client, sdk_response, source, evidence):
    response, sent = sdk_response
    response.update(provider_draft(evidence))
    result = client.post('/api/analyze', data={
        'mode': 'live', 'resume_text': source, 'job_description': 'Python e SQL.'})
    assert result.status_code == 200
    data = result.json()
    assert data['llm'] is None and data['llm_error'] == 'unsupported_evidence'
    assert data['ml']['status'] == 'predicted' and data['ml']['top_categories']
    assert len(sent) == 1


def test_api_semicolon_quote_preserves_abstention_without_evidence(client, sdk_response):
    response, _ = sdk_response
    response.update(provider_draft('Experiência em Python;'))
    response.update(habilidades=[], experiencia_profissional=[], requisitos_atendidos=[])
    result = client.post('/api/analyze', data={
        'mode': 'live', 'resume_text': 'Experiência em Python; Desenvolvimento de APIs.',
        'job_description': 'Python.'})
    data = result.json()
    assert result.status_code == 200 and data['llm_error'] is None
    assert data['llm']['nota_aderencia'] is None
    assert data['llm']['abstention_reason'] == 'insufficient_evidence'
