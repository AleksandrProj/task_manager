import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  getAssigneeName,
  getPaginationPath,
  getPriority,
  getStatus,
  normalizeTaskPage,
} from '../src/pages/tasks.js'

test('pagination follows only links returned by the API', () => {
  assert.equal(
    getPaginationPath('http://127.0.0.1:8000/api/tasks/?page=2'),
    '/tasks/?page=2',
  )
  assert.equal(
    getPaginationPath('/api/comments/?task=3&page=2'),
    '/comments/?task=3&page=2',
  )
  assert.equal(getPaginationPath('https://example.com/tasks/?page=2'), null)
})

test('task values have Russian labels and safe fallbacks', () => {
  assert.deepEqual(getStatus('in_progress'), {
    label: 'В работе',
    tone: 'amber',
  })
  assert.deepEqual(getPriority('high'), { label: 'Высокий', tone: 'red' })
  assert.equal(getStatus('unknown').label, 'Не указан')
  assert.equal(getPriority('unknown').label, 'Не указан')
})

test('assignee name uses the user directory with a clear fallback', () => {
  const users = new Map([[4, 'maria']])
  assert.equal(getAssigneeName(4, users), 'maria')
  assert.equal(getAssigneeName(null, users), 'Не назначен')
  assert.equal(getAssigneeName(8, users), 'Пользователь №8')
})

test('only paginated task responses with server page links are accepted', () => {
  const page = {
    count: 1,
    next: null,
    previous: null,
    pages: [{ number: 1, url: '/api/tasks/?page=1', current: true }],
    results: [{ id: 1 }],
  }
  assert.equal(normalizeTaskPage(page), page)
  assert.throws(() => normalizeTaskPage({ results: [] }), /неизвестном формате/)
})
