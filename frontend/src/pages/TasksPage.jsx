import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { auth } from '../auth/auth.js'
import Alert from '../components/ui/Alert.jsx'
import Badge from '../components/ui/Badge.jsx'
import Button, { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import {
  getAssigneeName,
  getPageNumber,
  getPriority,
  getStatus,
  getTaskPagePath,
  normalizeTaskPage,
  TASKS_PER_PAGE,
} from './tasks.js'
import styles from './TasksPage.module.css'

function TaskRow({ task, users }) {
  const status = getStatus(task.status)
  const priority = getPriority(task.priority)

  return (
    <li className={styles.task}>
      <div className={styles.title} data-label="Задача">
        <span>{task.title || 'Без названия'}</span>
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
    </li>
  )
}

export default function TasksPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const page = getPageNumber(searchParams.get('page'))
  const [taskPage, setTaskPage] = useState(null)
  const [requestError, setRequestError] = useState(null)
  const [retry, setRetry] = useState(0)
  const [users, setUsers] = useState(() => new Map())

  useEffect(() => {
    const controller = new AbortController()
    auth
      .request(getTaskPagePath(page), { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) {
          setTaskPage({ page, data: normalizeTaskPage(data) })
        }
      })
      .catch((requestError) => {
        if (!controller.signal.aborted && requestError.name !== 'AbortError') {
          setRequestError({
            page,
            retry,
            message: requestError.message || 'Не удалось загрузить задачи.',
          })
        }
      })

    return () => controller.abort()
  }, [page, retry])

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

  function goToPage(nextPage) {
    setSearchParams({ page: String(nextPage) })
  }

  const tasks = taskPage?.page === page ? taskPage.data : null
  const error =
    requestError?.page === page && requestError.retry === retry
      ? requestError.message
      : ''
  const totalPages = tasks
    ? Math.max(1, Math.ceil(tasks.count / TASKS_PER_PAGE))
    : 1

  return (
    <section aria-labelledby="page-title">
      <PageHeader
        title="Задачи"
        description="Задачи, которые вы создали или выполняете."
        actions={<ButtonLink to="/tasks/new">Новая задача</ButtonLink>}
      />
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
            </div>
            <ul className={styles.list} aria-label="Список задач">
              {tasks.results.map((task) => (
                <TaskRow key={task.id} task={task} users={users} />
              ))}
            </ul>
          </Card>
          {tasks.count > TASKS_PER_PAGE && (
            <nav className={styles.pagination} aria-label="Страницы задач">
              <button
                type="button"
                className={styles.pageButton}
                disabled={page === 1}
                onClick={() => goToPage(page - 1)}
              >
                Назад
              </button>
              <span>
                Страница {page} из {totalPages}
              </span>
              <button
                type="button"
                className={styles.pageButton}
                disabled={!tasks.next}
                onClick={() => goToPage(page + 1)}
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
