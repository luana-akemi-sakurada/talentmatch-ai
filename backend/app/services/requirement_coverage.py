"""Closed, explicitly delimited requirements; no semantic extraction or LLM score."""
import hashlib
import re
import unicodedata

from backend.app.schemas.analysis import LLMAnalysis, RequirementCoverage, RequirementCoverageItem
from backend.app.services.grounding import contains, nonpositive, passages


def identity(text: str) -> str:
    # Preserve accents, punctuation, numbers and qualifiers: no synonym/stem merging.
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


HEADER = re.compile(r'^(?:requisitos(?: obrigatórios| desejáveis| técnicos)?|obrigatórios|desejáveis|'
                    r'desejável|requirements|required|preferred)\s*:\s*(.*)$', re.I)
METADATA = re.compile(r'^(?:vaga|cargo|local|empresa|exemplo fictício[^:]*)\s*:', re.I)
BULLET = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s+(.+)$')
UNSUPPORTED = re.compile(r'\b(?:ou|or|não|not|no)\b|/|\b(?:exceto|unless|se|caso)\b', re.I)


def inventory(job: str) -> RequirementCoverage:
    """A complete list requires explicit headers and bullet/semicolon units.

    Each bullet or semicolon item is ONE requirement. Commas/AND inside it are
    components, all required together. Unknown prose cannot certify completeness.
    """
    items = {}
    reasons = []
    active = False
    empty_section = False
    for raw in re.split(r'\r\n|[\r\n]|(?<=[.!?])(?<!\d\.)\s+', job):
        line = raw.strip()
        if not line:
            continue
        header = HEADER.fullmatch(line)
        bullet = BULLET.fullmatch(line)
        if header:
            if empty_section:
                reasons.append('secao_sem_itens')
            active = True
            body = header.group(1)
            empty_section = not body.strip()
            units = body.split(';') if body else []
            # An inline comma/conjunction list has ambiguous grouping. Require
            # bullets or semicolons to certify its denominator, never guess it.
            if body and ';' not in body and re.search(r',(?!\d)|\s+(?:e|and|&)\s+', body, re.I):
                reasons.append('agrupamento_inline_ambiguo')
        elif bullet and active:
            body = bullet.group(1)
            units = body.split(';')
            if raw[:1].isspace():
                reasons.append('hierarquia_de_lista_ambigua')
        elif METADATA.match(line):
            active = False
            continue
        else:
            reasons.append('texto_da_vaga_nao_catalogado')
            active = False
            continue
        for unit in units:
            text = unit.strip()
            if text.endswith('.'):
                text = text[:-1].rstrip()
            if not text:
                continue
            empty_section = False
            key = identity(text)
            components = [part.strip() for part in re.split(r',(?!\d)|;|\s+(?:e|and|&)\s+', text, flags=re.I) if part.strip()]
            components = list({identity(part): part for part in components}.values())
            if key not in items:
                items[key] = RequirementCoverageItem(
                    id='req_' + hashlib.sha256(key.encode('utf-8')).hexdigest(), texto=text,
                    componentes=components, referencias_vaga=[line],
                    motivo='operador_nao_suportado' if UNSUPPORTED.search(text) else None)
            elif line not in items[key].referencias_vaga:
                items[key].referencias_vaga.append(line)
    if empty_section:
        reasons.append('secao_sem_itens')
    if not items:
        reasons.append('nenhum_requisito_catalogado')
    values = list(items.values())
    return RequirementCoverage(lista_completa=bool(values) and not reasons, requisitos=values,
                               total=len(values), indeterminados=len(values), motivos=list(dict.fromkeys(reasons)))


def evaluate(job: str, resume: str, analysis: LLMAnalysis | None, *,
             eligible: bool = True) -> RequirementCoverage:
    result = inventory(job)
    source = passages(resume)
    available = analysis is not None and eligible
    if not available:
        result.motivos.append('analise_contextual_indisponivel_ou_texto_incompleto')
    elif not (analysis.habilidades or analysis.experiencia_profissional or analysis.perfil_profissional
              or analysis.requisitos_atendidos):
        available = False
        result.motivos.append('sem_evidencias_contextuais_verificadas')
    if available:
        labels = {identity(label) for item in result.requisitos for label in [item.texto, *item.componentes]}
        returned = [pair.requisito for pair in analysis.requisitos_atendidos] + analysis.requisitos_sem_evidencia
        if any(identity(label) not in labels for label in returned):
            available = False
            result.motivos.append('avaliacao_fora_da_lista_fechada')
    for item in result.requisitos:
        if item.motivo or not available:
            item.motivo = item.motivo or 'avaliacao_indisponivel'
            continue
        states = []
        verified = []
        for component in item.componentes:
            aliases = {identity(component), identity(item.texto)}
            found = [pair for pair in analysis.requisitos_atendidos if identity(pair.requisito) in aliases]
            missing = any(identity(term) in aliases for term in analysis.requisitos_sem_evidencia)
            valid = [pair.evidencia for pair in found if pair.evidencia in source
                     and not nonpositive(pair.evidencia) and contains(component, pair.evidencia)
                     and contains(pair.requisito, job)]
            # An unrelated component of a composite may cite the same full label;
            # it only provides support where the component literally occurs.
            invalid = any(pair.evidencia not in source or nonpositive(pair.evidencia)
                          or (identity(pair.requisito) == identity(component)
                              and not contains(component, pair.evidencia)) for pair in found)
            positive_mention = any(contains(component, passage) and not nonpositive(passage) for passage in source)
            if invalid or (missing and (valid or positive_mention)):
                states.append('indeterminado')
            elif valid:
                states.append('evidencia_verificada')
                verified.extend(valid)
            elif missing:
                states.append('sem_evidencia_suficiente')
            else:
                states.append('indeterminado')
        item.evidencias = list(dict.fromkeys(verified))
        if 'indeterminado' in states or not states:
            item.motivo = 'avaliacao_omitida_incompleta_ou_inconsistente'
        elif 'sem_evidencia_suficiente' in states:
            item.estado = 'sem_evidencia_suficiente'
        else:
            item.estado = 'evidencia_verificada'
    result.com_evidencia = sum(item.estado == 'evidencia_verificada' for item in result.requisitos)
    result.sem_evidencia = sum(item.estado == 'sem_evidencia_suficiente' for item in result.requisitos)
    result.indeterminados = sum(item.estado == 'indeterminado' for item in result.requisitos)
    if result.lista_completa and result.total and not result.indeterminados and available:
        result.status = 'calculada'
        result.percentual = 100 * result.com_evidencia / result.total
    elif result.indeterminados:
        result.motivos.append('requisitos_com_avaliacao_indeterminada')
    return result
