import pytest
from backend.app.core.errors import ServiceError
from backend.app.services.reference_grounding import ReferenceResponse, catalogue, resolve_references


def response(**changes):
    data = dict(habilidades=[], experiencia_passagem_ids=[], requisitos_atendidos=[], requisitos_sem_evidencia=[], perfil_profissional=None)
    data.update(changes)
    return ReferenceResponse.model_validate(data)


def test_valid_id_recovers_original_quote():
    resume = 'Desenvolvo APIs em Python.'
    job = 'Python.'
    cv, _ = catalogue(resume, 'cv')
    jd, _ = catalogue(job, 'job')
    draft = response(habilidades=[{'habilidade': 'Python', 'passagem_id': 'cv_0001'}], requisitos_atendidos=[{'requisito': 'Python', 'vaga_passagem_id': 'job_0001', 'curriculo_passagem_id': 'cv_0001'}])
    result = resolve_references(draft, resume, job, cv, jd, True)
    assert result.requisitos_atendidos[0].evidencia == resume
    assert result.nota_aderencia is None


def test_bad_id_does_not_destroy_good_skill():
    resume = 'Uso Python.'
    cv, _ = catalogue(resume, 'cv')
    jd, _ = catalogue('Python.', 'job')
    draft = response(habilidades=[{'habilidade': 'Python', 'passagem_id': 'cv_0001'}, {'habilidade': 'Java', 'passagem_id': 'cv_9999'}])
    result = resolve_references(draft, resume, 'Python.', cv, jd, True)
    assert result.habilidades == ['Python']
    assert result.abstention_reason == 'partial_extraction'


def test_negation_not_published():
    resume = 'Não tenho experiência com Python.'
    cv, _ = catalogue(resume, 'cv')
    jd, _ = catalogue('Python.', 'job')
    result = resolve_references(response(habilidades=[{'habilidade': 'Python', 'passagem_id': 'cv_0001'}]), resume, 'Python.', cv, jd, False)
    assert not result.habilidades
    assert result.abstention_reason == 'partial_extraction'


def test_job_id_cannot_be_used_as_resume_evidence():
    cv, _ = catalogue('Uso Python.', 'cv')
    jd, _ = catalogue('Java.', 'job')
    result = resolve_references(response(habilidades=[{'habilidade': 'Java', 'passagem_id': 'job_0001'}]), 'Uso Python.', 'Java.', cv, jd, False)
    assert not result.habilidades


def test_invalid_schema_returns_service_error_not_type_error():
    from llm import parse_response
    with pytest.raises(ServiceError):
        parse_response('{}', ReferenceResponse)


def test_catalogue_does_not_cut_long_passage():
    units, omitted = catalogue('x' * 1001, 'cv')
    assert units == {}
    assert omitted == 1
