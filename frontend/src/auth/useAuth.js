import { useSyncExternalStore } from 'react'
import { auth } from './auth.js'

export function useAuth() {
  return useSyncExternalStore(auth.subscribe, auth.getSnapshot)
}
