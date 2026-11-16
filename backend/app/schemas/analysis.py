from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Evidence(StrictModel):
    requisito: str = Field(min_length=1, max_length=500)
    evidencia: str = Field(min_length=1, max_length=1000)


class SkillEvidence(StrictModel):
    habilidade: str = Field(min_length=1, max_length=200)
    evidencia: str = Field(min_length=1, max_length=1000)


class ProfessionalProfile(StrictModel):
    descricao: str = Field(min_length=3, max_length=200)
    evidencia: str = Field(min_length=1, max_length=1000)


class GroundedLLMResponse(StrictModel):
    """Provider-only extraction contract. No free-form claims are published."""
    habilidades: list[SkillEvidence] = Field(max_length=50)
    experiencia_profissional: list[str] = Field(max_length=30)
    anos_experiencia: float | None = Field(ge=0, le=80, strict=True)
    evidencia_anos_experiencia: str | None = Field(max_length=1000)
    requisitos_atendidos: list[Evidence] = Field(max_length=30)
    requisitos_sem_evidencia: list[str] = Field(max_length=30)
    # Accepted for detecting unsupported numerical conclusions, never published.
    nota_aderencia: int | None = Field(default=None, ge=0, le=100, strict=True)
    perfil_profissional: ProfessionalProfile | None = None


class LLMAnalysis(StrictModel):
    resumo: str = Field(min_length=1, max_length=3000)
    habilidades: list[str] = Field(max_length=50)
    anos_experiencia: float | None = Field(default=None, ge=0, le=80)
    experiencia_profissional: list[str] = Field(default_factory=list, max_length=30)
    nota_aderencia: int | None = Field(ge=0, le=100, strict=True)
    requisitos_atendidos: list[Evidence] = Field(default_factory=list, max_length=30)
    requisitos_sem_evidencia: list[str] = Field(default_factory=list, max_length=30)
    pontos_fortes: list[str] = Field(max_length=30)
    lacunas: list[str] = Field(max_length=30)
    justificativa: str = Field(min_length=1, max_length=4000)
    abstention_reason: str | None = None
    ml_context_included: bool | None = None
    perfil_profissional: ProfessionalProfile | None = None


class CategoryProbability(StrictModel):
    category: str
    probability: float = Field(ge=0, le=1)


class MLCoverage(StrictModel):
    active_features: int = Field(ge=0)
    analyzed_unigrams: int = Field(ge=0)
    known_unigrams: int = Field(ge=0)
    unknown_unigrams: int = Field(ge=0)
    unigram_coverage: float | None = Field(ge=0, le=1)
    zero_vector: bool


class MLResult(StrictModel):
    predicted_area: str
    model_name: str
    top_categories: list[CategoryProbability]
    status: Literal['predicted', 'abstained'] = 'predicted'
    coverage: MLCoverage | None = None
    warnings: list[str] = Field(default_factory=list)


class RequirementCoverageItem(StrictModel):
    id: str
    texto: str
    componentes: list[str]
    referencias_vaga: list[str]
    estado: Literal['evidencia_verificada', 'sem_evidencia_suficiente', 'indeterminado'] = 'indeterminado'
    evidencias: list[str] = Field(default_factory=list)
    motivo: str | None = None


class RequirementCoverage(StrictModel):
    status: Literal['calculada', 'indeterminada'] = 'indeterminada'
    lista_completa: bool = False
    requisitos: list[RequirementCoverageItem] = Field(default_factory=list)
    com_evidencia: int = 0
    sem_evidencia: int = 0
    indeterminados: int = 0
    total: int = 0
    percentual: float | None = None
    motivos: list[str] = Field(default_factory=list)
    formula: str = 'requisitos distintos com evidências verificadas / requisitos distintos avaliados × 100'


class AnalysisResponse(StrictModel):
    candidate_id: str
    mode: Literal['live', 'demo']
    ml: MLResult
    llm: LLMAnalysis | None
    warnings: list[str]
    llm_error: str | None = None
    llm_diagnostic: dict[str, str | int] | None = None
    cobertura_requisitos: RequirementCoverage | None = None
    privacy: dict[str, int | bool]


class ComparisonResponse(StrictModel):
    results: list[AnalysisResponse]
    failures: list[dict[str, str]]
    notice: str = 'Ordem de envio preservada. Não há ranking nem rejeição automática.'
