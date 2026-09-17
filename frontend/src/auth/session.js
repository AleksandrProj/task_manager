import { ApiError, apiRequest } from '../api/client.js'

export const REFRESH_STORAGE_KEY = 'task-manager.refresh'
const EXPIRED_MESSAGE = 'Сессия завершилась. Войдите снова.'

// The API session is independent of React so requests and refresh share one state.
export function createAuthSession({ request = apiRequest, storage } = {}) {
  let snapshot = { status: 'loading', user: null, message: null }
  let accessToken = null
  let refreshToken = null
  let generation = 0
  let refreshPromise = null
  let restorePromise = null
  const listeners = new Set()

  function publish(status, user = null, message = null) {
    snapshot = { status, user, message }
    listeners.forEach((listener) => listener())
  }

  function readRefresh() {
    try {
      return storage?.getItem(REFRESH_STORAGE_KEY) || null
    } catch {
      return null
    }
  }

  function saveRefresh(value) {
    try {
      if (value) storage?.setItem(REFRESH_STORAGE_KEY, value)
      else storage?.removeItem(REFRESH_STORAGE_KEY)
    } catch {
      // Storage may be disabled. The current in-memory session still works.
    }
  }

  function checkGeneration(expected) {
    if (expected !== generation) {
      throw new DOMException('Session changed', 'AbortError')
    }
  }

  function logout(message = null) {
    generation += 1
    accessToken = null
    refreshToken = null
    refreshPromise = null
    restorePromise = null
    saveRefresh(null)
    publish('anonymous', null, message)
  }

  function refresh() {
    if (refreshPromise) return refreshPromise
    if (!refreshToken) return Promise.reject(new ApiError(EXPIRED_MESSAGE, 401))
    const expected = generation
    const pending = request('/auth/token/refresh/', {
      method: 'POST',
      data: { refresh: refreshToken },
    })
      .then((tokens) => {
        checkGeneration(expected)
        if (!tokens.access || typeof tokens.access !== 'string') {
          throw new ApiError('Не удалось обновить вход.', 502)
        }
        accessToken = tokens.access
        return accessToken
      })
      .catch((error) => {
        if (expected === generation && [400, 401].includes(error.status)) {
          logout(EXPIRED_MESSAGE)
        }
        throw error
      })
      .finally(() => {
        if (refreshPromise === pending) refreshPromise = null
      })
    refreshPromise = pending
    return pending
  }

  async function authorizedRequest(path, options = {}) {
    const expected = generation
    let token = accessToken || (await refresh())
    checkGeneration(expected)
    options.signal?.throwIfAborted()
    try {
      const result = await request(path, { ...options, accessToken: token })
      checkGeneration(expected)
      return result
    } catch (error) {
      checkGeneration(expected)
      if (error.status !== 401) throw error
    }

    // A concurrent request may already have refreshed this same access token.
    token = accessToken !== token ? accessToken : await refresh()
    checkGeneration(expected)
    options.signal?.throwIfAborted()
    try {
      const result = await request(path, { ...options, accessToken: token })
      checkGeneration(expected)
      return result
    } catch (error) {
      if (expected === generation && error.status === 401)
        logout(EXPIRED_MESSAGE)
      throw error
    }
  }

  async function login(username, password, { signal } = {}) {
    const expected = ++generation
    const tokens = await request('/auth/token/', {
      method: 'POST',
      data: { username, password },
      signal,
    })
    checkGeneration(expected)
    if (
      typeof tokens.access !== 'string' ||
      !tokens.access ||
      typeof tokens.refresh !== 'string' ||
      !tokens.refresh
    ) {
      throw new ApiError('Не удалось прочитать ответ сервера.', 502)
    }
    const user = await request('/users/me/', {
      accessToken: tokens.access,
      signal,
    })
    checkGeneration(expected)
    signal?.throwIfAborted()
    accessToken = tokens.access
    refreshToken = tokens.refresh
    saveRefresh(refreshToken)
    publish('authenticated', user)
  }

  function restore() {
    if (restorePromise) return restorePromise
    if (['authenticated', 'anonymous'].includes(snapshot.status))
      return Promise.resolve()
    refreshToken = refreshToken || readRefresh()
    if (!refreshToken) {
      publish('anonymous')
      return Promise.resolve()
    }
    const expected = generation
    publish('loading')
    const pending = authorizedRequest('/users/me/')
      .then((user) => {
        checkGeneration(expected)
        publish('authenticated', user)
      })
      .catch((error) => {
        if (expected !== generation || error.name === 'AbortError') return
        if (error.status === 401) logout(EXPIRED_MESSAGE)
        else
          publish(
            'error',
            null,
            'Не удалось проверить вход. Проверьте соединение и попробуйте ещё раз.',
          )
      })
      .finally(() => {
        if (restorePromise === pending) restorePromise = null
      })
    restorePromise = pending
    return pending
  }

  return {
    getSnapshot: () => snapshot,
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    login,
    logout,
    restore,
    request: authorizedRequest,
  }
}
