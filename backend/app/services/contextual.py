"""Validate the optional, literal professional designation."""
from backend.app.schemas.analysis import GroundedLLMResponse
from backend.app.services.evidence_diagnostics import logger


def grounded_profile(draft: GroundedLLMResponse, resume: str, job: str):
    # Imported here to keep grounding's extraction helpers as the shared rules.
    from backend.app.services.grounding import contains, nonpositive, passages

    profile = draft.perfil_profissional
    if profile and (profile.evidencia not in passages(resume)
                    or nonpositive(profile.evidencia)
                    or not contains(profile.descricao, profile.evidencia)):
        logger.warning('context_block_omitted block=perfil_profissional rule=profile_not_grounded')
        profile = None

    return profile
