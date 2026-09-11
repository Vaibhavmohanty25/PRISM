import type {
  ActivityHistory,
  ActivityPredictiveSummary,
  ApiErrorPayload,
  ProjectPredictiveSummary,
  UploadResponse,
} from '../types/api'

type Requester = (path: string, init?: RequestInit) => Promise<unknown>

export class ApiError extends Error {
  constructor(message: string, readonly status: number, readonly code?: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function browserRequest(path: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(path, init)
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const payload = body as ApiErrorPayload | null
    throw { status: response.status, body: payload }
  }
  return body
}

function normalizeError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  const responseError = error as { status?: number; body?: ApiErrorPayload } | null
  return new ApiError(
    responseError?.body?.error?.message ?? 'The PRISM service could not complete that request.',
    responseError?.status ?? 0,
    responseError?.body?.error?.code,
  )
}

export class PrismApi {
  constructor(private readonly request: Requester = browserRequest) {}

  private async get<T>(path: string): Promise<T> {
    try { return await this.request(path) as T } catch (error) { throw normalizeError(error) }
  }

  async getProjects(): Promise<string[]> {
    const response = await this.get<{ projects: string[] }>('/api/v1/projects')
    return response.projects
  }

  getProjectPredictiveSummary(project: string) {
    return this.get<ProjectPredictiveSummary>(`/api/v1/projects/${encodeURIComponent(project)}/predictive-summary`)
  }

  getActivityPredictiveSummary(project: string, activity: string) {
    return this.get<ActivityPredictiveSummary>(`/api/v1/projects/${encodeURIComponent(project)}/activities/${encodeURIComponent(activity)}/predictive-summary`)
  }

  getActivityHistory(project: string, activity: string) {
    return this.get<ActivityHistory>(`/api/v1/projects/${encodeURIComponent(project)}/activities/${encodeURIComponent(activity)}/history`)
  }

  async uploadReport(file: File): Promise<UploadResponse> {
    const form = new FormData()
    form.append('file', file)
    try { return await this.request('/api/v1/upload', { method: 'POST', body: form }) as UploadResponse } catch (error) { throw normalizeError(error) }
  }
}

export const prismApi = new PrismApi()
