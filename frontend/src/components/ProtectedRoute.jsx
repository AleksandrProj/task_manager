import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from '../auth/useAuth.js'
import SessionStatus from './SessionStatus.jsx'

export default function ProtectedRoute() {
  const session = useAuth()
  const location = useLocation()
  if (session.status === 'loading' || session.status === 'error') {
    return <SessionStatus {...session} />
  }
  if (!session.user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search + location.hash }}
      />
    )
  }
  return <Outlet />
}
