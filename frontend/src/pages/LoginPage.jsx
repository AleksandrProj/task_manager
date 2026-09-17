import { useEffect, useRef, useState } from 'react'
import { Navigate, useLocation } from 'react-router'
import { auth } from '../auth/auth.js'
import { getReturnPath } from '../auth/returnPath.js'
import { useAuth } from '../auth/useAuth.js'
import SessionStatus from '../components/SessionStatus.jsx'
import Alert from '../components/ui/Alert.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import FormField from '../components/ui/FormField.jsx'
import styles from './LoginPage.module.css'

export default function LoginPage() {
  const session = useAuth()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const pending = useRef(null)

  useEffect(() => () => pending.current?.abort(), [])

  async function handleSubmit(event) {
    event.preventDefault()
    if (pending.current) return
    const nextErrors = {}
    if (!username.trim()) nextErrors.username = 'Введите имя пользователя.'
    if (!password) nextErrors.password = 'Введите пароль.'
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
      await auth.login(username.trim(), password, { signal: controller.signal })
    } catch (error) {
      if (error.name === 'AbortError') return
      if (error.status === 401)
        setMessage('Неверное имя пользователя или пароль.')
      else if (error.status === 400)
        setMessage('Проверьте имя пользователя и пароль.')
      else setMessage(error.message || 'Не удалось войти. Попробуйте ещё раз.')
    } finally {
      if (pending.current === controller) pending.current = null
      if (!controller.signal.aborted) setSubmitting(false)
    }
  }

  if (session.status === 'loading' || session.status === 'error') {
    return <SessionStatus {...session} />
  }
  if (session.user) {
    return <Navigate to={getReturnPath(location.state?.from)} replace />
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.intro} aria-label="О приложении">
        <span className={styles.eyebrow}>ВАШЕ РАБОЧЕЕ ПРОСТРАНСТВО</span>
        <h2>
          Задачи понятны.
          <br />
          Работа организована.
        </h2>
        <p>
          Планируйте работу, назначайте исполнителей и обсуждайте детали в одном
          месте.
        </p>
        <ul className={styles.features}>
          <li>
            <span aria-hidden="true">✓</span> Всё важное — в задачах
          </li>
          <li>
            <span aria-hidden="true">✓</span> Понятные статусы и приоритеты
          </li>
          <li>
            <span aria-hidden="true">✓</span> Обсуждения рядом с задачей
          </li>
        </ul>
      </aside>
      <Card className={styles.card}>
        <header className={styles.formHeader}>
          <h1>Вход в Task Manager</h1>
          <p>Введите данные своей учётной записи.</p>
        </header>
        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          {session.message && !message && (
            <Alert variant="info">{session.message}</Alert>
          )}
          {message && <Alert title="Не удалось войти">{message}</Alert>}
          <FormField
            label="Имя пользователя"
            name="username"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            required
            maxLength={150}
            placeholder="Ваш логин"
            value={username}
            disabled={submitting}
            error={errors.username}
            onChange={(event) => {
              setUsername(event.target.value)
              setErrors((current) => ({ ...current, username: '' }))
              setMessage('')
            }}
          />
          <div className={styles.passwordGroup}>
            <FormField
              id="login-password"
              label="Пароль"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              placeholder="Ваш пароль"
              value={password}
              disabled={submitting}
              error={errors.password}
              onChange={(event) => {
                setPassword(event.target.value)
                setErrors((current) => ({ ...current, password: '' }))
                setMessage('')
              }}
            />
            <button
              type="button"
              className={styles.toggle}
              aria-controls="login-password"
              aria-pressed={showPassword}
              disabled={submitting}
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? 'Скрыть пароль' : 'Показать пароль'}
            </button>
          </div>
          <Button
            type="submit"
            loading={submitting}
            loadingText="Входим…"
            className={styles.submit}
          >
            Войти
          </Button>
        </form>
        <p className={styles.help}>
          Нет учётной записи или забыли пароль?
          <br />
          Обратитесь к администратору.
        </p>
      </Card>
    </div>
  )
}
