import assert from 'node:assert/strict'
import { mock, test } from 'node:test'
import { ApiError } from '../src/api/client.js'
import { createAuthSession, REFRESH_STORAGE_KEY } from '../src/auth/session.js'
import { getReturnPath } from '../src/auth/returnPath.js'

const user = { id: 7, username: 'test-user' }
const tokens = { access: 'test-access', refresh: 'test-refresh' }

function memoryStorage(refresh) {
  const values = new Map(refresh ? [[REFRESH_STORAGE_KEY, refresh]] : [])
  return {
    values,
    getItem: (key) => values.get(key),
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  }
}

function deferred() {
  let resolve, reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

test('without a saved refresh token, restore is anonymous and makes no request', async () => {
  const request = mock.fn()
  const session = createAuthSession({ request, storage: memoryStorage() })
  await session.restore()
  assert.equal(session.getSnapshot().status, 'anonymous')
  assert.equal(request.mock.callCount(), 0)
})

test('login loads the profile and persists only the refresh token', async () => {
  const storage = memoryStorage()
  const request = mock.fn(async (path) =>
    path === '/auth/token/' ? tokens : user,
  )
  const session = createAuthSession({ request, storage })
  const changed = mock.fn()
  const unsubscribe = session.subscribe(changed)
  await session.restore()
  await session.login('test-user', ' password with spaces ')

  assert.deepEqual(request.mock.calls[0].arguments[1].data, {
    username: 'test-user',
    password: ' password with spaces ',
  })
  assert.equal(request.mock.calls[1].arguments[1].accessToken, tokens.access)
  assert.deepEqual(session.getSnapshot(), {
    status: 'authenticated',
    user,
    message: null,
  })
  assert.deepEqual([...storage.values], [[REFRESH_STORAGE_KEY, tokens.refresh]])
  assert.equal(changed.mock.callCount(), 2)
  unsubscribe()
  session.logout()
  assert.equal(changed.mock.callCount(), 2)
  assert.equal(storage.values.size, 0)
})

test('wrong credentials do not persist tokens or authenticate the user', async () => {
  const storage = memoryStorage()
  const session = createAuthSession({
    storage,
    request: async () => {
      throw new ApiError('Invalid credentials', 401)
    },
  })
  await session.restore()
  await assert.rejects(session.login('wrong', 'wrong'), { status: 401 })
  assert.equal(session.getSnapshot().status, 'anonymous')
  assert.equal(storage.values.size, 0)
})

test('failed profile loading does not commit a partial login', async () => {
  const storage = memoryStorage()
  const session = createAuthSession({
    storage,
    request: async (path) => {
      if (path === '/auth/token/') return tokens
      throw new ApiError('Offline', 0)
    },
  })
  await session.restore()
  await assert.rejects(session.login('user', 'password'), { status: 0 })
  assert.equal(session.getSnapshot().user, null)
  assert.equal(storage.values.size, 0)
})

test('malformed login response is rejected', async () => {
  const session = createAuthSession({
    storage: memoryStorage(),
    request: async () => ({ access: tokens.access }),
  })
  await session.restore()
  await assert.rejects(session.login('user', 'password'), { status: 502 })
  assert.equal(session.getSnapshot().user, null)
})

test('restore refreshes access and loads the profile only once', async () => {
  const request = mock.fn(async (path) =>
    path === '/auth/token/refresh/' ? { access: 'restored-access' } : user,
  )
  const session = createAuthSession({
    request,
    storage: memoryStorage(tokens.refresh),
  })
  await Promise.all([session.restore(), session.restore()])
  assert.equal(request.mock.callCount(), 2)
  assert.deepEqual(request.mock.calls[0].arguments[1].data, {
    refresh: tokens.refresh,
  })
  assert.equal(
    request.mock.calls[1].arguments[1].accessToken,
    'restored-access',
  )
  assert.deepEqual(session.getSnapshot().user, user)
})

test('concurrent 401 responses share one refresh request', async () => {
  const refreshResponse = deferred()
  const request = mock.fn(async (path, options) => {
    if (path === '/auth/token/') return tokens
    if (path === '/users/me/') return user
    if (path === '/auth/token/refresh/') return refreshResponse.promise
    if (options.accessToken === tokens.access)
      throw new ApiError('Expired', 401)
    return { count: 0, results: [] }
  })
  const session = createAuthSession({ request, storage: memoryStorage() })
  await session.login('user', 'password')
  const responses = Promise.all([
    session.request('/tasks/'),
    session.request('/comments/'),
  ])
  refreshResponse.resolve({ access: 'new-access' })
  assert.equal((await responses).length, 2)
  assert.equal(
    request.mock.calls.filter(
      (call) => call.arguments[0] === '/auth/token/refresh/',
    ).length,
    1,
  )
  assert.equal(session.getSnapshot().status, 'authenticated')
})

test('a late 401 reuses the refreshed token instead of refreshing again', async () => {
  const late = deferred()
  let refreshCalls = 0
  const session = createAuthSession({
    storage: memoryStorage(),
    request: async (path, options) => {
      if (path === '/auth/token/') return tokens
      if (path === '/users/me/') return user
      if (path === '/auth/token/refresh/') {
        refreshCalls++
        return { access: 'new-access' }
      }
      if (options.accessToken === 'new-access') return 'success'
      if (path === '/comments/') return late.promise
      throw new ApiError('Expired', 401)
    },
  })
  await session.login('user', 'password')
  const pending = session.request('/comments/')
  assert.equal(await session.request('/tasks/'), 'success')
  late.reject(new ApiError('Expired', 401))
  assert.equal(await pending, 'success')
  assert.equal(refreshCalls, 1)
})

for (const status of [400, 401]) {
  test(`refresh rejected with ${status} clears the saved session`, async () => {
    const storage = memoryStorage(tokens.refresh)
    const session = createAuthSession({
      storage,
      request: async () => {
        throw new ApiError('Expired', status)
      },
    })
    await session.restore()
    assert.equal(session.getSnapshot().status, 'anonymous')
    assert.equal(
      session.getSnapshot().message,
      'Сессия завершилась. Войдите снова.',
    )
    assert.equal(storage.values.size, 0)
  })
}

test('network failure during restore keeps refresh and allows retry', async () => {
  const storage = memoryStorage(tokens.refresh)
  let offline = true
  const session = createAuthSession({
    storage,
    request: async (path) => {
      if (offline) throw new ApiError('Offline', 0)
      return path === '/auth/token/refresh/' ? { access: 'new-access' } : user
    },
  })
  await session.restore()
  assert.equal(session.getSnapshot().status, 'error')
  assert.equal(storage.getItem(REFRESH_STORAGE_KEY), tokens.refresh)
  offline = false
  await session.restore()
  assert.equal(session.getSnapshot().status, 'authenticated')
})

test('403 does not refresh tokens or sign the user out', async () => {
  const request = mock.fn(async (path) => {
    if (path === '/auth/token/') return tokens
    if (path === '/users/me/') return user
    throw new ApiError('Forbidden', 403)
  })
  const session = createAuthSession({ request, storage: memoryStorage() })
  await session.login('user', 'password')
  await assert.rejects(session.request('/tasks/1/'), { status: 403 })
  assert.equal(session.getSnapshot().status, 'authenticated')
  assert.equal(request.mock.callCount(), 3)
})

test('a second 401 signs out after a single retry, without a refresh loop', async () => {
  const storage = memoryStorage()
  const request = mock.fn(async (path) => {
    if (path === '/auth/token/') return tokens
    if (path === '/users/me/') return user
    if (path === '/auth/token/refresh/') return { access: 'new-access' }
    throw new ApiError('Unauthorized', 401)
  })
  const session = createAuthSession({ request, storage })
  await session.login('user', 'password')
  await assert.rejects(session.request('/tasks/'), { status: 401 })
  assert.equal(request.mock.callCount(), 5)
  assert.equal(session.getSnapshot().status, 'anonymous')
  assert.equal(storage.values.size, 0)
})

test('logging out while refresh is pending cannot restore the session', async () => {
  const refreshResponse = deferred()
  const storage = memoryStorage(tokens.refresh)
  const session = createAuthSession({
    storage,
    request: () => refreshResponse.promise,
  })
  const restoring = session.restore()
  session.logout()
  refreshResponse.resolve({ access: 'late-access' })
  await restoring
  assert.equal(session.getSnapshot().status, 'anonymous')
  assert.equal(storage.values.size, 0)
})

test('logging out while the login profile is pending discards the login result', async () => {
  const profile = deferred()
  const storage = memoryStorage()
  const session = createAuthSession({
    storage,
    request: async (path) =>
      path === '/auth/token/' ? tokens : profile.promise,
  })
  const loggingIn = session.login('user', 'password')
  await Promise.resolve()
  session.logout()
  profile.resolve(user)
  await assert.rejects(loggingIn, { name: 'AbortError' })
  assert.equal(session.getSnapshot().status, 'anonymous')
  assert.equal(storage.values.size, 0)
})

test('logging out discards a successful response from the previous session', async () => {
  const response = deferred()
  const session = createAuthSession({
    storage: memoryStorage(),
    request: async (path) => {
      if (path === '/auth/token/') return tokens
      if (path === '/users/me/') return user
      return response.promise
    },
  })
  await session.login('user', 'password')
  const pending = session.request('/tasks/')
  session.logout()
  response.resolve({ results: [{ id: 1 }] })
  await assert.rejects(pending, { name: 'AbortError' })
})

test('disabled browser storage still permits in-memory login and logout', async () => {
  const storage = {
    getItem() {
      throw new Error('Storage disabled')
    },
    setItem() {
      throw new Error('Storage disabled')
    },
    removeItem() {
      throw new Error('Storage disabled')
    },
  }
  const session = createAuthSession({
    storage,
    request: async (path) => (path === '/auth/token/' ? tokens : user),
  })
  await session.restore()
  await session.login('user', 'password')
  assert.equal(session.getSnapshot().status, 'authenticated')
  session.logout()
  assert.equal(session.getSnapshot().status, 'anonymous')
})

test('an aborted login does not persist a session', async () => {
  const controller = new AbortController()
  const storage = memoryStorage()
  const session = createAuthSession({
    storage,
    request: async (path) => {
      if (path === '/auth/token/') return tokens
      controller.abort()
      return user
    },
  })
  await assert.rejects(
    session.login('user', 'password', { signal: controller.signal }),
    { name: 'AbortError' },
  )
  assert.equal(storage.values.size, 0)
})

test('return path accepts task pages and rejects external or unexpected destinations', () => {
  assert.equal(
    getReturnPath('/tasks/123/edit?tab=details'),
    '/tasks/123/edit?tab=details',
  )
  for (const path of [
    '//evil.example',
    'https://evil.example',
    '/login',
    '/tasks-elsewhere',
    null,
    {},
  ]) {
    assert.equal(getReturnPath(path), '/tasks')
  }
})
