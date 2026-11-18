"""Literal evidence validation. Not semantic entailment or truth detection."""
import re
import unicodedata
from backend.app.schemas.analysis import Evidence, GroundedLLMResponse, LLMAnalysis
from backend.app.services.evidence_diagnostics import failure, omitted_skill, logger
from backend.app.services.contextual import grounded_profile


def passages(text: str) -> set[str]:
    return {p.strip() for p in re.split(r'(?<=[.!?])\s+|(?<=;)\s*|[\r\n]+', text) if p.strip()}


def normalized(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))


def contains(term: str, text: str) -> bool:
    return bool(re.search(r'(?<!\w)' + re.escape(normalized(term)) + r'(?!\w)', normalized(text)))


def nonpositive(evidence: str) -> bool:
    text = normalized(evidence)
    return bool(re.search(r'\b(nao|sem|nunca|nenhum|nenhuma|not|never|without|lack|lacking)\b', text)
                or re.search(r'\bno\b[^.!?]*\b(experience|knowledge|skills?|proficiency)\b', text)
                or re.search(r'\b(pretendo|desejo|quero|would like|interested in|plan to|want to)\b', text))


def resolve_quote(evidence: str, source: set[str]) -> str:
    """Only whitespace normalization and unique bounded substring completion.
    Always return the original full source passage; never translate or paraphrase.
    Unresolved evidence is left unchanged so strict validation rejects it.
    """
    if evidence in source:
        return evidence
    fragment = ' '.join(evidence.split())
    if not fragment:
        return evidence
    pattern = r'(?<!\w)' + re.escape(fragment) + r'(?!\w)'
    candidates = [p for p in source if re.search(pattern, ' '.join(p.split()))]
    if len(candidates) == 1:
        return candidates[0]
    return evidence


def quote(evidence: str, source: set[str], field: str = 'evidencia', index: int | None = None):
    if evidence not in source:
        clipped = any(evidence in passage for passage in source)
        raise failure('incomplete_passage' if clipped else 'quote_not_found', field, 'curriculo', 'segmentation' if clipped else 'text', 'Abstenção: a evidência não corresponde a uma passagem completa e unívoca do currículo.', index)
    if nonpositive(evidence):
        raise failure('nonpositive_evidence', field, 'curriculo', 'support', 'Abstenção: a passagem contém negação, ausência ou intenção; não sustenta uma afirmação positiva automaticamente.', index)


NUMBER_WORDS = {'zero': 0, 'um': 1, 'uma': 1, 'one': 1, 'dois': 2, 'duas': 2, 'two': 2, 'tres': 3, 'three': 3, 'quatro': 4, 'four': 4, 'cinco': 5, 'five': 5, 'seis': 6, 'six': 6, 'sete': 7, 'seven': 7, 'oito': 8, 'eight': 8, 'nove': 9, 'nine': 9, 'dez': 10, 'ten': 10}


def duration_supported(years: float, evidence: str) -> bool:
    text = normalized(evidence)
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
        values.append(value if value is not None else float(match.group(1).replace(',', '.')))
    return bool(values) and set(values) == {years}


def grounded_duration(years: float | None, evidence: str | None, source: set[str]) -> tuple[float | None, str | None]:
    if years is None:
        return None, None
    if evidence:
        left = r'(?<![\w.,])' if evidence[0].isdigit() else r'(?<!\w)'
        right = r'(?![\w.,])' if evidence[-1].isdigit() else r'(?!\w)'
        candidates = [evidence] if evidence in source else sorted(p for p in source if re.search(left + re.escape(evidence) + right, p))
        if len(candidates) == 1 and not nonpositive(candidates[0]) and duration_supported(years, candidates[0]):
            return years, candidates[0]
    logger.warning('duration_omitted action=abstain_duration')
    return None, None


