import { buildApiUrl, requestJson } from './apiClient'

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

/**
 * 책 채팅 세션을 미리 빌드한다 (캐시 hit 면 즉시 반환).
 * 첫 빌드는 정보 수집 + 임베딩으로 수십 초 걸릴 수 있다.
 */
export async function ensureBookChatSession(bookId, { signal } = {}) {
  const response = await fetch(buildApiUrl(`/api/books/${encodeURIComponent(bookId)}/chat/session`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
    signal,
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const detail = err.detail ?? response.statusText
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return response.json()
}

export async function resetBookChat(bookId) {
  const response = await fetch(buildApiUrl(`/api/books/${encodeURIComponent(bookId)}/chat/reset`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  })
  if (!response.ok) return { status: 'error' }
  return response.json()
}

/**
 * SSE 로 책 채팅 응답을 스트리밍한다.
 * 콜백:
 *   onDelta(text)    토큰이 도착할 때마다 (누적이 아닌 부분 텍스트)
 *   onDone(finalText) 정상 완료 (서버가 모은 최종 답변)
 *   onRejected(text) 관련성 가드 탈락 (이 책과 무관한 질문)
 *   onError(message) 서버/네트워크 에러
 *   onReady()        세션 준비 완료 (빌드 종료 직후)
 * 반환값: 스트림이 종료되면 resolve.
 */
export async function streamBookChat(
  bookId,
  question,
  { onDelta, onDone, onRejected, onError, onReady, signal } = {},
) {
  let response
  try {
    response = await fetch(buildApiUrl(`/api/books/${encodeURIComponent(bookId)}/chat/messages`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({ question }),
      signal,
    })
  } catch (err) {
    onError?.(err?.message || '네트워크 오류')
    return
  }

  if (!response.ok || !response.body) {
    let detail = response.statusText
    try {
      const err = await response.json()
      if (err?.detail) detail = err.detail
    } catch (_) {
      /* ignore */
    }
    onError?.(typeof detail === 'string' ? detail : JSON.stringify(detail))
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let finalText = ''
  let done = false

  const handleEvent = (rawBlock) => {
    const lines = rawBlock.split(/\r?\n/)
    let evt = 'message'
    const dataParts = []
    for (const line of lines) {
      if (!line) continue
      if (line.startsWith(':')) continue
      if (line.startsWith('event:')) {
        evt = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataParts.push(line.slice(5).replace(/^\s/, ''))
      }
    }
    if (dataParts.length === 0) return
    let payload = {}
    try {
      payload = JSON.parse(dataParts.join('\n'))
    } catch (_) {
      payload = { text: dataParts.join('\n') }
    }
    if (evt === 'ready') {
      onReady?.()
    } else if (evt === 'delta') {
      const t = payload.text || ''
      finalText += t
      onDelta?.(t)
    } else if (evt === 'rejected') {
      onRejected?.(payload.text || '')
    } else if (evt === 'done') {
      done = true
      onDone?.(payload.text || finalText)
    } else if (evt === 'error') {
      onError?.(payload.detail || payload.text || '서버 오류')
    }
  }

  try {
    while (true) {
      const { value, done: streamDone } = await reader.read()
      if (streamDone) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)
        handleEvent(block)
      }
    }
    if (buffer.trim()) handleEvent(buffer)
    if (!done) onDone?.(finalText)
  } catch (err) {
    onError?.(err?.message || '스트림 오류')
  }
}
