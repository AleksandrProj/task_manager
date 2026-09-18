import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import AppLayout from './components/AppLayout.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import PlaceholderPage from './pages/PlaceholderPage.jsx'
import TasksPage from './pages/TasksPage.jsx'
import AddTasksPage from './pages/AddTasksPage.jsx'
import TaskDetailPage from './pages/TaskDetailPage.jsx'
import LoadingState from './components/ui/LoadingState.jsx'
import LoginPage from './pages/LoginPage.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { auth } from './auth/auth.js'

const ComponentsPage = import.meta.env.DEV
  ? lazy(() => import('./pages/ComponentsPage.jsx'))
  : null

export default function App() {
  useEffect(() => {
    void auth.restore()
  }, [])
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {import.meta.env.DEV && (
          <Route
            path="ui"
            element={
              <Suspense fallback={<LoadingState />}>
                <ComponentsPage />
              </Suspense>
            }
          />
        )}
        <Route index element={<Navigate to="/tasks" replace />} />
        <Route path="login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="tasks" element={<TasksPage />} />
          <Route path="tasks/new" element={<AddTasksPage />} />
          <Route path="tasks/:id" element={<TaskDetailPage />} />
          <Route
            path="tasks/:id/edit"
            element={
              <PlaceholderPage
                title="Редактирование задачи"
                description="Измените описание, приоритет или исполнителя."
              />
            }
          />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
