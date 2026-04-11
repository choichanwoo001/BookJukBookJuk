import { createClient } from '@supabase/supabase-js'

let client = null

/** VITE_* 가 없으면 null (로컬 JSON만 사용). */
export function getSupabase() {
  if (client) return client
  const url = import.meta.env.VITE_SUPABASE_URL
  const key = import.meta.env.VITE_SUPABASE_ANON_KEY
  if (!url || !key) return null
  client = createClient(url, key)
  return client
}
