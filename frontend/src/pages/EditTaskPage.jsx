import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import { auth } from '../auth/auth.js'
import { useAuth } from '../auth/useAuth.js'
import Alert from '../components/ui/Alert.jsx'
import Button, { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import FormField from '../components/ui/FormField.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import styles from './AddTasksPage.module.css'

const emptyValues = {
  title: '',
  description: '',
  status: 'new',
  priority: 'medium',
  assignee: '',
}

function getServerErrors(details) {
  if (!details || typeof details !== 'object') return {}

  const messages = {
    title: 'Проверьте название задачи.',
    description: 'Описание должно содержать не более 500 символов.',
    status: 'Выберите статус из списка.',
    priority: 'Выберите приоритет из списка.',
    assignee: 'Выберите доступного исполнителя.',
  }

  return Object.fromEntries(
    Object.keys(messages)
      .filter((field) => details[field])
      .map((field) => [field, messages[field]]),
  )
}

export default function EditTaskPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const taskId = Number(id)
  const invalidId = !Number.isInteger(taskId) || taskId < 1
  const [taskResponse, setTaskResponse] = useState(null)
  const [requestError, setRequestError] = useState(null)
  const [retry, setRetry] = useState(0)
  const [values, setValues] = useState(emptyValues)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [users, setUsers] = useState([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [usersMessage, setUsersMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const pending = useRef(null)

  useEffect(() => {
    if (invalidId) return undefined

    const controller = new AbortController()
    auth
      .request(`/tasks/${taskId}/`, { signal: controller.signal })
      .then((task) => {
        if (!controller.signal.aborted && task?.id === taskId) {
          setTaskResponse({ id: taskId, data: task })
          setValues({
            title: task.title || '',
            description: task.description || '',
            status: task.status || 'new',
            priority: task.priority || 'medium',
            assignee: task.assignee ? String(task.assignee) : '',
          })
        } else if (!controller.signal.aborted) {
          setRequestError({
            id: taskId,
            retry,
            message: 'Сервер вернул задачу в неизвестном формате.',
          })
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted && error.name !== 'AbortError') {
          setRequestError({
            id: taskId,
            retry,
            message: error.message || 'Не удалось загрузить задачу.',
          })
        }
      })

    return () => controller.abort()
  }, [invalidId, retry, taskId])

  useEffect(() => {
    const controller = new AbortController()

    async function loadUsers() {
      const loadedUsers = []
      let page = 1
      while (!controller.signal.aborted) {
        const response = await auth.request(`/users/?page=${page}`, {
          signal: controller.signal,
        })
        if (!Array.isArray(response?.results)) {
          throw new Error(
            'Сервер вернул список пользователей в неизвестном формате.',
          )
        }
        loadedUsers.push(...response.results)
        if (!response.next) {
          setUsers(loadedUsers)
          return
        }
        page += 1
      }
    }

    loadUsers()
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setUsersMessage(error.message || 'Не удалось загрузить исполнителей.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setUsersLoading(false)
      })

    return () => controller.abort()
  }, [])

  useEffect(() => () => pending.current?.abort(), [])

  function updateValue(field, value) {
    setValues((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: '' }))
    setMessage('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (pending.current) return

    const nextErrors = {}
    if (isCreator && !values.title.trim()) {
      nextErrors.title = 'Введите название задачи.'
    }
    setErrors(nextErrors)
    setMessage('')

    const firstError = Object.keys(nextErrors)[0]
    if (firstError) {
      event.currentTarget.elements[firstError].focus()
      return
    }

    const controller = new AbortController()
    pending.current = controller
    setSubmitting(true)
    try {
      await auth.request(
        isCreator ? `/tasks/${taskId}/` : `/tasks/${taskId}/status/`,
        {
          method: 'PUT',
          data: isCreator
            ? {
                title: values.title.trim(),
                description: values.description.trim(),
                status: values.status,
                priority: values.priority,
                assignee: values.assignee ? Number(values.assignee) : null,
              }
            : { status: values.status },
          signal: controller.signal,
        },
      )
      navigate(`/tasks/${taskId}`)
    } catch (error) {
      if (error.name === 'AbortError') return
      const serverErrors = getServerErrors(error.details)
      setErrors(serverErrors)
      setMessage(
        error.status === 400
          ? 'Проверьте заполненные поля.'
          : error.message ||
              'Не удалось сохранить изменения. Попробуйте ещё раз.',
      )
      const serverField = Object.keys(serverErrors)[0]
      if (serverField) event.currentTarget.elements[serverField].focus()
    } finally {
      if (pending.current === controller) pending.current = null
      if (!controller.signal.aborted) setSubmitting(false)
    }
  }

  const task = taskResponse?.id === taskId ? taskResponse.data : null
  const error = invalidId
    ? 'Задача с таким адресом не найдена.'
    : requestError?.id === taskId && requestError.retry === retry
      ? requestError.message
      : ''
  const assignees = users.filter((candidate) => candidate.id !== task?.creator)
  const isCreator = task?.creator === user?.id
  const canChangeStatus = isCreator || task?.assignee === user?.id

  return (
    <section aria-labelledby="page-title">
      <PageHeader
        title={isCreator ? 'Редактирование задачи' : 'Изменение статуса'}
        description={task ? task.title : 'Загружаем данные задачи.'}
        actions={
          <ButtonLink variant="secondary" to={`/tasks/${id}`}>
            К задаче
          </ButtonLink>
        }
      />
      {error ? (
        <Card className={styles.card}>
          <Alert title="Не удалось открыть задачу">{error}</Alert>
          {!invalidId && (
            <Button
              variant="secondary"
              onClick={() => setRetry((value) => value + 1)}
            >
              Попробовать снова
            </Button>
          )}
        </Card>
      ) : !task ? (
        <Card className={styles.card}>
          <LoadingState>Загружаем задачу…</LoadingState>
        </Card>
      ) : !canChangeStatus ? (
        <Card className={styles.card}>
          <Alert title="Редактирование недоступно">
            Изменять задачу может её создатель или текущий исполнитель.
          </Alert>
        </Card>
      ) : (
        <Card className={styles.card}>
          <form className={styles.form} onSubmit={handleSubmit} noValidate>
            {message && (
              <Alert title="Не удалось сохранить изменения">{message}</Alert>
            )}
            {isCreator ? (
              <>
                <FormField
                  label="Название"
                  name="title"
                  required
                  autoFocus
                  maxLength={150}
                  value={values.title}
                  disabled={submitting}
                  error={errors.title}
                  onChange={(event) => updateValue('title', event.target.value)}
                />
                <FormField
                  as="textarea"
                  label="Описание"
                  name="description"
                  maxLength={500}
                  value={values.description}
                  disabled={submitting}
                  error={errors.description}
                  onChange={(event) =>
                    updateValue('description', event.target.value)
                  }
                />
                <div className={styles.fields}>
                  <FormField
                    as="select"
                    label="Статус"
                    name="status"
                    value={values.status}
                    disabled={submitting}
                    error={errors.status}
                    onChange={(event) =>
                      updateValue('status', event.target.value)
                    }
                  >
                    <option value="new">Новая</option>
                    <option value="in_progress">В работе</option>
                    <option value="done">Выполнена</option>
                  </FormField>
                  <FormField
                    as="select"
                    label="Приоритет"
                    name="priority"
                    value={values.priority}
                    disabled={submitting}
                    error={errors.priority}
                    onChange={(event) =>
                      updateValue('priority', event.target.value)
                    }
                  >
                    <option value="low">Низкий</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                  </FormField>
                </div>
                {usersLoading ? (
                  <LoadingState>Загружаем исполнителей…</LoadingState>
                ) : (
                  <FormField
                    as="select"
                    label="Исполнитель"
                    name="assignee"
                    value={values.assignee}
                    disabled={submitting || Boolean(usersMessage)}
                    error={errors.assignee}
                    hint={
                      usersMessage || 'Исполнителя можно снять или изменить.'
                    }
                    onChange={(event) =>
                      updateValue('assignee', event.target.value)
                    }
                  >
                    <option value="">Не назначен</option>
                    {assignees.map((assignee) => (
                      <option key={assignee.id} value={assignee.id}>
                        {assignee.username}
                      </option>
                    ))}
                  </FormField>
                )}
              </>
            ) : (
              <>
                <Alert variant="info" title="Доступ исполнителя">
                  Вы можете изменить только статус этой задачи.
                </Alert>
                <FormField
                  as="select"
                  label="Статус"
                  name="status"
                  value={values.status}
                  disabled={submitting}
                  error={errors.status}
                  onChange={(event) =>
                    updateValue('status', event.target.value)
                  }
                >
                  <option value="new">Новая</option>
                  <option value="in_progress">В работе</option>
                  <option value="done">Выполнена</option>
                </FormField>
              </>
            )}
            <div className={styles.actions}>
              <Button
                type="submit"
                loading={submitting}
                loadingText="Сохраняем…"
              >
                {isCreator ? 'Сохранить изменения' : 'Изменить статус'}
              </Button>
              <ButtonLink variant="secondary" to={`/tasks/${taskId}`}>
                Отмена
              </ButtonLink>
            </div>
          </form>
        </Card>
      )}
    </section>
  )
}
