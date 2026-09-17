const API_BASE = '/api'

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

export async function apiRequest(
  path,
  { method = 'GET', data, accessToken, signal } = {},
) {
  const headers = { Accept: 'application/json' }
  if (data !== undefined) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: data === undefined ? undefined : JSON.stringify(data),
      credentials: 'omit',
      signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('Не удалось связаться с сервером. Попробуйте ещё раз.')
  }

  if (response.status === 204) return null

  let result = null
  if (response.headers.get('content-type')?.includes('application/json')) {
    try {
      result = await response.json()
    } catch (error) {
      if (error.name === 'AbortError') throw error
      throw new ApiError('Не удалось прочитать ответ сервера.', response.status)
    }
  }

  if (!response.ok) {
    const messages = {
      400: 'Проверьте введённые данные.',
      401: 'Необходимо войти в приложение.',
      403: 'Недостаточно прав для этого действия.',
      404: 'Запрошенные данные не найдены.',
    }
    throw new ApiError(
      messages[response.status] || 'Ошибка сервера. Попробуйте позже.',
      response.status,
      result,
    )
  }

  if (result === null) {
    throw new ApiError(
      'Сервер вернул ответ в неизвестном формате.',
      response.status,
    )
  }

  return result
}
