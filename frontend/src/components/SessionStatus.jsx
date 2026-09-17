import { auth } from '../auth/auth.js'
import Alert from './ui/Alert.jsx'
import Button from './ui/Button.jsx'
import Card from './ui/Card.jsx'
import LoadingState from './ui/LoadingState.jsx'
import styles from './SessionStatus.module.css'

export default function SessionStatus({ status, message }) {
  return (
    <Card className={styles.card}>
      {status === 'loading' ? (
        <LoadingState>Проверяем вход…</LoadingState>
      ) : (
        <div className={styles.stack}>
          <Alert title="Не удалось восстановить вход">{message}</Alert>
          <div className={styles.actions}>
            <Button onClick={() => auth.restore()}>Попробовать снова</Button>
            <Button variant="secondary" onClick={() => auth.logout()}>
              Войти заново
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
}
