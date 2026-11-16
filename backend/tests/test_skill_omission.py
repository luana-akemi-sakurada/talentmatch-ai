"""Isolated name mismatches are omitted; all other grounding stays mandatory."""
import json
import logging

import pytest

import llm
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import GroundedLLMResponse
from backend.app.services.grounding import ground
from backend.tests.test_evidence_passages import sdk_response


TERMS = ['Java', 'Python', 'SQL', 'Git', 'Docker', 'JUnit']
QUOTES = [f'Utilizei {term} em projetos.' for term in TERMS]
CV = '\n'.join(QUOTES)
JOB = 'Java, Python, SQL, Git, Docker, JUnit e Testes unitários.'


def draft():
    return GroundedLLMResponse(
        habilidades=[{'habilidade': term, 'evidencia': evidence} for term, evidence in zip(TERMS, QUOTES)]
        + [{'habilidade': 'Testes unitários', 'evidencia': QUOTES[-1]}],
        experiencia_profissional=[], anos_experiencia=None, evidencia_anos_experiencia=None,
        requisitos_atendidos=[{'requisito': 'Java', 'evidencia': QUOTES[0]}],
        requisitos_sem_evidencia=[], nota_aderencia=100)


def test_one_of_seven_invalid_names_is_omitted_without_leaking_into_derived_fields(caplog):
    caplog.set_level(logging.WARNING, logger='talentmatch.evidence')
    result = ground(draft(), CV, JOB, False)
    assert result.habilidades == TERMS
    assert 'Testes unitários' not in result.model_dump_json()
    assert 'Itens de habilidades omitidos: 1.' in result.justificativa
    assert result.nota_aderencia is None
    assert 'index=6 action=omit' in caplog.text
    assert 'skill_not_in_evidence' in caplog.text
    assert 'Testes unitários' not in caplog.text
    assert all(passage not in caplog.text for passage in QUOTES)


@pytest.mark.parametrize('dependent_field,rule', [
    ('requisito', 'requirement_not_in_evidence'),
    ('experiencia', 'quote_not_found'),
    ('requisito_inventado', 'requirement_not_in_job'),
])
def test_unsupported_dependent_claims_still_abort_the_analysis(dependent_field, rule):
    payload = draft().model_dump()
    if dependent_field == 'requisito':
        payload['requisitos_atendidos'].append({'requisito': 'Testes unitários', 'evidencia': QUOTES[-1]})
    elif dependent_field == 'experiencia':
        payload['experiencia_profissional'] = ['Experiência com Testes unitários.']
    else:
        payload['requisitos_atendidos'].append({'requisito': 'AWS', 'evidencia': QUOTES[-1]})
    with pytest.raises(ServiceError) as error:
        ground(GroundedLLMResponse.model_validate(payload), CV, JOB, False)
    assert error.value.code == 'unsupported_evidence'
    assert error.value.diagnostic['rule'] == rule


def test_removed_skill_is_not_an_anchor_for_reworded_requirements():
    payload = draft().model_dump()
    payload['requisitos_atendidos'] = [{'requisito': 'Experiência com Testes unitários', 'evidencia': QUOTES[-1]}]
    with pytest.raises(ServiceError) as error:
        ground(GroundedLLMResponse.model_validate(payload), CV, 'Experiência com Testes unitários.', False)
    assert error.value.diagnostic['rule'] == 'requirement_not_in_evidence'


@pytest.mark.parametrize('bad_quote,rule', [
    ('Utilizei JUnit e AWS em projetos.', 'quote_not_found'),
    ('JUnit', 'incomplete_passage'),
    ('Não utilizei JUnit em projetos.', 'nonpositive_evidence'),
])
def test_name_mismatch_does_not_hide_invalid_or_negative_quote(bad_quote, rule):
    payload = draft().model_dump()
    payload['habilidades'][-1]['evidencia'] = bad_quote
    cv = CV + '\n' + bad_quote if rule == 'nonpositive_evidence' else CV
    with pytest.raises(ServiceError) as error:
        ground(GroundedLLMResponse.model_validate(payload), cv, JOB, False)
    assert error.value.diagnostic['rule'] == rule
    assert error.value.diagnostic['index'] == 6


def test_separately_proven_requirement_is_not_removed_just_because_skill_had_wrong_quote():
    payload = draft().model_dump()
    independent = 'Pratiquei Testes unitários em projetos.'
    payload['requisitos_atendidos'].append({'requisito': 'Testes unitários', 'evidencia': independent})
    result = ground(GroundedLLMResponse.model_validate(payload), CV + '\n' + independent, JOB, False)
    assert 'Testes unitários' not in result.habilidades
    assert result.requisitos_atendidos[-1].evidencia == independent
    assert result.requisitos_atendidos[-1].requisito == 'Testes unitários'
    assert result.nota_aderencia is None


def test_all_skills_omitted_means_explicit_abstention_and_no_score():
    payload = draft().model_dump()
    payload['habilidades'] = payload['habilidades'][-1:]
    payload['requisitos_atendidos'] = []
    result = ground(GroundedLLMResponse.model_validate(payload), CV, JOB, False)
    assert result.habilidades == [] and result.requisitos_atendidos == []
    assert result.pontos_fortes == [] and result.experiencia_profissional == []
    assert result.nota_aderencia is None and result.abstention_reason == 'insufficient_evidence'
    assert result.resumo.startswith('Abstenção:')


def test_valid_duplicate_after_invalid_item_is_checked_independently():
    payload = draft().model_dump()
    payload['habilidades'].insert(0, {'habilidade': 'Java', 'evidencia': QUOTES[-1]})
    result = ground(GroundedLLMResponse.model_validate(payload), CV, JOB, False)
    assert result.habilidades == TERMS
    assert 'Itens de habilidades omitidos: 2.' in result.justificativa


def test_sdk_api_publish_valid_items_after_one_omission(client, sdk_response):
    response, sent = sdk_response
    response.update(draft().model_dump())
    result = client.post('/api/analyze', data={'mode': 'live', 'resume_text': CV, 'job_description': JOB})
    assert result.status_code == 200 and len(sent) == 1
    data = result.json()
    assert data['llm_error'] is None and data['llm_diagnostic'] is None
    assert data['llm']['habilidades'] == TERMS
    assert data['llm']['nota_aderencia'] is None
    assert 'Testes unitários' not in json.dumps(data['llm'], ensure_ascii=False)
    assert data['ml']['top_categories']
    assert 'literalmente presente na respectiva habilidades[].evidencia' in sent[0]['messages'][0]['content']


def test_sdk_api_unsupported_dependency_remains_fatal(client, sdk_response):
    response, _ = sdk_response
    response.update(draft().model_dump())
    response['requisitos_atendidos'].append({'requisito': 'Testes unitários', 'evidencia': QUOTES[-1]})
    result = client.post('/api/analyze', data={'mode': 'live', 'resume_text': CV, 'job_description': JOB})
    data = result.json()
    assert result.status_code == 200 and data['llm'] is None
    assert data['llm_error'] == 'unsupported_evidence'
    assert data['llm_diagnostic']['rule'] == 'requirement_not_in_evidence'
    assert data['llm_diagnostic']['index'] == 1
    assert data['ml']['top_categories']


def test_provider_cannot_reintroduce_removed_skill_with_free_form_summary(sdk_response):
    response, _ = sdk_response
    response.update(draft().model_dump())
    response['resumo'] = 'Pessoa competente em Testes unitários.'
    with pytest.raises(ServiceError) as error:
        llm.analisar(CV, JOB, None, None)
    assert error.value.code == 'invalid_llm_response'
