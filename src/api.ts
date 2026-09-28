let csrf = ''
export function setCsrf(value: string) { csrf = value }
export async function api<T = unknown>(path: string, method = 'GET', data?: unknown): Promise<T> {
  const response = await fetch('/api' + path, { method, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: data === undefined ? undefined : JSON.stringify(data) })
  if (!response.ok) {
    let message = 'ارتباط با سامانه برقرار نشد.'
    try { const body = await response.json(); message = typeof body.detail === 'string' ? body.detail : 'مقادیر فرم را بررسی کنید.' } catch { /* Generic message for invalid server responses. */ }
    if (response.status === 401 && path !== '/auth/login') window.dispatchEvent(new Event('session-expired'))
    throw new Error(message)
  }
  return response.json() as Promise<T>
}
export async function download(path: string, filename: string) {
  const response = await fetch('/api' + path, { credentials: 'same-origin' })
  if (!response.ok) throw new Error('دریافت فایل انجام نشد. دسترسی خود را بررسی کنید.')
  const url = URL.createObjectURL(await response.blob())
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}
