import Card from '../components/ui/Card.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import PageHeader from '../components/ui/PageHeader.jsx'

export default function PlaceholderPage({ title, description }) {
  return (
    <section aria-labelledby="page-title">
      <PageHeader title={title} description={description} />
      <Card>
        <EmptyState title="Этот раздел скоро появится" />
      </Card>
    </section>
  )
}
