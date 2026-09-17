import { useState } from 'react'
import Alert from '../components/ui/Alert.jsx'
import Badge from '../components/ui/Badge.jsx'
import Button, { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import FormField from '../components/ui/FormField.jsx'
import LoadingState from '../components/ui/LoadingState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'
import styles from './ComponentsPage.module.css'

export default function ComponentsPage() {
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  function handleSubmit(event) {
    event.preventDefault()
    const invalid = !title.trim()
    setError(invalid ? 'Введите название задачи.' : '')
    setSuccess(!invalid)
    if (invalid) event.currentTarget.elements.title.focus()
  }

  function resetExample(event) {
    event.currentTarget.form.reset()
    setTitle('')
    setError('')
    setSuccess(false)
  }

  return (
    <section aria-labelledby="page-title">
      <PageHeader
        title="Компоненты интерфейса"
        description="Примеры для проверки оформления. Данные этой страницы не отправляются на сервер."
        actions={
          <ButtonLink to="/tasks" variant="secondary">
            К задачам
          </ButtonLink>
        }
      />
      <div className={styles.grid}>
        <Card>
          <h2 className={styles.heading}>Поля и проверка формы</h2>
          <form className={styles.stack} onSubmit={handleSubmit} noValidate>
            <FormField
              label="Название задачи"
              name="title"
              required
              maxLength={150}
              value={title}
              onChange={(event) => {
                setTitle(event.target.value)
                setError('')
                setSuccess(false)
              }}
              placeholder="Например, подготовить документацию"
              hint="До 150 символов. Поля со звёздочкой обязательны."
              error={error}
            />
            <FormField
              as="textarea"
              label="Описание"
              name="description"
              maxLength={500}
              hint="До 500 символов."
            />
            <FormField
              as="select"
              label="Статус"
              name="status"
              defaultValue="new"
            >
              <option value="new">Новая</option>
              <option value="in_progress">В работе</option>
              <option value="done">Выполнена</option>
            </FormField>
            <FormField
              label="Недоступное поле"
              disabled
              defaultValue="Только для примера"
            />
            {success && (
              <Alert variant="success" title="Поля заполнены">
                Это пример формы, данные не отправлены.
              </Alert>
            )}
            <div className={styles.row}>
              <Button type="submit">Проверить форму</Button>
              <Button variant="secondary" onClick={resetExample}>
                Сбросить
              </Button>
            </div>
          </form>
        </Card>
        <div className={styles.stack}>
          <Card>
            <h2 className={styles.heading}>Состояния кнопок</h2>
            <div className={styles.row}>
              <Button loading>Сохранить</Button>
              <Button disabled>Недоступно</Button>
              <Button variant="danger" disabled>
                Удалить
              </Button>
            </div>
          </Card>
          <Card>
            <h2 className={styles.heading}>Статусы и приоритеты</h2>
            <div className={styles.row}>
              <Badge>Новая</Badge>
              <Badge tone="blue">В работе</Badge>
              <Badge tone="green">Выполнена</Badge>
              <Badge tone="amber">Средний приоритет</Badge>
              <Badge tone="red">Высокий приоритет</Badge>
            </div>
          </Card>
          <Alert title="Не удалось сохранить">
            Проверьте соединение и попробуйте ещё раз.
          </Alert>
          <Alert variant="info" title="Изменения доступны автору задачи" />
          <Card>
            <LoadingState>Загружаем задачи…</LoadingState>
          </Card>
        </div>
      </div>
      <Card className={styles.bottomCard}>
        <EmptyState
          title="Пока нет задач"
          description="Здесь появятся задачи, которые вы создадите или получите от коллег."
        />
      </Card>
    </section>
  )
}
