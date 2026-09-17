import { Link } from 'react-router'
import styles from './ui.module.css'

export default function Button({
  children,
  variant = 'primary',
  loading = false,
  loadingText = 'Сохранение…',
  disabled = false,
  type = 'button',
  className = '',
  ...props
}) {
  return (
    <button
      {...props}
      type={type}
      className={`${styles.button} ${styles[variant]} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {loading && <span className={styles.spinner} aria-hidden="true" />}
      {loading ? loadingText : children}
    </button>
  )
}

export function ButtonLink({
  children,
  variant = 'primary',
  className = '',
  ...props
}) {
  return (
    <Link
      {...props}
      className={`${styles.button} ${styles[variant]} ${className}`}
    >
      {children}
    </Link>
  )
}
