"""Fictitious inputs only; no provider requests or semantic equivalence inference."""
import json
import logging

import pytest

import llm
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import GroundedLLMResponse
from backend.app.services.grounding import ground
from backend.tests.test_evidence_passages import sdk_response


CV = 'Desenvolvi sistemas em Java.'
JOB = 'Experiência com Java.'


def draft(requirement='Experiência com Java', evidence=CV, skills=True):
    return GroundedLLMResponse(
        habilidades=[{'habilidade': 'Java', 'evidencia': CV}] if skills else [],
        experiencia_profissional=[], anos_experiencia=None, evidencia_anos_experiencia=None,
        requisitos_atendidos=[{'requisito': requirement, 'evidencia': evidence}],
        requisitos_sem_evidencia=[], nota_aderencia=100)


def test_different_wording_only_publishes_independently_verified_skill():
    result = ground(draft(), CV, JOB, False)
    assert [(item.requisito, item.evidencia) for item in result.requisitos_atendidos] == [('Java', CV)]
    assert result.nota_aderencia is None and result.abstention_reason == 'score_not_validated'


def test_unproven_qualifiers_are_not_published_as_demonstrated():
    requirement = 'Cinco anos de experiência avançada com Java e AWS'
    result = ground(draft(requirement), CV, requirement + '.', False)
    assert [item.requisito for item in result.requisitos_atendidos] == ['Java']
    assert result.anos_experiencia is None and result.nota_aderencia is None
    assert 'avançada' not in result.justificativa
    assert 'AWS' not in result.pontos_fortes[0]


@pytest.mark.parametrize('requirement,evidence,job,skills,rule,source', [
    ('AWS', CV, 'Java e AWS.', True, 'requirement_not_in_evidence', 'curriculo'),
    ('AWS', CV, JOB, True, 'requirement_not_in_job', 'vaga'),
    ('Conhecimento de Java', CV, JOB, True, 'requirement_not_in_job', 'vaga'),
    ('Experiência com Java', CV, JOB, False, 'requirement_not_in_evidence', 'curriculo'),
    ('Java', 'Desenvolvi sistemas em Java e AWS.', JOB, True, 'quote_not_found', 'curriculo'),
    ('Java', 'Java', JOB, True, 'incomplete_passage', 'curriculo'),
])
def test_failure_identifies_rule_field_source_and_index(requirement, evidence, job, skills, rule, source):
    with pytest.raises(ServiceError) as error:
        ground(draft(requirement, evidence, skills), CV, job, False)
    diagnostic = error.value.diagnostic
    assert diagnostic['rule'] == rule and diagnostic['source'] == source
    assert diagnostic['field'].startswith('requisitos_atendidos.') and diagnostic['index'] == 0
    assert error.value.code == 'unsupported_evidence'


def test_semantic_equivalence_is_not_automatic_proof():
    data = draft('Testes automatizados')
    data.habilidades = []
    data.requisitos_atendidos[0].evidencia = 'Escrevi testes JUnit.'
    with pytest.raises(ServiceError) as error:
        ground(data, 'Escrevi testes JUnit.', 'Testes automatizados.', False)
    assert error.value.diagnostic['rule'] == 'requirement_not_in_evidence'


@pytest.mark.parametrize('newline', ['\n', '\r\n', '\r'])
def test_case_accents_and_job_punctuation_do_not_require_equal_sentences(newline):
    data = draft('EXPERIENCIA com JAVA')
    result = ground(data, CV + newline + 'Conhecimento de SQL;',
                    'Experiência com Java; SQL, Git.', False)
    assert result.requisitos_atendidos[0].requisito == 'Java'


def test_quote_case_and_internal_line_breaks_are_still_literal():
    data = draft('Java', 'Desenvolvi sistemas em JAVA.')
    with pytest.raises(ServiceError) as error:
        ground(data, CV, JOB, False)
    assert error.value.diagnostic['rule'] == 'quote_not_found'
    with pytest.raises(ServiceError):
        ground(draft('Java'), 'Desenvolvi sistemas\nem Java.', JOB, False)


def test_multiple_valid_evidences_for_same_skill_are_preserved_and_exact_duplicates_removed():
    data = draft('Java')
    second = 'Utilizei Java em APIs;'
    payload = data.model_dump()
    payload['requisitos_atendidos'].extend([
        {'requisito': 'Experiência com Java', 'evidencia': second},
        {'requisito': 'Java', 'evidencia': CV}])
    # Validate the provider contract before testing grounding.
    data = GroundedLLMResponse.model_validate(payload)
    result = ground(data, CV + '\r\n' + second, JOB, False)
    assert [(item.requisito, item.evidencia) for item in result.requisitos_atendidos] == [('Java', CV), ('Java', second)]
    assert result.nota_aderencia is None


