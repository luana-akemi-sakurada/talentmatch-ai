"""Provider returns references; only the server supplies literal quotations."""
from pydantic import BaseModel, ConfigDict, Field
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import GroundedLLMResponse, SkillEvidence, Evidence, ProfessionalProfile
from backend.app.services.grounding import ground, passages, contains


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class SkillReference(Closed):
    habilidade: str = Field(min_length=1, max_length=200)
    passagem_id: str = Field(min_length=1, max_length=40)


class RequirementReference(Closed):
    requisito: str = Field(min_length=1, max_length=500)
    vaga_passagem_id: str = Field(min_length=1, max_length=40)
    curriculo_passagem_id: str = Field(min_length=1, max_length=40)


class MissingReference(Closed):
    requisito: str = Field(min_length=1, max_length=500)
    vaga_passagem_id: str = Field(min_length=1, max_length=40)


class ProfileReference(Closed):
    descricao: str = Field(min_length=3, max_length=200)
    passagem_id: str = Field(min_length=1, max_length=40)


class ReferenceResponse(Closed):
    habilidades: list[SkillReference] = Field(max_length=50)
    experiencia_passagem_ids: list[str] = Field(max_length=30)
    requisitos_atendidos: list[RequirementReference] = Field(max_length=30)
    requisitos_sem_evidencia: list[MissingReference] = Field(max_length=30)
    perfil_profissional: ProfileReference | None


def catalogue(text: str, prefix: str):
    units = sorted(passages(text), key=lambda p: (text.find(p), p))
    # Never crop a quotation to fit a field: omit overlong units explicitly.
    accepted = [p for p in units if len(p) <= 1000]
    return {f'{prefix}_{i:04d}': p for i, p in enumerate(accepted, 1)}, len(units) - len(accepted)


def empty_draft():
    return GroundedLLMResponse(habilidades=[], experiencia_profissional=[], anos_experiencia=None, evidencia_anos_experiencia=None, requisitos_atendidos=[], requisitos_sem_evidencia=[], nota_aderencia=None, perfil_profissional=None)


def resolve_references(draft: ReferenceResponse, resume: str, job: str, resume_units: dict, job_units: dict, included: bool, omitted_units: int = 0):
    collected = empty_draft()
    rejected = 0
    def valid(candidate):
        nonlocal rejected
        try:
            return ground(candidate, resume, job, included)
        except ServiceError:
            rejected += 1
            return None
    for item in draft.habilidades:
        passage = resume_units.get(item.passagem_id)
        if passage is None or not contains(item.habilidade, passage):
            rejected += 1
            continue
        candidate = empty_draft()
        candidate.habilidades = [SkillEvidence(habilidade=item.habilidade, evidencia=passage)]
        if valid(candidate):
            collected.habilidades.extend(candidate.habilidades)
    for identifier in dict.fromkeys(draft.experiencia_passagem_ids):
        passage = resume_units.get(identifier)
        if passage is None:
            rejected += 1
            continue
        candidate = empty_draft()
        candidate.experiencia_profissional = [passage]
        if valid(candidate):
            collected.experiencia_profissional.append(passage)
    for item in draft.requisitos_atendidos:
        source = job_units.get(item.vaga_passagem_id)
        passage = resume_units.get(item.curriculo_passagem_id)
        if source is None or passage is None or not contains(item.requisito, source):
            rejected += 1
            continue
        candidate = empty_draft()
        candidate.habilidades = collected.habilidades
        candidate.requisitos_atendidos = [Evidence(requisito=item.requisito, evidencia=passage)]
        result = valid(candidate)
        if result:
            # Keep the verified labels returned by grounding, not broad qualifiers.
            collected.requisitos_atendidos.extend(result.requisitos_atendidos)
    dedup = {}
    for item in collected.requisitos_atendidos:
        dedup[(item.requisito, item.evidencia)] = item
    collected.requisitos_atendidos = list(dedup.values())[:30]
    for item in draft.requisitos_sem_evidencia:
        source = job_units.get(item.vaga_passagem_id)
        if source is None or not contains(item.requisito, source):
            rejected += 1
            continue
        candidate = collected.model_copy(deep=True)
        candidate.requisitos_sem_evidencia.append(item.requisito)
        if valid(candidate):
            collected.requisitos_sem_evidencia.append(item.requisito)
    if draft.perfil_profissional:
        item = draft.perfil_profissional
        passage = resume_units.get(item.passagem_id)
        if passage is not None:
            candidate = empty_draft()
            candidate.perfil_profissional = ProfessionalProfile(descricao=item.descricao, evidencia=passage)
            result = valid(candidate)
            if result and result.perfil_profissional:
                collected.perfil_profissional = result.perfil_profissional
            elif result:
                rejected += 1
        else:
            rejected += 1
    result = ground(collected, resume, job, included)
    note = f' Evidências recuperadas no servidor por IDs, sem citações livres do LLM. Itens rejeitados: {rejected}. Passagens acima do limite omitidas do catálogo: {omitted_units}.'
    result.justificativa = (result.justificativa + note)[:4000]
    if rejected or omitted_units:
        result.abstention_reason = 'partial_extraction'
    return result
