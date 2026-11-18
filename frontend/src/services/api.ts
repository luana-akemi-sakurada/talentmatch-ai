import type { Analysis, Categories, Metrics } from '@/types'

export const API = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '').replace(/\/api$/, '')
export interface HealthStatus { status: string; model_loaded: boolean; model_type?: string }
async function request<T>(path: string, options: RequestInit = {}, acceptDegraded = false): Promise<T> {
  try {
    const response = await fetch(`${API}/api${path}`, { ...options, cache: 'no-store' })
    const body: unknown = await response.json().catch(() => null)
    if (acceptDegraded && response.status === 503 && body && typeof body === 'object' && 'status' in body && body.status === 'degraded' && 'model_loaded' in body && body.model_loaded === false) return body as T
    if (!response.ok) {
      const errorBody = body as {error?: {message?: string}} | null
      throw new Error(errorBody?.error?.message || `API respondeu HTTP ${response.status}.`)
    }
    if (body === null) throw new Error('A API não retornou JSON. Confira VITE_API_URL e o proxy /api do Vite.')
    return body as T
  } catch (error) {
    if (error instanceof TypeError) throw new Error('Falha de conexão com a API. Verifique o backend, a URL configurada e as permissões de CORS.')
    throw error
  }
}
export const api = {
  metrics: () => request<Metrics>('/models/metrics'),
  categories: () => request<Categories>('/models/categories'),
  health: async (): Promise<HealthStatus> => {
    const data = await request<HealthStatus>('/health', {}, true)
    if (!data || typeof data.model_loaded !== 'boolean' || typeof data.status !== 'string') throw new Error('Resposta de saúde inválida. Confira se a URL aponta para o backend TalentMatch.')
    return data
  },
  analyze: (body: FormData, signal: AbortSignal) => request<Analysis>('/analyze', { method: 'POST', body, signal }),
}
