export function getReturnPath(path) {
  return typeof path === 'string' && /^\/tasks(?:\/|\?|#|$)/.test(path)
    ? path
    : '/tasks'
}
