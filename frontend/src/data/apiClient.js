function buildApiUrl(path) {
  const base = import.meta.env.VITE_API_BASE_URL ?? ''
  if (!base) return path
  return `${String(base).replace(/\/$/, '')}${path}`
}

export async function requestJson(path) {
  const response = await fetch(buildApiUrl(path))
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const detail = err.detail ?? response.statusText
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json()
}
