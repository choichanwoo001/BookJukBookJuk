function buildApiUrl(path) {
  const base = import.meta.env.VITE_API_BASE_URL ?? ''
  if (!base) return path
  return `${String(base).replace(/\/$/, '')}${path}`
}

async function fetchJson(path) {
  const response = await fetch(buildApiUrl(path))
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const detail = err.detail ?? response.statusText
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json()
}

export async function fetchHomeSections(limit = 4, userId = 'dev_user_1') {
  const q = new URLSearchParams({
    limit: String(limit),
    user_id: userId,
  })
  return fetchJson(`/api/home-sections?${q.toString()}`)
}

export async function fetchSectionBooks(sectionId, limit = 20, userId = 'dev_user_1') {
  const q = new URLSearchParams({
    limit: String(limit),
    user_id: userId,
  })
  return fetchJson(`/api/sections/${encodeURIComponent(sectionId)}/books?${q.toString()}`)
}

export async function fetchBooksSearch(query, limit = 30) {
  const q = new URLSearchParams({
    q: query,
    limit: String(limit),
  })
  return fetchJson(`/api/books/search?${q.toString()}`)
}

export async function fetchBookDetail(bookId) {
  return fetchJson(`/api/books/${encodeURIComponent(bookId)}`)
}

export async function fetchBookComments(bookId, limit = 20) {
  const q = new URLSearchParams({ limit: String(limit) })
  return fetchJson(`/api/books/${encodeURIComponent(bookId)}/comments?${q.toString()}`)
}

export async function fetchBookCommentDetail(bookId, commentId) {
  return fetchJson(`/api/books/${encodeURIComponent(bookId)}/comments/${encodeURIComponent(commentId)}`)
}

export async function fetchUserCollections(userId = 'dev_user_1') {
  return fetchJson(`/api/users/${encodeURIComponent(userId)}/collections`)
}

export async function fetchCollectionDetail(collectionId) {
  return fetchJson(`/api/collections/${encodeURIComponent(collectionId)}`)
}
