import { API } from '@/services/api'
export interface Interval { point: number; low: number; high: number }
export interface TaskEvaluation {
  model: string; classes: string[];
  splits: Record<string, {rows: number; resume_groups: number; candidates: number; class_counts: Record<string, number>}>;
  evaluation: {
    metrics: {accuracy: Interval; f1_macro: Interval};
    bootstrap: {method: string; iterations: number; confidence: number; scope: string};
    probability_quality: Record<string, {log_loss: number; multiclass_brier: number}>;
    classification_report: Record<string, number | {precision: number; recall: number; 'f1-score': number; support: number}>;
    confusion_matrix: {labels: string[]; counts: number[][]};
  };
}
export interface Evaluation {
  schema_version: number; run_id: string; dataset: string; sklearn_version: string;
  split_strategy: string; area_candidates_excluded_ambiguous: number;
  tasks: {area: TaskEvaluation; compatibility: TaskEvaluation}; limitations: string[];
}
export async function getEvaluation(): Promise<Evaluation> {
  const response = await fetch(`${API}/api/models/metrics`, {cache: 'no-store'})
  const body = await response.json()
  if (!response.ok) throw new Error(body?.error?.message || `Avaliação indisponível (${response.status}).`)
  if (body.schema_version !== 2 || !body.tasks?.area || !body.tasks?.compatibility) throw new Error('A API ainda não oferece a avaliação atualizada. Reinicie o backend.')
  return body as Evaluation
}
