import { ButtonLink } from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'

export default function NotFoundPage() {
  return (
    <section aria-labelledby="page-title">
      <PageHeader title="Страница не найдена" />
      <Card>
        <EmptyState
          title="Здесь пока ничего нет"
          description="Проверьте адрес или вернитесь к задачам."
          action={<ButtonLink to="/tasks">Перейти к задачам</ButtonLink>}
        />
      </Card>
    </section>
  )
}
