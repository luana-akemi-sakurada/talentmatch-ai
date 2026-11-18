export interface ModelMetric { name: string; accuracy: number; f1_macro: number; precision_macro: number | null; recall_macro: number | null }
export interface Metrics {
  models: ModelMetric[]; selected_model: string; selection_criterion: string; source: string;
  dataset: { name: string; train_fraction: number; test_fraction: number; random_state: number; stratified: boolean; train_count: number | null; test_count: number | null; available_locally: boolean };
  limitations: string[];
}
export interface Categories { categories: string[]; counts: null; distribution_available: boolean; notice: string }
export interface Evidence { requisito: string; evidencia: string }
export interface ProfessionalProfile { descricao: string; evidencia: string }
export interface CompatibilityPrediction {
  disponivel: boolean;
  compatibilidade_prevista: string;
  rotulo_bruto: string;
  probabilidade_calibrada: number;
  nivel_confianca: string;
  margem_top1_top2: number;
  entropia_normalizada: number;
  alternativas: { compatibilidade: string; probabilidade_calibrada: number }[];
  score_estimado?: number;
  intervalo_80?: [number, number];
  cortes_faixas?: [number, number];
  faixas?: { faixa: string; probabilidade: number }[];
  sinais?: { sinal: string; contribuicao: number }[];
  habilidades_em_comum?: string[];
  habilidades_da_vaga_ausentes?: string[];
  n_habilidades_vaga?: number;
  similaridade_textual?: number | null;
  anos_curriculo?: number | null;
  anos_vaga?: number | null;
  formacao_curriculo?: string;
  formacao_vaga?: string;
}
export interface OODDetection {
  possivel_ood: boolean;
  similaridade_ao_centroide_mais_proximo: number;
  classe_centroide_mais_proxima: string;
  limiar_validado: number;
}
export interface RequisitoPriorizado {
  requisito: string;
  similaridade_cosseno: number;
}
export interface MLContext {
  disponivel: boolean;
  area_prevista: string;
  probabilidade_area_prevista: number;
  nivel_confianca: string;
  margem_top1_top2: number;
  entropia_normalizada: number;
  alternativas: { area: string; probabilidade_calibrada: number }[];
  deteccao_fora_distribuicao: OODDetection;
  compatibilidade_curriculo_vaga: CompatibilityPrediction;
  requisitos_priorizados: RequisitoPriorizado[];
  interpretacao: string;
}
export interface Analysis {
  cobertura_requisitos?: {status:'calculada'|'indeterminada'; lista_completa:boolean; com_evidencia:number; sem_evidencia:number; indeterminados:number; total:number; percentual:number|null; formula:string; motivos:string[]; requisitos:{id:string; texto:string; componentes:string[]; referencias_vaga:string[]; estado:'evidencia_verificada'|'sem_evidencia_suficiente'|'indeterminado'; evidencias:string[]; motivo:string|null}[]} | null;
  candidate_id: string; mode: 'live' | 'demo';
  ml: { predicted_area: string; model_name: string; top_categories: { category: string; probability: number }[]; status?: 'predicted' | 'abstained'; warnings?: string[]; coverage?: { active_features:number; analyzed_unigrams:number; known_unigrams:number; unknown_unigrams:number; unigram_coverage:number|null; zero_vector:boolean } | null };
  ml_context?: MLContext | null;
  llm: { resumo: string; habilidades: string[]; anos_experiencia: number | null; experiencia_profissional: string[]; nota_aderencia: number | null; requisitos_atendidos: Evidence[]; requisitos_sem_evidencia: string[]; pontos_fortes: string[]; lacunas: string[]; justificativa: string; abstention_reason?:string|null; ml_context_included?:boolean|null; perfil_profissional?: ProfessionalProfile|null } | null;
  warnings: string[]; llm_error: string | null; privacy: Record<string, number | boolean>;
}