def test_invalid_second_evidence_abstains_atomically_with_original_index():
    data = draft('Java')
    payload = data.model_dump()
    payload['requisitos_atendidos'].append({'requisito': 'Java', 'evidencia': 'Inventei experiência em Java.'})
    with pytest.raises(ServiceError) as error:
        ground(GroundedLLMResponse.model_validate(payload), CV, JOB, False)
    assert error.value.diagnostic['index'] == 1
    assert error.value.diagnostic['field'] == 'requisitos_atendidos.evidencia'


def test_joined_evidence_passages_are_not_accepted_as_one_quote():
    text = CV + ' Utilizei SQL.'
    with pytest.raises(ServiceError):
        ground(draft('Java', text), text, JOB, False)


def test_missing_requirement_cannot_contradict_reduced_label():
    data = draft()
    data.requisitos_sem_evidencia = ['Java']
    with pytest.raises(ServiceError) as error:
        ground(data, CV, JOB, False)
    assert error.value.diagnostic['rule'] == 'contradictory_requirement'


def test_multiple_evidences_preserve_contract_limit_without_truncating_silently():
    payload = draft('Java').model_dump()
    quotes = [f'Projeto {index} utilizou Java.' for index in range(31)]
    payload['requisitos_atendidos'] = [
        {'requisito': 'Java', 'evidencia': passage} for passage in quotes[:30]]
    # A phrase with two independently verified skills can expand the last item.
    quotes[-1] = 'Projeto final utilizou Java e SQL.'
    payload['habilidades'].append({'habilidade': 'SQL', 'evidencia': quotes[-1]})
    payload['requisitos_atendidos'][-1] = {'requisito': 'Experiência com Java e SQL', 'evidencia': quotes[-1]}
    with pytest.raises(ServiceError) as error:
        ground(GroundedLLMResponse.model_validate(payload), CV + '\n' + '\n'.join(quotes),
               'Experiência com Java e SQL.', False)
    assert error.value.diagnostic['rule'] == 'verified_requirements_limit'


@pytest.mark.parametrize('content,rule,field', [
    ('not json', 'json_invalid', 'response'),
    ('{}', 'schema_invalid', 'habilidades'),
    ('[]', 'schema_invalid', 'response'),
])
def test_structure_diagnostics(content, rule, field):
    with pytest.raises(ServiceError) as error:
        llm.parse_response(content)
    assert error.value.diagnostic == {'rule': rule, 'field': field, 'source': 'response', 'category': 'structure'}


def test_logs_never_include_raw_quotes_unknown_properties_or_personal_data(caplog):
    caplog.set_level(logging.WARNING, logger='talentmatch.evidence')
    secret_marker = 'Pessoa Fictícia sensitive-marker@example.invalid'
    payload = draft().model_dump()
    payload[secret_marker] = secret_marker
    with pytest.raises(ServiceError) as error:
        llm.parse_response(json.dumps(payload))
    assert error.value.diagnostic['field'] == 'unknown'
    with pytest.raises(ServiceError):
        ground(draft('Java', secret_marker), CV, JOB, False)
    assert secret_marker not in caplog.text and CV not in caplog.text
    assert 'quote_not_found' in caplog.text and 'schema_invalid' in caplog.text


def test_sdk_and_api_success_keep_contract_and_no_score(client, sdk_response):
    response, sent = sdk_response
    response.update(draft().model_dump())
    result = client.post('/api/analyze', data={'mode': 'live', 'resume_text': CV, 'job_description': JOB})
    assert result.status_code == 200 and len(sent) == 1
    data = result.json()
    assert data['llm_error'] is None and data['llm_diagnostic'] is None
    assert data['llm']['requisitos_atendidos'] == [{'requisito': 'Java', 'evidencia': CV}]
    assert data['llm']['nota_aderencia'] is None


def test_sdk_and_api_failure_expose_safe_diagnostic_and_preserve_ml(client, sdk_response):
    response, _ = sdk_response
    response.update(draft('AWS').model_dump())
    result = client.post('/api/analyze', data={'mode': 'live', 'resume_text': CV, 'job_description': JOB})
    data = result.json()
    assert result.status_code == 200 and data['ml']['top_categories']
    assert data['llm'] is None and data['llm_error'] == 'unsupported_evidence'
    assert data['llm_diagnostic'] == {'rule': 'requirement_not_in_job',
        'field': 'requisitos_atendidos.requisito', 'source': 'vaga', 'category': 'text', 'index': 0}
