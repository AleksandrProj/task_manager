import styles from './ui.module.css'

export default function Alert({ title, children, variant = 'error' }) {
  return (
    <div
      className={`${styles.alert} ${styles[variant]}`}
      role={variant === 'error' ? 'alert' : 'status'}
    >
      {title && <p className={styles.alertTitle}>{title}</p>}
      {children && <div>{children}</div>}
    </div>
  )
}
