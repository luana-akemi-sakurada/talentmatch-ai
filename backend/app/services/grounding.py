"""Conservative literal grounding, not semantic entailment or truth detection."""
import re
import unicodedata
from backend.app.schemas.analysis import Evidence, GroundedLLMResponse, LLMAnalysis
from backend.app.services.evidence_diagnostics import failure, omitted_skill, logger
from backend.app.services.contextual import grounded_profile


def passages(text: str) -> set[str]:
    # Delimiters belong to the cited passage. Split AFTER semicolons, including
    # adjacent items without whitespace; commas remain inside the same passage.
    return {part.strip() for part in re.split(r'(?<=[.!?])\s+|(?<=;)\s*|[\r\n]+', text) if part.strip()}


def normalized(text: str) -> str:
    return ''.join(char for char in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(char))


def contains(term: str, text: str) -> bool:
    return bool(re.search(r'(?<!\w)' + re.escape(normalized(term)) + r'(?!\w)', normalized(text)))


def nonpositive(evidence: str) -> bool:
    text = normalized(evidence)
    return bool(re.search(r'\b(nao|sem|nunca|nenhum|nenhuma|not|never|without|lack|lacking)\b', text)
            or re.search(r'\bno\b[^.!?]*\b(experience|knowledge|skills?|proficiency)\b', text)
            or re.search(r'\b(pretendo|desejo|quero|would like|interested in|plan to|want to)\b', text))


def quote(evidence: str, source: set[str], field: str = 'evidencia', index: int | None = None):
    if evidence not in source:
        clipped = any(evidence in passage for passage in source)
        raise failure('incomplete_passage' if clipped else 'quote_not_found', field, 'curriculo',
                      'segmentation' if clipped else 'text',
                      'Abstenção: a evidência deve citar uma passagem completa do currículo enviado.', index)
    # Conservative: do not turn explicit negation/absence into a positive claim.
    if nonpositive(evidence):
        raise failure('nonpositive_evidence', field, 'curriculo', 'support',
                      'Abstenção: a passagem citada contém negação ou ausência; não sustenta uma afirmação positiva automaticamente.', index)


NUMBER_WORDS = {'zero': 0, 'um': 1, 'uma': 1, 'one': 1, 'dois': 2, 'duas': 2, 'two': 2,
                'tres': 3, 'three': 3, 'quatro': 4, 'four': 4, 'cinco': 5, 'five': 5,
                'seis': 6, 'six': 6, 'sete': 7, 'seven': 7, 'oito': 8, 'eight': 8,
                'nove': 9, 'nine': 9, 'dez': 10, 'ten': 10}


def duration_supported(years: float, evidence: str) -> bool:
    text = normalized(evidence)
    # No aggregation of jobs, dates, ranges or lower/upper bounds.
    if re.search(r'\b(mais de|pelo menos|ate|over|more than|at least|up to)\b', text):
        return False
    if (re.search(r'\b\w+\s*[-–—]\s*\w+\s+(anos?|years?)\b', text)
            or re.search(r'\b\w+\s+(?:a|to)\s+\w+\s+(anos?|years?)\b', text)
            or re.search(r'\b(entre|between)\b[^.!?]*\b(anos?|years?)\b', text)):
        return False
    pattern = r'(?<![\w.,])(\d+(?:[.,]\d+)?|' + '|'.join(NUMBER_WORDS) + r')\s+(?:anos? de experiencia|years? of experience)\b'
    values = []
    for match in re.finditer(pattern, text):
        value = NUMBER_WORDS.get(match.group(1))
        if value is None:
            value = float(match.group(1).replace(',', '.'))
        values.append(value)
    return bool(values) and set(values) == {years}


def grounded_duration(years: float | None, evidence: str | None,
                      source: set[str]) -> tuple[float | None, str | None]:
    """Resolve only an exact, unambiguous excerpt; otherwise abstain on duration."""
    if years is None:
        return None, None
    rule = 'duration_evidence_missing'
    if evidence:
        if evidence in source:
            candidates = [evidence]
        else:
            # No normalization or reconstruction. Numeric edges must not turn
            # '2 anos' into a match within '12 anos' or a decimal fragment.
            left = r'(?<![\w.,])' if evidence[0].isdigit() else r'(?<!\w)'
            right = r'(?![\w.,])' if evidence[-1].isdigit() else r'(?!\w)'
            pattern = left + re.escape(evidence) + right
            candidates = sorted(passage for passage in source if re.search(pattern, passage))
        rule = 'duration_quote_ambiguous' if len(candidates) > 1 else 'duration_quote_not_found'
        if len(candidates) == 1:
            passage = candidates[0]
            if nonpositive(passage):
                rule = 'nonpositive_duration_evidence'
            elif duration_supported(years, passage):
                if passage != evidence:
                    logger.info('duration_evidence_resolved field=evidencia_anos_experiencia source=curriculo')
                return years, passage
            else:
                rule = 'duration_not_supported'
    logger.warning('duration_omitted rule=%s field=evidencia_anos_experiencia '
                   'source=curriculo action=abstain_duration', rule)
    return None, None


