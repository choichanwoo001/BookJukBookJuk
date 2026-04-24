import { requestJson } from './apiClient'

export async function fetchHomeSections(limit = 4, userId = 'dev_user_1') {
  const q = new URLSearchParams({
    limit: String(limit),
    user_id: userId,
  })
  return requestJson(`/api/home-sections?${q.toString()}`)
}

export async function fetchSectionBooks(sectionId, limit = 20, userId = 'dev_user_1') {
  const q = new URLSearchParams({
    limit: String(limit),
    user_id: userId,
  })
  return requestJson(`/api/sections/${encodeURIComponent(sectionId)}/books?${q.toString()}`)
}

export async function fetchBooksSearch(query, limit = 30) {
  const q = new URLSearchParams({
    q: query,
    limit: String(limit),
  })
  return requestJson(`/api/books/search?${q.toString()}`)
}

export async function fetchBookDetail(bookId) {
  return requestJson(`/api/books/${encodeURIComponent(bookId)}`)
}

export async function fetchBookComments(bookId, limit = 20) {
  const q = new URLSearchParams({ limit: String(limit) })
  return requestJson(`/api/books/${encodeURIComponent(bookId)}/comments?${q.toString()}`)
}

export async function fetchBookCommentDetail(bookId, commentId) {
  return requestJson(`/api/books/${encodeURIComponent(bookId)}/comments/${encodeURIComponent(commentId)}`)
}

export async function fetchUserCollections(userId = 'dev_user_1') {
  return requestJson(`/api/users/${encodeURIComponent(userId)}/collections`)
}

export async function fetchCollectionDetail(collectionId) {
  return requestJson(`/api/collections/${encodeURIComponent(collectionId)}`)
}
