import styles from './ui.module.css'

export default function PageHeader({ title, description, actions }) {
  return (
    <header className={styles.pageHeader}>
      <div className={styles.pageHeading}>
        <h1 id="page-title">{title}</h1>
        {description && <p className={styles.description}>{description}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </header>
  )
}
