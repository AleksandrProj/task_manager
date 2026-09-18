import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router'
import { auth } from '../auth/auth.js'
import { useAuth } from '../auth/useAuth.js'
import Alert from '../components/ui/Alert.jsx'
import Badge from '../components/ui/Badge.jsx'
import Button, { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import FormField from '../components/ui/FormField.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import {
  getAssigneeName,
  getPaginationPath,
  getPriority,
  getStatus,
} from './tasks.js'
import styles from './TaskDetailPage.module.css'

function formatDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Не указана'
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export default function TaskDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const taskId = Number(id)
  const invalidId = !Number.isInteger(taskId) || taskId < 1
  const [taskResponse, setTaskResponse] = useState(null)
  const [users, setUsers] = useState(() => new Map())
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const commentStartPath = invalidId ? null : `/comments/?task=${taskId}`
  const [commentNavigation, setCommentNavigation] = useState(() => ({
    taskId,
    path: commentStartPath,
  }))
  const [commentResponse, setCommentResponse] = useState(null)
  const [commentError, setCommentError] = useState(null)
  const [commentRetry, setCommentRetry] = useState(0)
  const [commentText, setCommentText] = useState('')
  const [commentFormError, setCommentFormError] = useState('')
  const [commentSubmitting, setCommentSubmitting] = useState(false)
  const [commentDeletingId, setCommentDeletingId] = useState(null)
  const [commentActionMessage, setCommentActionMessage] = useState('')
  const commentPending = useRef(null)
  const commentDeletePending = useRef(null)
  const commentPath =
    commentNavigation.taskId === taskId
      ? commentNavigation.path
      : commentStartPath

  useEffect(() => {
    if (invalidId) return undefined

    const controller = new AbortController()
    auth
      .request(`/tasks/${taskId}/`, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted && data?.id === taskId) {
          setTaskResponse({ id: taskId, data })
        } else if (!controller.signal.aborted) {
          setError('Сервер вернул задачу в неизвестном формате.')
        }
      })
      .catch((requestError) => {
        if (!controller.signal.aborted && requestError.name !== 'AbortError') {
          setError(requestError.message || 'Не удалось загрузить задачу.')
        }
      })

    return () => controller.abort()
  }, [invalidId, taskId, retry])

  useEffect(() => {
    const controller = new AbortController()

    async function loadUsers() {
      const names = new Map()
      let page = 1
      while (!controller.signal.aborted) {
        const response = await auth.request(`/users/?page=${page}`, {
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
        page += 1
      }
    }

    loadUsers().catch(() => undefined)
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!commentPath) return undefined

    const controller = new AbortController()
    auth
      .request(commentPath, { signal: controller.signal })
      .then((data) => {
        if (
          !controller.signal.aborted &&
          Number.isInteger(data?.count) &&
          Array.isArray(data.pages) &&
          Array.isArray(data.results)
        ) {
          setCommentResponse({ taskId, path: commentPath, data })
        } else if (!controller.signal.aborted) {
          setCommentError({
            taskId,
            path: commentPath,
            retry: commentRetry,
            message: 'Сервер вернул комментарии в неизвестном формате.',
          })
        }
      })
      .catch((requestError) => {
        if (!controller.signal.aborted && requestError.name !== 'AbortError') {
          setCommentError({
            taskId,
            path: commentPath,
            retry: commentRetry,
            message:
              requestError.message || 'Не удалось загрузить комментарии.',
          })
        }
      })

    return () => controller.abort()
  }, [commentPath, commentRetry, taskId])

  useEffect(
    () => () => {
      commentPending.current?.abort()
      commentDeletePending.current?.abort()
    },
    [],
  )

  const task = taskResponse?.id === taskId ? taskResponse.data : null
  const status = getStatus(task?.status)
  const priority = getPriority(task?.priority)
  const displayError = invalidId ? 'Задача с таким адресом не найдена.' : error
  const comments =
    commentResponse?.taskId === taskId && commentResponse.path === commentPath
      ? commentResponse.data
      : null
  const displayCommentError =
    commentError?.taskId === taskId &&
    commentError.path === commentPath &&
    commentError.retry === commentRetry
      ? commentError.message
      : ''

  async function addComment(event) {
    event.preventDefault()
    if (commentPending.current) return

    const text = commentText.trim()
    if (!text) {
      setCommentFormError('Введите текст комментария.')
      event.currentTarget.elements.text.focus()
      return
    }

    const controller = new AbortController()
    commentPending.current = controller
    setCommentSubmitting(true)
    setCommentFormError('')
    try {
      await auth.request('/comments/', {
        method: 'POST',
        data: { task: taskId, text },
        signal: controller.signal,
      })
      setCommentText('')
      setCommentResponse(null)
      setCommentRetry((value) => value + 1)
    } catch (requestError) {
      if (requestError.name !== 'AbortError') {
        setCommentFormError(
          requestError.status === 400
            ? 'Проверьте текст комментария.'
            : requestError.message || 'Не удалось добавить комментарий.',
        )
      }
    } finally {
      if (commentPending.current === controller) commentPending.current = null
      if (!controller.signal.aborted) setCommentSubmitting(false)
    }
  }

  function goToCommentPage(link) {
    const path = getPaginationPath(link)
    if (path) setCommentNavigation({ taskId, path })
  }

  async function deleteComment(comment) {
    if (
      commentDeletePending.current ||
      !window.confirm('Удалить этот комментарий?')
    ) {
      return
    }

    const controller = new AbortController()
    commentDeletePending.current = controller
    setCommentDeletingId(comment.id)
    setCommentActionMessage('')
    try {
      await auth.request(`/comments/${comment.id}/`, {
        method: 'DELETE',
        signal: controller.signal,
      })
      if (comments.results.length === 1 && comments.previous) {
        goToCommentPage(comments.previous)
      } else {
        setCommentResponse(null)
        setCommentRetry((value) => value + 1)
      }
    } catch (requestError) {
      if (requestError.name !== 'AbortError') {
        setCommentActionMessage(
          requestError.message || 'Не удалось удалить комментарий.',
        )
      }
    } finally {
      if (commentDeletePending.current === controller) {
        commentDeletePending.current = null
      }
      if (!controller.signal.aborted) setCommentDeletingId(null)
    }
  }

  return (
    <section aria-labelledby="page-title">
      <PageHeader
        title={task?.title || 'Задача'}
        description={task ? 'Подробная информация о задаче.' : undefined}
        actions={
          <>
            {task?.creator === user?.id && (
              <ButtonLink to={`/tasks/${task.id}/edit`}>
                Редактировать
              </ButtonLink>
            )}
            <ButtonLink variant="secondary" to="/tasks">
              К списку задач
            </ButtonLink>
          </>
        }
      />
      {displayError ? (
        <Card className={styles.card}>
          <Alert title="Не удалось открыть задачу">{displayError}</Alert>
          {!invalidId && (
            <Button
              variant="secondary"
              className={styles.retry}
              onClick={() => {
                setTaskResponse(null)
                setError('')
                setRetry((value) => value + 1)
              }}
            >
              Попробовать снова
            </Button>
          )}
        </Card>
      ) : !task ? (
        <Card className={styles.card}>
          <LoadingState>Загружаем задачу…</LoadingState>
        </Card>
      ) : (
        <div className={styles.stack}>
          <Card className={styles.card}>
            <div className={styles.summary}>
              <div>
                <span className={styles.label}>Статус</span>
                <Badge tone={status.tone}>{status.label}</Badge>
              </div>
              <div>
                <span className={styles.label}>Приоритет</span>
                <Badge tone={priority.tone}>{priority.label}</Badge>
              </div>
            </div>
            <div className={styles.description}>
              <h2>Описание</h2>
              <p>{task.description || 'Описание не добавлено.'}</p>
            </div>
            <dl className={styles.details}>
              <div>
                <dt>Создатель</dt>
                <dd>{getAssigneeName(task.creator, users)}</dd>
              </div>
              <div>
                <dt>Исполнитель</dt>
                <dd>{getAssigneeName(task.assignee, users)}</dd>
              </div>
              <div>
                <dt>Создана</dt>
                <dd>{formatDate(task.created_at)}</dd>
              </div>
              <div>
                <dt>Обновлена</dt>
                <dd>{formatDate(task.updated_at)}</dd>
              </div>
            </dl>
          </Card>
          <Card className={styles.card}>
            <h2 className={styles.commentsTitle}>Комментарии</h2>
            <form
              className={styles.commentForm}
              onSubmit={addComment}
              noValidate
            >
              <FormField
                as="textarea"
                label="Новый комментарий"
                name="text"
                maxLength={500}
                placeholder="Напишите сообщение для участников задачи"
                value={commentText}
                disabled={commentSubmitting}
                error={commentFormError}
                onChange={(event) => {
                  setCommentText(event.target.value)
                  setCommentFormError('')
                }}
              />
              <Button
                type="submit"
                loading={commentSubmitting}
                loadingText="Добавляем…"
              >
                Добавить комментарий
              </Button>
            </form>
            {commentActionMessage && (
              <Alert title="Не удалось удалить комментарий">
                {commentActionMessage}
              </Alert>
            )}
            {displayCommentError ? (
              <div className={styles.commentState}>
                <Alert title="Не удалось загрузить комментарии">
                  {displayCommentError}
                </Alert>
                <Button
                  variant="secondary"
                  onClick={() => setCommentRetry((value) => value + 1)}
                >
                  Попробовать снова
                </Button>
              </div>
            ) : !comments ? (
              <LoadingState>Загружаем комментарии…</LoadingState>
            ) : comments.results.length === 0 ? (
              <p className={styles.emptyComments}>Комментариев пока нет.</p>
            ) : (
              <>
                <ol className={styles.comments}>
                  {comments.results.map((comment) => (
                    <li key={comment.id} className={styles.comment}>
                      <div className={styles.commentMeta}>
                        <div>
                          <strong>
                            {getAssigneeName(comment.author, users)}
                          </strong>
                          <time dateTime={comment.created_at}>
                            {formatDate(comment.created_at)}
                          </time>
                        </div>
                        {comment.author === user?.id && (
                          <Button
                            variant="danger"
                            loading={commentDeletingId === comment.id}
                            loadingText="Удаляем…"
                            onClick={() => deleteComment(comment)}
                          >
                            Удалить
                          </Button>
                        )}
                      </div>
                      <p>{comment.text}</p>
                    </li>
                  ))}
                </ol>
                {(comments.previous || comments.next) && (
                  <nav
                    className={styles.commentPagination}
                    aria-label="Страницы комментариев"
                  >
                    <Button
                      variant="secondary"
                      disabled={!comments.previous}
                      onClick={() => goToCommentPage(comments.previous)}
                    >
                      Назад
                    </Button>
                    {comments.pages.map((page) => (
                      <Button
                        key={page.number}
                        variant={page.current ? 'primary' : 'secondary'}
                        disabled={page.current}
                        aria-current={page.current ? 'page' : undefined}
                        onClick={() => goToCommentPage(page.url)}
                      >
                        {page.number}
                      </Button>
                    ))}
                    <Button
                      variant="secondary"
                      disabled={!comments.next}
                      onClick={() => goToCommentPage(comments.next)}
                    >
                      Вперед
                    </Button>
                  </nav>
                )}
              </>
            )}
          </Card>
        </div>
      )}
    </section>
  )
}
