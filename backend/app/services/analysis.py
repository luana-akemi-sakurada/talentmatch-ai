import logging
import re
from typing import Literal
from llm import analisar
from backend.app.core.config import MAX_JOB_CHARS, MAX_LLM_CHARS
from backend.app.core.errors import ServiceError
from backend.app.schemas.analysis import AnalysisResponse, Evidence, LLMAnalysis
from backend.app.services.classifier import predict
from backend.app.services.files import validate_text
from backend.app.services.privacy import minimize
from backend.app.services.requirement_coverage import evaluate

logger = logging.getLogger('talentmatch.analysis')


def demo_analysis(resume: str, job: str) -> LLMAnalysis:
    """Explicitly synthetic illustration; never impersonates a live LLM."""
    vocabulary = ['Python', 'SQL', 'Excel', 'Power BI', 'Java', 'React', 'TypeScript',
                  'Docker', 'AWS', 'pandas', 'Git', 'comunicação', 'liderança']
    has = lambda term, text: bool(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, re.I))
    skills = [term for term in vocabulary if has(term, resume)]
    required = [term for term in vocabulary if has(term, job)]
    evidence = []
    for term in required:
        if has(term, resume):
            match = re.search(re.escape(term), resume, re.I)
            requirement = re.search(re.escape(term), job, re.I)
            evidence.append(Evidence(requisito=requirement.group(), evidencia=match.group()))
    missing = [term for term in required if not has(term, resume)]
    return LLMAnalysis(
        resumo='DEMONSTRAÇÃO SIMULADA: correspondência literal de um vocabulário limitado; não houve chamada a um LLM.',
        habilidades=skills, anos_experiencia=None, experiencia_profissional=[],
        nota_aderencia=round(100 * len(evidence) / len(required)) if required else 0,
        requisitos_atendidos=evidence, requisitos_sem_evidencia=missing,
        pontos_fortes=[f'Menção literal a {item.requisito}.' for item in evidence],
        lacunas=[f'{term}: sem menção literal localizada nesta simulação.' for term in missing],
        justificativa='Indicador ilustrativo = termos da vaga encontrados / termos reconhecidos na vaga. '
        'Se nenhum termo for reconhecido, o indicador é zero e não é interpretável. '
        'Não avalia experiência, contexto ou competência. O classificador ML acima usa o modelo real.',
    )


def analyze(resume: str, job: str, mode: Literal['live', 'demo'], candidate_id: str) -> AnalysisResponse:
    resume = validate_text(resume)
    if not job.strip() or len(job) > MAX_JOB_CHARS:
        raise ServiceError('invalid_job', f'Informe uma vaga entre 1 e {MAX_JOB_CHARS} caracteres.')
    safe_resume, resume_count = minimize(resume, resume=True)
    safe_job, job_count = minimize(job)
    ml = predict(safe_resume)
    warnings = [*ml.warnings, 'Indicador heurístico, sem valor de probabilidade ou decisão de contratação.',
                'A minimização automática pode deixar dados pessoais no texto livre; revise o documento antes de enviar.',
                'Modelo treinado em inglês; desempenho em português não validado.']
    if len(safe_resume) > MAX_LLM_CHARS:
        warnings.append(f'A análise contextual usa somente os primeiros {MAX_LLM_CHARS} caracteres minimizados.')
    error = None
    diagnostic = None
    result = None
    if mode == 'demo':
        result = demo_analysis(safe_resume[:MAX_LLM_CHARS], safe_job)
        warnings.insert(0, 'RESPOSTA SIMULADA. Apenas a classificação ML utiliza o modelo treinado real.')
    else:
        try:
            result = LLMAnalysis.model_validate(analisar(safe_resume, safe_job,
                ml.predicted_area if ml.status == 'predicted' else None,
                ml.top_categories[0].probability if ml.top_categories else None))
            if result.abstention_reason:
                warnings.append('Abstenção de pontuação: evidências textuais são exibidas quando verificáveis, '
                                'mas nenhuma nota LLM é publicada sem método de pontuação validado. Não significa aderência zero.')
        except ServiceError as exc:
            logger.warning('llm_failure code=%s', exc.code)
            error = exc.code
            diagnostic = exc.diagnostic
            warnings.append(exc.message)
    return AnalysisResponse(candidate_id=candidate_id, mode=mode, ml=ml, llm=result,
                            cobertura_requisitos=evaluate(safe_job, safe_resume[:MAX_LLM_CHARS], result,
                                eligible=mode == 'live' and len(safe_resume) <= MAX_LLM_CHARS),
                            llm_error=error, llm_diagnostic=diagnostic, warnings=warnings,
                            privacy={'minimized': True, 'resume_redactions': resume_count,
                                     'job_redactions': job_count, 'stored_permanently': False})
