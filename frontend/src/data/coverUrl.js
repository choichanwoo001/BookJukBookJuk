import { hashString } from './hashString'
import { APP_IMAGES } from './imagePool'

/** 비우면 상대 경로 `/api` (Vite dev/preview가 백엔드로 프록시). 프로덕션 빌드 시 백엔드 절대 URL. */
function apiBase() {
  const raw = import.meta.env.VITE_API_BASE_URL ?? ''
  return String(raw).replace(/\/$/, '')
}

/** Open Library Covers API — 키 불필요 (프록시 폴백·정적 배포용). */
export function openLibraryCoverUrl(isbn13) {
  const clean = String(isbn13 ?? '').replace(/[^0-9X]/gi, '')
  if (clean.length !== 13) return null
  return `https://covers.openlibrary.org/b/isbn/${clean}-M.jpg`
}

export function pickFallbackCoverById(id) {
  return APP_IMAGES[hashString(String(id)) % APP_IMAGES.length]
}

/**
 * 백엔드 GET /api/book-cover → 알라딘 표지 URL로 302, 실패 시 Open Library.
 * 로컬: Vite가 /api 를 FastAPI(기본 8000)로 프록시.
 */
export function aladinProxyCoverUrl(isbn13) {
  const clean = String(isbn13 ?? '').replace(/[^0-9X]/gi, '')
  if (clean.length !== 13) return null
  const base = apiBase()
  const path = `/api/book-cover?isbn13=${encodeURIComponent(clean)}`
  return base ? `${base}${path}` : path
}

/**
 * DB에 표지 URL이 있으면 우선.
 * 없으면 ISBN-13이면 알라딘 프록시(실패 시 서버가 Open Library로 넘김), 아니면 로컬 풀.
 */
export function coverForListBook(id, coverFromDb) {
  if (coverFromDb && String(coverFromDb).trim()) return String(coverFromDb).trim()
  const clean = String(id ?? '').replace(/[^0-9X]/gi, '')
  if (clean.length === 13) return aladinProxyCoverUrl(clean)
  return openLibraryCoverUrl(id) ?? pickFallbackCoverById(id)
}
