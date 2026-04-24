import { coverForListBook } from './coverUrl'
import { hashString } from './hashString'
import { requestJson } from './apiClient'

function ratingForId(id) {
  const h = hashString(String(id))
  return Math.round((4 + (h % 10) / 10) * 10) / 10
}

/**
 * GET /api/recommendations (Vite dev: 프록시 → FastAPI)
 * @returns {Promise<{ items: Array }>}
 */
export async function fetchRecommendations(limit = 4) {
  const path = `/api/recommendations?limit=${encodeURIComponent(String(limit))}`
  return requestJson(path)
}

/** API 한 권 → BookSection용 목록 아이템 (dummyBooks toListBook과 유사 필드). */
export function apiItemToListBook(item) {
  const id = String(item.id || item.isbn13 || '')
  return {
    id,
    title: item.title || '',
    authors: item.authors || '',
    description: '',
    rating: ratingForId(id),
    image: coverForListBook(id, ''),
  }
}

export function apiItemsToListBooks(items) {
  if (!Array.isArray(items)) return []
  return items.map(apiItemToListBook)
}
