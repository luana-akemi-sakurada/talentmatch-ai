"""Only duration may recover a literal excerpt or abstain without losing context."""
import json
import logging

import pytest

from backend.app.core.config import ROOT
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import GroundedLLMResponse
from backend.app.services.grounding import ground, grounded_duration, passages
from backend.tests.test_evidence_passages import sdk_response


SKILL = 'Desenvolvi APIs em Java.'
EXPERIENCE = 'Utilizei Git em projetos.'
DURATION = 'Possuo 2 anos de experiência em Java.'
BASE = SKILL + '\n' + EXPERIENCE
JOB = 'Java e AWS.'


def draft(years=2, evidence=DURATION):
    return GroundedLLMResponse(
        habilidades=[{'habilidade': 'Java', 'evidencia': SKILL}],
        experiencia_profissional=[EXPERIENCE], anos_experiencia=years,
        evidencia_anos_experiencia=evidence,
        requisitos_atendidos=[{'requisito': 'Java', 'evidencia': SKILL}],
        requisitos_sem_evidencia=['AWS'], nota_aderencia=None)


@pytest.mark.parametrize('evidence', [DURATION, '2 anos de experiência', 'anos de experiência em Java'])
def test_complete_and_unique_literal_excerpt_return_the_original_full_passage(evidence):
    assert grounded_duration(2, evidence, passages(BASE + '\n' + DURATION)) == (2, DURATION)
    value = ground(draft(evidence=evidence), BASE + '\n' + DURATION, JOB, False)
    assert value.anos_experiencia == 2 and value.habilidades == ['Java']


@pytest.mark.parametrize('years,evidence,resume', [
    (2, None, BASE + '\n' + DURATION),
    (2, SKILL, BASE),
    (2, '2 anos de experiência', BASE),
    (5, '5 anos de experiência', BASE + '\n' + DURATION),
    (5, DURATION, BASE + '\n' + DURATION),
    (2, 'Possuo dois anos de experiência em Java.', BASE + '\n' + DURATION),
    (2, '2 anos de experiência', BASE + '\nNão possuo 2 anos de experiência em Java.'),
    (2, '2 anos de experiência', BASE + '\nPretendo obter 2 anos de experiência em Java.'),
    (2, '2 anos de experiência', BASE + '\nPossuo 12 anos de experiência em Java.'),
    (2.5, '5 anos de experiência', BASE + '\nPossuo 2.5 anos de experiência em Java.'),
    (2, '24 meses de experiência', BASE + '\nPossuo 24 meses de experiência em Java.'),
    (3, '2 a 3 anos de experiência', BASE + '\nPossuo 2 a 3 anos de experiência em Java.'),
    (3, 'two to three years of experience', BASE + '\nI have two to three years of experience in Java.'),
    (2, '2 anos de experiência', BASE + '\nPossuo 2 anos de experiência em Java e 3 anos de experiência em SQL.'),
])
def test_unverified_or_contradictory_duration_is_null_and_preserves_other_verified_fields(years, evidence, resume):
    assert grounded_duration(years, evidence, passages(resume)) == (None, None)
    value = ground(draft(years, evidence), resume, JOB, False)
    assert value.anos_experiencia is None
    assert value.habilidades == ['Java'] and value.experiencia_profissional == [EXPERIENCE]
    assert value.requisitos_atendidos[0].model_dump() == {'requisito': 'Java', 'evidencia': SKILL}
    assert value.requisitos_sem_evidencia == ['AWS'] and value.pontos_fortes == [SKILL]
    assert value.nota_aderencia is None
    assert 'Duração de experiência não estabelecida' in value.justificativa
    # Unverified scalar years must not be turned into a generated assertion.
    assert value.resumo == 'Menções verificadas no currículo: Java.\nExperiência citada: ' + EXPERIENCE


def test_ambiguous_excerpt_is_not_resolved_by_picking_a_convenient_passage():
    resume = BASE + '\n' + DURATION + '\nPossuo 3 anos de experiência em SQL.'
    assert grounded_duration(2, 'anos de experiência', passages(resume)) == (None, None)


