export const TASKS_PER_PAGE = 20

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

export function getPageNumber(value) {
  const page = Number(value)
  return Number.isInteger(page) && page > 0 ? page : 1
}

export function getTaskPagePath(page) {
  return `/tasks/?page=${page}`
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

export function normalizeTaskPage(data) {
  if (!data || !Number.isInteger(data.count) || !Array.isArray(data.results)) {
    throw new Error('Сервер вернул список задач в неизвестном формате.')
  }
  return data
}
