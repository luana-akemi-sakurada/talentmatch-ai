"""Only caller-defined codes/paths and numeric indices; never provider/input text."""
import logging
from backend.app.core.errors import ServiceError

logger = logging.getLogger('talentmatch.evidence')


def omitted_skill(index: int) -> None:
    logger.warning('evidence_item_omitted rule=skill_not_in_evidence field=habilidades.habilidade '
                   'source=curriculo category=support index=%s action=omit', index)


def failure(rule: str, field: str, source: str, category: str, message: str,
            index: int | None = None, code: str = 'unsupported_evidence') -> ServiceError:
    diagnostic = {'rule': rule, 'field': field, 'source': source, 'category': category}
    if index is not None:
        diagnostic['index'] = index
    logger.warning('evidence_failure rule=%s field=%s source=%s category=%s index=%s',
                   rule, field, source, category, index)
    return ServiceError(code, message, 502, diagnostic=diagnostic)
