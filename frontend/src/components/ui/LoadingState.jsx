import styles from './ui.module.css'

export default function LoadingState({ children = 'Загрузка…' }) {
  return (
    <div className={styles.loadingState} role="status">
      <span className={styles.spinner} aria-hidden="true" />
      <span>{children}</span>
    </div>
  )
}
