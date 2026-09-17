import assert from 'node:assert/strict'
import { afterEach, mock, test } from 'node:test'

import { ApiError, apiRequest } from '../src/api/client.js'

afterEach(() => mock.restoreAll())

test('GET preserves pagination and query parameters without session cookies', async () => {
  const page = { count: 1, next: null, previous: null, results: [{ id: 7 }] }
  const fetch = mock.method(globalThis, 'fetch', async () =>
    Response.json(page),
  )

  assert.deepEqual(await apiRequest('/comments/?task=3&page=2'), page)
  const [url, options] = fetch.mock.calls[0].arguments
  assert.equal(url, '/api/comments/?task=3&page=2')
  assert.equal(options.method, 'GET')
  assert.equal(options.credentials, 'omit')
  assert.equal(options.headers.Authorization, undefined)
  assert.equal(options.headers['Content-Type'], undefined)
})

test('writes serialize JSON and use the supplied access token', async () => {
  const fetch = mock.method(globalThis, 'fetch', async () =>
    Response.json({ id: 1 }, { status: 201 }),
  )

  await apiRequest('/tasks/', {
    method: 'POST',
    data: { title: 'New task' },
    accessToken: 'test-access-token',
  })

  const [, options] = fetch.mock.calls[0].arguments
  assert.equal(options.headers.Authorization, 'Bearer test-access-token')
  assert.equal(options.headers['Content-Type'], 'application/json')
  assert.equal(options.body, JSON.stringify({ title: 'New task' }))
})

test('DELETE handles a 204 response without parsing JSON', async () => {
  mock.method(
    globalThis,
    'fetch',
    async () => new Response(null, { status: 204 }),
  )
  assert.equal(await apiRequest('/tasks/1/', { method: 'DELETE' }), null)
})

test('validation errors retain field details for forms', async () => {
  const details = { title: ['This field is required.'] }
  mock.method(globalThis, 'fetch', async () =>
    Response.json(details, { status: 400 }),
  )
  await assert.rejects(
    apiRequest('/tasks/', { method: 'POST', data: {} }),
    (error) => {
      assert.ok(error instanceof ApiError)
      assert.equal(error.status, 400)
      assert.deepEqual(error.details, details)
      return true
    },
  )
})

test('401 remains distinguishable for the authentication flow', async () => {
  mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: 'Token is expired' }, { status: 401 }),
  )
  await assert.rejects(apiRequest('/users/me/'), {
    name: 'ApiError',
    status: 401,
  })
})

test('HTML gateway errors become API errors without exposing HTML', async () => {
  mock.method(
    globalThis,
    'fetch',
    async () => new Response('<html>Bad gateway</html>', { status: 502 }),
  )
  await assert.rejects(apiRequest('/tasks/'), {
    name: 'ApiError',
    status: 502,
    details: null,
  })
})

test('an HTML page is never treated as successful API data', async () => {
  mock.method(
    globalThis,
    'fetch',
    async () => new Response('<html>Application</html>'),
  )
  await assert.rejects(apiRequest('/tasks/'), { name: 'ApiError', status: 200 })
})

test('invalid JSON becomes an API error', async () => {
  mock.method(
    globalThis,
    'fetch',
    async () =>
      new Response('{broken', {
        headers: { 'Content-Type': 'application/json' },
      }),
  )
  await assert.rejects(apiRequest('/tasks/'), { name: 'ApiError', status: 200 })
})

test('network failures have status zero', async () => {
  mock.method(globalThis, 'fetch', async () => {
    throw new TypeError('Failed to fetch')
  })
  await assert.rejects(apiRequest('/tasks/'), { name: 'ApiError', status: 0 })
})

test('request cancellation is preserved and the signal reaches fetch', async () => {
  const controller = new AbortController()
  controller.abort()
  const fetch = mock.method(globalThis, 'fetch', async () => {
    throw controller.signal.reason
  })

  await assert.rejects(apiRequest('/tasks/', { signal: controller.signal }), {
    name: 'AbortError',
  })
  assert.equal(fetch.mock.calls[0].arguments[1].signal, controller.signal)
})

test('cancellation while reading the response remains an AbortError', async () => {
  const response = Response.json({ id: 1 })
  mock.method(response, 'json', async () => {
    throw new DOMException('Aborted', 'AbortError')
  })
  mock.method(globalThis, 'fetch', async () => response)

  await assert.rejects(apiRequest('/users/me/'), { name: 'AbortError' })
})
