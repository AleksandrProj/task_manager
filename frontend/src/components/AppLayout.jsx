import { NavLink, Outlet } from 'react-router'
import { auth } from '../auth/auth.js'
import { useAuth } from '../auth/useAuth.js'
import Button from './ui/Button.jsx'
import styles from './AppLayout.module.css'

export default function AppLayout() {
  const { user } = useAuth()
  return (
    <div className={styles.app}>
      <a className={styles.skipLink} href="#main">
        К содержимому
      </a>
      <header className={styles.header}>
        <NavLink to="/tasks" className={styles.brand}>
          <span className={styles.mark} aria-hidden="true">
            ✓
          </span>
          Task Manager
        </NavLink>
        <nav className={styles.nav} aria-label="Основная навигация">
          <NavLink to="/tasks">Задачи</NavLink>
          {user ? (
            <>
              <span className={styles.username} title={user.username}>
                {user.username}
              </span>
              <Button variant="secondary" onClick={() => auth.logout()}>
                Выйти
              </Button>
            </>
          ) : (
            <NavLink to="/login">Войти</NavLink>
          )}
        </nav>
      </header>
      <main id="main" className={styles.main} tabIndex={-1}>
        <Outlet />
      </main>
    </div>
  )
}
