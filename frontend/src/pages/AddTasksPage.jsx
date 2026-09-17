import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { auth } from '../auth/auth.js'
import { useAuth } from '../auth/useAuth.js'
import Alert from '../components/ui/Alert.jsx'
import Button, { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import FormField from '../components/ui/FormField.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import styles from './AddTasksPage.module.css'

const initialValues = {
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

export default function AddTasksPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [users, setUsers] = useState([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [usersMessage, setUsersMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const pending = useRef(null)

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
    if (!values.title.trim()) nextErrors.title = 'Введите название задачи.'
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
      await auth.request('/tasks/', {
        method: 'POST',
        data: {
          title: values.title.trim(),
          description: values.description.trim(),
          status: values.status,
          priority: values.priority,
          assignee: values.assignee ? Number(values.assignee) : null,
        },
        signal: controller.signal,
      })
      navigate('/tasks')
    } catch (error) {
      if (error.name === 'AbortError') return
      const serverErrors = getServerErrors(error.details)
      setErrors(serverErrors)
      setMessage(
        error.status === 400
          ? 'Проверьте заполненные поля.'
          : error.message || 'Не удалось создать задачу. Попробуйте ещё раз.',
      )
      const serverField = Object.keys(serverErrors)[0]
      if (serverField) event.currentTarget.elements[serverField].focus()
    } finally {
      if (pending.current === controller) pending.current = null
      if (!controller.signal.aborted) setSubmitting(false)
    }
  }

  const assignees = users.filter((candidate) => candidate.id !== user?.id)

  return (
    <section aria-labelledby="page-title">
      <PageHeader
        title="Новая задача"
        description="Заполните основные данные и при необходимости назначьте исполнителя."
        actions={
          <ButtonLink variant="secondary" to="/tasks">
            К списку задач
          </ButtonLink>
        }
      />
      <Card className={styles.card}>
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          {message && (
            <Alert title="Не удалось создать задачу">{message}</Alert>
          )}
          <FormField
            label="Название"
            name="title"
            required
            autoFocus
            maxLength={150}
            placeholder="Например, подготовить план встречи"
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
            placeholder="Добавьте детали, если они нужны"
            value={values.description}
            disabled={submitting}
            error={errors.description}
            onChange={(event) => updateValue('description', event.target.value)}
          />
          <div className={styles.fields}>
            <FormField
              as="select"
              label="Статус"
              name="status"
              value={values.status}
              disabled={submitting}
              error={errors.status}
              onChange={(event) => updateValue('status', event.target.value)}
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
              onChange={(event) => updateValue('priority', event.target.value)}
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
              hint={usersMessage || 'Исполнителя можно назначить позже.'}
              onChange={(event) => updateValue('assignee', event.target.value)}
            >
              <option value="">Не назначен</option>
              {assignees.map((assignee) => (
                <option key={assignee.id} value={assignee.id}>
                  {assignee.username}
                </option>
              ))}
            </FormField>
          )}
          <div className={styles.actions}>
            <Button type="submit" loading={submitting} loadingText="Создаём…">
              Создать задачу
            </Button>
            <ButtonLink variant="secondary" to="/tasks">
              Отмена
            </ButtonLink>
          </div>
        </form>
      </Card>
    </section>
  )
}
