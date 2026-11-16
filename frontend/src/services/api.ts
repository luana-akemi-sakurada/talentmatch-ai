import type { Analysis, Categories, Comparison, Metrics } from '@/types'

export const API = import.meta.env.VITE_API_URL || ''
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    const response = await fetch(`${API}/api${path}`, { ...options, cache: 'no-store' })
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      throw new Error(body?.error?.message || `Serviço indisponível (${response.status}).`)
    }
    return await response.json() as T
  } catch (error) {
    if (error instanceof TypeError) throw new Error('Não foi possível conectar à API. Verifique se o backend está em execução.')
    throw error
  }
}
export const api = {
  metrics: () => request<Metrics>('/models/metrics'),
  categories: () => request<Categories>('/models/categories'),
  health: () => request<{status: string; model_loaded: boolean}>('/health'),
  analyze: (body: FormData, signal: AbortSignal) => request<Analysis>('/analyze', { method: 'POST', body, signal }),
  compare: (body: FormData, signal: AbortSignal) => request<Comparison>('/compare', { method: 'POST', body, signal }),
}
