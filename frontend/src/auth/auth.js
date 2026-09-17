import { createAuthSession } from './session.js'

let storage
try {
  storage = window.sessionStorage
} catch {
  /* In-memory login remains available. */
}

export const auth = createAuthSession({ storage })
