import styles from './ui.module.css'

export default function Card({ children, className = '', ...props }) {
  return (
    <div {...props} className={`${styles.card} ${className}`}>
      {children}
    </div>
  )
}
