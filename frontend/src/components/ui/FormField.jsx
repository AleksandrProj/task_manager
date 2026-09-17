import { useId } from 'react'
import styles from './ui.module.css'

export default function FormField({
  as: Control = 'input',
  label,
  hint,
  error,
  id,
  required = false,
  className = '',
  'aria-describedby': describedBy,
  ...props
}) {
  const generatedId = useId()
  const fieldId = id || generatedId
  const descriptionIds = [
    describedBy,
    hint && `${fieldId}-hint`,
    error && `${fieldId}-error`,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={styles.field}>
      <label htmlFor={fieldId} className={styles.label}>
        {label}
        {required && (
          <span className={styles.required} aria-hidden="true">
            {' '}
            *
          </span>
        )}
      </label>
      <Control
        {...props}
        id={fieldId}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={descriptionIds || undefined}
        className={`${styles.control} ${className}`}
      />
      {hint && (
        <p id={`${fieldId}-hint`} className={styles.hint}>
          {hint}
        </p>
      )}
      {error && (
        <p id={`${fieldId}-error`} className={styles.fieldError} role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
