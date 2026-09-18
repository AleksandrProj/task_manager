import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { auth } from '../auth/auth.js'
import { useAuth } from '../auth/useAuth.js'
import Alert from '../components/ui/Alert.jsx'
import Badge from '../components/ui/Badge.jsx'
import Button, { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import {
  getAssigneeName,
  getPaginationPath,
  getPriority,
  getStatus,
  normalizeTaskPage,
} from './tasks.js'
import styles from './TasksPage.module.css'

function TaskRow({ task, users, canDelete, deleting, onDelete }) {
  const status = getStatus(task.status)
  const priority = getPriority(task.priority)

  return (
    <li className={styles.task}>
      <div className={styles.title} data-label="Задача">
        <Link className={styles.titleLink} to={`/tasks/${task.id}`}>
          {task.title || 'Без названия'}
        </Link>
        {task.description && <small>{task.description}</small>}
      </div>
      <div data-label="Статус">
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
      <div data-label="Приоритет">
        <Badge tone={priority.tone}>{priority.label}</Badge>
      </div>
      <div className={styles.assignee} data-label="Исполнитель">
        {getAssigneeName(task.assignee, users)}
      </div>
      {canDelete && (
        <div className={styles.rowActions}>
          <Button
            variant="danger"
            loading={deleting}
            loadingText="Удаляем…"
            onClick={() => onDelete(task)}
          >
            Удалить
          </Button>
        </div>
      )}
    </li>
  )
}

export default function TasksPage() {
  const { user } = useAuth()
  const [taskPath, setTaskPath] = useState('/tasks/')
  const [taskPage, setTaskPage] = useState(null)
  const [requestError, setRequestError] = useState(null)
  const [retry, setRetry] = useState(0)
  const [users, setUsers] = useState(() => new Map())
  const [deletingId, setDeletingId] = useState(null)
  const [actionMessage, setActionMessage] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    auth
      .request(taskPath, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setTaskPage({ path: taskPath, data: normalizeTaskPage(data) })
        }
      })
      .catch((requestError) => {
        if (!controller.signal.aborted && requestError.name !== 'AbortError') {
          setRequestError({
            path: taskPath,
            retry,
            message: requestError.message || 'Не удалось загрузить задачи.',
          })
        }
      })

    return () => controller.abort()
  }, [retry, taskPath])

  useEffect(() => {
    const controller = new AbortController()

    async function loadUsers() {
      const names = new Map()
      let userPage = 1
      while (!controller.signal.aborted) {
        const response = await auth.request(`/users/?page=${userPage}`, {
          signal: controller.signal,
        })
        if (!Array.isArray(response?.results)) return
        response.results.forEach((user) => {
          if (Number.isInteger(user.id) && user.username) {
            names.set(user.id, user.username)
          }
        })
        setUsers(new Map(names))
        if (!response.next) return
        userPage += 1
      }
    }

    loadUsers().catch((requestError) => {
      if (requestError.name !== 'AbortError') setUsers(new Map())
    })
    return () => controller.abort()
  }, [])

  function goToPage(link) {
    const path = getPaginationPath(link)
    if (path) setTaskPath(path)
  }

  async function deleteTask(task) {
    if (deletingId || !window.confirm(`Удалить задачу «${task.title}»?`)) return

    setDeletingId(task.id)
    setActionMessage('')
    try {
      await auth.request(`/tasks/${task.id}/`, { method: 'DELETE' })
      if (tasks.results.length === 1 && tasks.previous) goToPage(tasks.previous)
      else setRetry((value) => value + 1)
    } catch (error) {
      if (error.name !== 'AbortError') {
        setActionMessage(error.message || 'Не удалось удалить задачу.')
      }
    } finally {
      setDeletingId(null)
    }
  }

  const tasks = taskPage?.path === taskPath ? taskPage.data : null
  const error =
    requestError?.path === taskPath && requestError.retry === retry
      ? requestError.message
      : ''

  return (
    <section aria-labelledby="page-title">
      <PageHeader
        title="Задачи"
        description="Задачи, которые вы создали или выполняете."
        actions={<ButtonLink to="/tasks/new">Новая задача</ButtonLink>}
      />
      {actionMessage && (
        <Alert title="Не удалось удалить задачу">{actionMessage}</Alert>
      )}
      {error ? (
        <Card>
          <Alert title="Не удалось загрузить задачи">{error}</Alert>
          <Button
            variant="secondary"
            onClick={() => setRetry((value) => value + 1)}
          >
            Попробовать снова
          </Button>
        </Card>
      ) : !tasks ? (
        <Card>
          <LoadingState>Загружаем задачи…</LoadingState>
        </Card>
      ) : tasks.results.length === 0 ? (
        <Card>
          <EmptyState
            title="Задач пока нет"
            description="Создайте первую задачу, чтобы начать работу."
            action={<ButtonLink to="/tasks/new">Создать задачу</ButtonLink>}
          />
        </Card>
      ) : (
        <>
          <Card className={styles.listCard}>
            <div className={styles.columns} aria-hidden="true">
              <span>Задача</span>
              <span>Статус</span>
              <span>Приоритет</span>
              <span>Исполнитель</span>
              <span>Действия</span>
            </div>
            <ul className={styles.list} aria-label="Список задач">
              {tasks.results.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  users={users}
                  canDelete={task.creator === user?.id}
                  deleting={deletingId === task.id}
                  onDelete={deleteTask}
                />
              ))}
            </ul>
          </Card>
          {(tasks.previous || tasks.next) && (
            <nav className={styles.pagination} aria-label="Страницы задач">
              <button
                type="button"
                className={styles.pageButton}
                disabled={!tasks.previous}
                onClick={() => goToPage(tasks.previous)}
              >
                Назад
              </button>
              {tasks.pages.map((page) => (
                <button
                  key={page.number}
                  type="button"
                  className={styles.pageNumber}
                  aria-current={page.current ? 'page' : undefined}
                  disabled={page.current}
                  onClick={() => goToPage(page.url)}
                >
                  {page.number}
                </button>
              ))}
              <button
                type="button"
                className={styles.pageButton}
                disabled={!tasks.next}
                onClick={() => goToPage(tasks.next)}
              >
                Вперёд
              </button>
            </nav>
          )}
        </>
      )}
    </section>
  )
}