@pytest.mark.parametrize('newline', ['\n', '\r\n', '\r'])
def test_excerpt_resolution_uses_existing_passage_segmentation_without_rewriting(newline):
    passage = 'Desenvolvedora com dois anos de experiência em Java;'
    resume = BASE + newline + passage + 'Utilizei SQL.'
    assert grounded_duration(2, 'dois anos de experiência', passages(resume)) == (2, passage)


@pytest.mark.parametrize('years,evidence', [(2.5, 'Tenho 2,5 anos de experiência em Java.'),
                                          (2, 'Developer with two years of experience in Java.')])
def test_explicit_decimal_and_written_years_keep_existing_supported_formats(years, evidence):
    assert grounded_duration(years, evidence, {evidence}) == (years, evidence)


def test_no_duration_always_clears_the_evidence_pair():
    assert grounded_duration(None, DURATION, passages(BASE + '\n' + DURATION)) == (None, None)


def test_input_is_not_mutated_and_logs_do_not_contain_quotes_or_resume(caplog):
    caplog.set_level(logging.INFO, logger='talentmatch.evidence')
    payload = draft(7, 'Possuo 7 anos de experiência em Java.')
    before = payload.model_dump()
    assert ground(payload, BASE, JOB, False).anos_experiencia is None
    assert payload.model_dump() == before
    assert 'duration_omitted' in caplog.text and 'action=abstain_duration' in caplog.text
    assert 'Possuo 7 anos' not in caplog.text and SKILL not in caplog.text
    grounded_duration(2, '2 anos de experiência', passages(DURATION))
    assert 'duration_evidence_resolved' in caplog.text and DURATION not in caplog.text


@pytest.mark.parametrize('field', ['habilidades', 'experiencia_profissional', 'requisitos_atendidos'])
def test_duration_recovery_does_not_relax_other_citation_rules(field):
    payload = draft(evidence='2 anos de experiência').model_dump()
    if field == 'experiencia_profissional':
        payload[field] = ['Java']
    else:
        payload[field][0]['evidencia'] = 'Java'
    with pytest.raises(ServiceError) as error:
        ground(GroundedLLMResponse.model_validate(payload), BASE + '\n' + DURATION, JOB, False)
    assert error.value.code == 'unsupported_evidence'
    assert error.value.diagnostic['rule'] == 'incomplete_passage'


def test_sdk_api_resolves_original_fictional_resume_and_omits_invented_duration(client, sdk_response):
    data = json.loads((ROOT / 'scripts/model_cases.json').read_text(encoding='utf-8'))
    resume = next(case['text'] for case in data['cases'] if case['id'] == 'software-short-pt')
    first = resume.split('. ')[0] + '.'
    response, sent = sdk_response
    response.update(draft().model_dump())
    response.update(habilidades=[{'habilidade': 'Java', 'evidencia': first}],
                    experiencia_profissional=['Experiência com Git, testes unitários JUnit e Docker.'],
                    requisitos_atendidos=[{'requisito': 'Java', 'evidencia': first}],
                    evidencia_anos_experiencia=first)
    form = {'mode': 'live', 'resume_text': resume, 'job_description': data['job']}
    baseline = client.post('/api/analyze', data=form).json()
    assert baseline['llm_error'] is None and baseline['llm']['anos_experiencia'] == 2
    response['evidencia_anos_experiencia'] = 'dois anos de experiência'
    recovered = client.post('/api/analyze', data=form).json()
    assert recovered == baseline
    response.update(anos_experiencia=5, evidencia_anos_experiencia='cinco anos de experiência')
    omitted = client.post('/api/analyze', data=form).json()
    assert len(sent) == 3
    assert omitted['llm_error'] is None and omitted['llm_diagnostic'] is None
    assert omitted['llm']['anos_experiencia'] is None
    assert omitted['ml'] == baseline['ml']
    for key in ('habilidades', 'experiencia_profissional', 'requisitos_atendidos',
                'requisitos_sem_evidencia', 'pontos_fortes', 'lacunas', 'resumo'):
        assert omitted['llm'][key] == baseline['llm'][key]