def ground(draft: GroundedLLMResponse, resume: str, job: str, context_included: bool) -> LLMAnalysis:
    source = passages(resume)
    skills = []
    omitted_count = 0
    for index, item in enumerate(draft.habilidades):
        quote(item.evidencia, source, 'habilidades.evidencia', index)
        if not contains(item.habilidade, item.evidencia):
            # Only this name/quote mismatch is recoverable. The full quote must
            # already have passed validation; every other field is checked below.
            omitted_skill(index)
            omitted_count += 1
            continue
        if normalized(item.habilidade) not in {normalized(skill) for skill in skills}:
            skills.append(item.habilidade)
    for index, item in enumerate(draft.experiencia_profissional):
        quote(item, source, 'experiencia_profissional', index)
    experience = list(dict.fromkeys(draft.experiencia_profissional))
    years, years_evidence = grounded_duration(draft.anos_experiencia, draft.evidencia_anos_experiencia, source)

    requirements = []
    seen = set()
    evidence_pairs = set()
    claimed = set()
    for index, item in enumerate(draft.requisitos_atendidos):
        quote(item.evidencia, source, 'requisitos_atendidos.evidencia', index)
        if not contains(item.requisito, job):
            raise failure('requirement_not_in_job', 'requisitos_atendidos.requisito', 'vaga', 'text',
                          'Abstenção: o requisito informado não tem correspondência literal verificável na vaga.', index)
        # A job phrase need not be reproduced by the candidate. Only publish the
        # independently verified skill, never unsupported qualifiers in that phrase.
        labels = [item.requisito] if contains(item.requisito, item.evidencia) else [
            skill for skill in skills if contains(skill, item.requisito)
            and contains(skill, job) and contains(skill, item.evidencia)]
        if not labels:
            raise failure('requirement_not_in_evidence', 'requisitos_atendidos.requisito', 'curriculo', 'support',
                          'Abstenção: o requisito não aparece na citação e não há competência literal verificada que sustente a associação.', index)
        claimed.add(normalized(item.requisito))
        for label in labels:
            key = normalized(label)
            pair = (key, item.evidencia)
            if pair not in evidence_pairs:
                if len(requirements) >= 30:
                    raise failure('verified_requirements_limit', 'requisitos_atendidos', 'response', 'structure',
                                  'Abstenção: a extração excedeu o limite de associações verificadas.', index)
                requirements.append(Evidence(requisito=label, evidencia=item.evidencia))
                seen.add(key)
                evidence_pairs.add(pair)
    missing = []
    for index, item in enumerate(draft.requisitos_sem_evidencia):
        if not contains(item, job):
            raise failure('missing_requirement_not_in_job', 'requisitos_sem_evidencia', 'vaga', 'text',
                          'Abstenção: requisito sem evidência não tem referência verificável à vaga.', index)
        if (normalized(item) in seen or normalized(item) in claimed
                or any(contains(item, passage) and not nonpositive(passage) for passage in source)):
            raise failure('contradictory_requirement', 'requisitos_sem_evidencia', 'curriculo', 'support',
                          'Abstenção: requisitos contraditórios ou sem referência verificável à vaga.', index)
        if normalized(item) not in {normalized(value) for value in missing}:
            missing.append(item)

    profile = grounded_profile(draft, resume, job)
    supported = bool(skills or experience or requirements or profile)
    # No experiment currently validates completeness/weights of a generated
    # requirements list. Do not silently turn a provider score into a measured one.
    reason = 'score_not_validated' if supported and requirements else 'insufficient_evidence'
    if not supported:
        summary = 'Abstenção: não há evidências verificáveis suficientes para descrever competências ou experiência.'
    else:
        summary = 'Menções verificadas no currículo: ' + (', '.join(skills) if skills else 'consulte as citações abaixo') + '.'
        if experience:
            summary += '\nExperiência citada: ' + ' '.join(experience)
    justification = (f'{len(requirements)} associações requisito-evidência com correspondência literal e {len(missing)} requisitos sem evidência informada. '
                     'Quando a redação da vaga difere da citação, somente a competência literal verificada é apresentada; '
                     'os demais qualificadores do requisito não são confirmados por essa associação. '
                     'A lista pode não cobrir todos os requisitos da vaga. Abstenção de pontuação: '
                     'não há regra validada de completude e ponderação para justificar uma nota de aderência. '
                     'Citação literal não comprova competência, veracidade ou equivalência semântica. Revisão humana obrigatória.')
    if omitted_count:
        justification += (f' Itens de habilidades omitidos: {omitted_count}. O nome de cada item omitido não ocorre '
                          'literalmente na respectiva citação. Os demais campos foram validados separadamente.')
    if draft.anos_experiencia is not None and years_evidence is None:
        justification += ' Duração de experiência não estabelecida com evidência verificável; os demais campos foram validados independentemente.'
    return LLMAnalysis(resumo=summary[:3000], habilidades=skills, anos_experiencia=years,
                       experiencia_profissional=experience, nota_aderencia=None,
                       requisitos_atendidos=requirements, requisitos_sem_evidencia=missing,
                       pontos_fortes=list(dict.fromkeys(item.evidencia for item in requirements)),
                       lacunas=[f'Sem evidência verificada para: {item}.' for item in missing],
                       justificativa=justification,
                       perfil_profissional=profile,
                       abstention_reason=reason, ml_context_included=context_included)
