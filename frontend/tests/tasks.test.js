import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  getAssigneeName,
  getPageNumber,
  getPriority,
  getStatus,
  getTaskPagePath,
  normalizeTaskPage,
} from '../src/pages/tasks.js'

test('pagination uses only positive whole page numbers', () => {
  assert.equal(getPageNumber('3'), 3)
  assert.equal(getPageNumber('0'), 1)
  assert.equal(getPageNumber('1.5'), 1)
  assert.equal(getPageNumber('text'), 1)
  assert.equal(getTaskPagePath(2), '/tasks/?page=2')
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

test('only paginated task responses are accepted', () => {
  const page = { count: 1, next: null, previous: null, results: [{ id: 1 }] }
  assert.equal(normalizeTaskPage(page), page)
  assert.throws(() => normalizeTaskPage({ results: [] }), /неизвестном формате/)
})
