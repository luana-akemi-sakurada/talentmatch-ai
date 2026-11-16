"""Synthetic requirements; no provider calls or trained-model changes."""
import pytest

from backend.app.schemas.analysis import Evidence, LLMAnalysis
from backend.app.services.requirement_coverage import evaluate, inventory
from backend.tests.test_evidence_passages import sdk_response, provider_draft
import json
import llm


def analysis(found=(), missing=(), resume='Experiência em Python e SQL.'):
    return LLMAnalysis(resumo='Extração verificada.', habilidades=['Python'],
        experiencia_profissional=[resume], nota_aderencia=None,
        requisitos_atendidos=[Evidence(requisito=term, evidencia=quote) for term, quote in found],
        requisitos_sem_evidencia=list(missing), pontos_fortes=[], lacunas=[], justificativa='Sem nota.')


@pytest.mark.parametrize('found,missing,expected', [
    (['Python','SQL'], [], 100), (['Python'], ['SQL'], 50), ([], ['Python','SQL'], 0),
])
def test_full_partial_and_zero(found, missing, expected):
    resume = 'Experiência em ' + (' e '.join(found) if found else 'Enfermagem') + '.'
    result = evaluate('Requisitos:\n- Python\n- SQL', resume,
                      analysis([(term,resume) for term in found], missing, resume))
    assert result.percentual == expected
    assert result.total == 2
    assert result.com_evidencia == len(found)


def test_duplicates_and_stable_ids():
    first = inventory('Requisitos:\n- Python.\n- PYTHON\n- SQL')
    second = inventory('Requisitos: SQL; Python')
    assert first.total == 2 and first.lista_completa
    assert {item.id for item in first.requisitos} == {item.id for item in second.requisitos}
    assert len(first.requisitos[0].referencias_vaga) == 2
    assert inventory('Requisitos: Java; JavaScript; C++; C').total == 4


@pytest.mark.parametrize('missing,expected', [([], None), (['SQL'], 0)])
def test_compound_is_one_requirement_and_needs_all_components(missing, expected):
    resume = 'Experiência em Python.'
    result = evaluate('Requisitos:\n- Python e SQL', resume, analysis([('Python',resume)],missing))
    assert result.total == 1
    assert result.percentual == expected


def test_compound_full_and_multiple_evidence_not_counted_twice():
    resume = 'Experiência em Python. Projetos em SQL.'
    pairs = [('Python','Experiência em Python.'), ('SQL','Projetos em SQL.'),
             ('Python','Experiência em Python.')]
    result = evaluate('Requisitos:\n- Python e SQL', resume, analysis(pairs))
    assert result.percentual == 100 and result.com_evidencia == 1
    assert len(result.requisitos[0].evidencias) == 2


@pytest.mark.parametrize('job', [
    'Buscamos Python e SQL.', 'Requisitos: Python, SQL',
    'Requisitos:\n- Python\nTambém exigimos SQL.',
    'Requisitos:\n- Python ou SQL', 'Requisitos:\n  - Python', '',
    'Requisitos:\n- Python\nDesejáveis:', 'Requisitos:\n- Python não exigido',
])
def test_ambiguous_or_uncatalogued_job_abstains(job):
    result = evaluate(job,'Experiência em Python.', analysis([('Python','Experiência em Python.')]))
    assert result.percentual is None


@pytest.mark.parametrize('pairs,missing', [
    ([('Python','Python')],[]),  # clipped quote
    ([('Python','Experiência em AWS.')],[]),  # invented quote
    ([('Python','Experiência em SQL.')],[]),  # unrelated evidence
    ([('Python','Experiência em Python.')],['Python']),  # contradictory
    ([('Python','Experiência em Python.'),('AWS','Experiência em Python.')],[]),
    ([],[]),  # omitted evaluation must not shrink denominator
])
def test_inconsistent_incomplete_or_unsupported_evaluations(pairs,missing):
    result = evaluate('Requisitos:\n- Python', 'Experiência em Python. Experiência em SQL.', analysis(pairs,missing))
    assert result.percentual is None and result.total == 1


def test_no_contextual_evidence_or_failure_or_truncation_abstains():
    empty = analysis([],['Python'])
    empty.habilidades = []
    empty.experiencia_profissional = []
    for response, eligible in [(empty,True),(None,True),(analysis(),False)]:
        assert evaluate('Requisitos: Python','Texto insuficiente.',response,eligible=eligible).percentual is None


def test_literal_references_and_numbered_items():
    job = 'Vaga: Backend\r\nRequisitos:\r\n1. Python\r\n2. SQL'
    result = inventory(job)
    assert result.lista_completa and result.total == 2
    assert all(ref in job for item in result.requisitos for ref in item.referencias_vaga)


def test_omitted_extraction_is_detected_by_parser():
    result = evaluate('Requisitos:\n- Python\n- SQL', 'Experiência em Python.',
                      analysis([('Python','Experiência em Python.')]))
    assert result.com_evidencia == 1 and result.total == 2 and result.indeterminados == 1
    assert result.percentual is None


@pytest.mark.parametrize('missing,expected', [(['SQL'],50),([],None)])
def test_adapter_to_api_coverage_with_mocked_provider(client,sdk_response,missing,expected):
    response,sent = sdk_response
    response.update(provider_draft('Experiência em Python.',score=None))
    response['requisitos_sem_evidencia'] = missing
    result = client.post('/api/analyze',data={'resume_text':'Experiência em Python.',
        'job_description':'Requisitos:\n- Python\n- SQL','mode':'live'})
    assert result.status_code == 200
    data = result.json()
    assert data['llm_error'] is None
    assert data['llm']['nota_aderencia'] is None
    assert data['cobertura_requisitos']['percentual'] == expected
    payload = json.loads(sent[0]['messages'][1]['content'])
    assert len(payload['requisitos_identificados']) == 2
    assert 'TODOS os componentes' in llm.SYSTEM


def test_invalid_evidence_preserves_ml_and_abstains_coverage(client,sdk_response):
    response,_ = sdk_response
    response.update(provider_draft('Experiência em AWS.',score=None))
    data = client.post('/api/analyze',data={'resume_text':'Experiência em Python.',
        'job_description':'Requisitos: Python','mode':'live'}).json()
    assert data['ml'] and data['llm_error'] == 'unsupported_evidence'
    assert data['cobertura_requisitos']['percentual'] is None