def ground(draft: GroundedLLMResponse, resume: str, job: str, context_included: bool) -> LLMAnalysis:
    source = passages(resume)
    draft = draft.model_copy(deep=True)
    resolved = 0
    for item in [*draft.habilidades, *draft.requisitos_atendidos]:
        full = resolve_quote(item.evidencia, source)
        resolved += int(full != item.evidencia)
        item.evidencia = full
    experience = [resolve_quote(item, source) for item in draft.experiencia_profissional]
    resolved += sum(a != b for a, b in zip(experience, draft.experiencia_profissional))
    draft.experiencia_profissional = experience
    if draft.perfil_profissional:
        full = resolve_quote(draft.perfil_profissional.evidencia, source)
        resolved += int(full != draft.perfil_profissional.evidencia)
        draft.perfil_profissional.evidencia = full
    skills = []
    omitted_count = 0
    for index, item in enumerate(draft.habilidades):
        quote(item.evidencia, source, 'habilidades.evidencia', index)
        if not contains(item.habilidade, item.evidencia):
            omitted_skill(index)
            omitted_count += 1
            continue
        if normalized(item.habilidade) not in {normalized(s) for s in skills}:
            skills.append(item.habilidade)
    for index, item in enumerate(draft.experiencia_profissional):
        quote(item, source, 'experiencia_profissional', index)
    experience = list(dict.fromkeys(draft.experiencia_profissional))
    years, years_evidence = grounded_duration(draft.anos_experiencia, draft.evidencia_anos_experiencia, source)
    requirements, seen, evidence_pairs, claimed = [], set(), set(), set()
    for index, item in enumerate(draft.requisitos_atendidos):
        quote(item.evidencia, source, 'requisitos_atendidos.evidencia', index)
        if not contains(item.requisito, job):
            raise failure('requirement_not_in_job', 'requisitos_atendidos.requisito', 'vaga', 'text', 'Abstenção: requisito sem referência literal na vaga.', index)
        labels = [item.requisito] if contains(item.requisito, item.evidencia) else [s for s in skills if contains(s, item.requisito) and contains(s, job) and contains(s, item.evidencia)]
        if not labels:
            raise failure('requirement_not_in_evidence', 'requisitos_atendidos.requisito', 'curriculo', 'support', 'Abstenção: não há competência literal verificada que sustente a associação.', index)
        claimed.add(normalized(item.requisito))
        for label in labels:
            pair = (normalized(label), item.evidencia)
            if pair not in evidence_pairs:
                if len(requirements) >= 30:
                    raise failure('verified_requirements_limit', 'requisitos_atendidos', 'response', 'structure', 'Abstenção: limite de associações verificadas excedido.', index)
                requirements.append(Evidence(requisito=label, evidencia=item.evidencia))
                seen.add(normalized(label))
                evidence_pairs.add(pair)
    missing = []
    for index, item in enumerate(draft.requisitos_sem_evidencia):
        if not contains(item, job):
            raise failure('missing_requirement_not_in_job', 'requisitos_sem_evidencia', 'vaga', 'text', 'Abstenção: requisito sem referência verificável à vaga.', index)
        if normalized(item) in seen or normalized(item) in claimed or any(contains(item, p) and not nonpositive(p) for p in source):
            raise failure('contradictory_requirement', 'requisitos_sem_evidencia', 'curriculo', 'support', 'Abstenção: requisitos contraditórios.', index)
        if normalized(item) not in {normalized(v) for v in missing}:
            missing.append(item)
    profile = grounded_profile(draft, resume, job)
    supported = bool(skills or experience or requirements or profile)
    summary = 'Abstenção: não há evidências verificáveis suficientes para descrever competências ou experiência.'
    if supported:
        summary = 'Menções verificadas no currículo: ' + (', '.join(skills) if skills else 'consulte as citações abaixo') + '.'
        if experience:
            summary += '\nExperiência citada: ' + ' '.join(experience)
    justification = (f'{len(requirements)} associações requisito-evidência com correspondência literal e {len(missing)} requisitos sem evidência informada. '
        'Associações confirmam apenas os termos verificados, não os demais qualificadores de frases compostas. '
        'A lista pode não cobrir todos os requisitos da vaga. Não há regra validada de completude e ponderação para nota de aderência. '
        'Citação literal não comprova competência, veracidade ou equivalência semântica. Revisão humana obrigatória.')
    if resolved:
        justification += f' {resolved} citações foram resolvidas para passagens completas e unívocas do texto original; negações e suporte foram verificados após a resolução.'
    if omitted_count:
        justification += f' {omitted_count} habilidades foram omitidas por nome sem suporte literal na citação.'
    if draft.anos_experiencia is not None and years_evidence is None:
        justification += ' Duração de experiência não estabelecida com evidência verificável.'
    return LLMAnalysis(resumo=summary[:3000], habilidades=skills, anos_experiencia=years, experiencia_profissional=experience, nota_aderencia=None, requisitos_atendidos=requirements, requisitos_sem_evidencia=missing, pontos_fortes=list(dict.fromkeys(i.evidencia for i in requirements)), lacunas=[f'Sem evidência verificada para: {i}.' for i in missing], justificativa=justification, perfil_profissional=profile, abstention_reason='score_not_validated' if supported and requirements else 'insufficient_evidence', ml_context_included=context_included)
