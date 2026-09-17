import styles from './ui.module.css'

export default function EmptyState({ title, description, action }) {
  return (
    <div className={styles.emptyState}>
      <span className={styles.emptyIcon} aria-hidden="true">
        ☰
      </span>
      <h2>{title}</h2>
      {description && <p className={styles.description}>{description}</p>}
      {action && <div className={styles.actions}>{action}</div>}
    </div>
  )
}
