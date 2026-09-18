const statuses = {
  new: { label: 'Новая', tone: 'blue' },
  in_progress: { label: 'В работе', tone: 'amber' },
  done: { label: 'Выполнена', tone: 'green' },
}

const priorities = {
  low: { label: 'Низкий', tone: 'neutral' },
  medium: { label: 'Средний', tone: 'amber' },
  high: { label: 'Высокий', tone: 'red' },
}

export function getStatus(status) {
  return statuses[status] || { label: 'Не указан', tone: 'neutral' }
}

export function getPriority(priority) {
  return priorities[priority] || { label: 'Не указан', tone: 'neutral' }
}

export function getAssigneeName(assignee, users) {
  if (assignee === null || assignee === undefined) return 'Не назначен'
  return users.get(assignee) || `Пользователь №${assignee}`
}

export function getPaginationPath(link) {
  if (!link || typeof link !== 'string') return null
  try {
    const url = new URL(link, 'http://localhost')
    if (!url.pathname.startsWith('/api/')) return null
    return `${url.pathname.slice('/api'.length)}${url.search}`
  } catch {
    return null
  }
}

export function normalizeTaskPage(data) {
  if (
    !data ||
    !Number.isInteger(data.count) ||
    !Array.isArray(data.pages) ||
    !Array.isArray(data.results)
  ) {
    throw new Error('Сервер вернул список задач в неизвестном формате.')
  }
  return data
}
