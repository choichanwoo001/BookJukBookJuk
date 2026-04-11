import staticCatalog from '../data/booksCatalog.json'
import { getSupabase } from '../lib/supabaseClient.js'

let cached = null
let initPromise = null

const BOOK_COLUMNS =
  'id, title, authors, description, author_bio, editorial_review, publisher, published_year, kdc_class_no, kdc_class_nm, sector, cover_image_url'

function normalizeBookRow(row) {
  return {
    id: String(row.id),
    title: row.title ?? '',
    authors: row.authors ?? '',
    description: row.description ?? '',
    author_bio: row.author_bio ?? '',
    editorial_review: row.editorial_review ?? '',
    publisher: row.publisher ?? '',
    published_year: row.published_year != null ? String(row.published_year) : '',
    kdc_class_no: row.kdc_class_no ?? '',
    kdc_class_nm: row.kdc_class_nm ?? '',
    sector: row.sector != null ? Number(row.sector) : 0,
    cover_image_url: row.cover_image_url ?? '',
  }
}

async function loadFromSupabase() {
  const supabase = getSupabase()
  if (!supabase) return null
  const { data, error } = await supabase.from('books').select(BOOK_COLUMNS).order('id', { ascending: true })
  if (error) {
    console.warn('[catalog] Supabase 조회 실패 — 로컬 JSON 사용', error.message)
    return null
  }
  if (!Array.isArray(data) || data.length === 0) {
    console.warn('[catalog] Supabase books 테이블이 비어 있음 — 로컬 JSON 사용')
    return null
  }
  return data.map(normalizeBookRow)
}

/**
 * 앱 진입 시 한 번 호출. Supabase에 행이 있으면 그걸 쓰고, 없거나 실패 시 booksCatalog.json.
 */
export function initCatalog() {
  if (cached) return Promise.resolve()
  if (initPromise) return initPromise
  initPromise = (async () => {
    const fromDb = await loadFromSupabase()
    cached = fromDb ?? staticCatalog
  })()
  return initPromise
}

/** initCatalog 완료 후 목록 (미초기화 시 정적 JSON으로 폴백). */
export function getCatalogRows() {
  return cached ?? staticCatalog
}
