import { describe, expect, it, vi } from 'vitest'
import { PrismApi, ApiError } from './api'

describe('PrismApi', () => {
  it('loads the project names from the versioned API', async () => {
    const request = vi.fn().mockResolvedValue({ projects: ['North Tower'] })
    const api = new PrismApi(request)

    await expect(api.getProjects()).resolves.toEqual(['North Tower'])
    expect(request).toHaveBeenCalledWith('/api/v1/projects')
  })

  it('turns structured backend errors into a user-safe ApiError', async () => {
    const request = vi.fn().mockRejectedValue({
      status: 404,
      body: { error: { code: 'project_not_found', message: 'Unknown project' } },
    })
    const api = new PrismApi(request)

    await expect(api.getProjects()).rejects.toEqual(
      new ApiError('Unknown project', 404, 'project_not_found'),
    )
  })
})
