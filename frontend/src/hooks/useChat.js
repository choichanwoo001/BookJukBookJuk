import { useState, useRef, useEffect } from 'react'

/**
 * 채팅 공통 로직 훅.
 *
 * @param {(text: string, helpers?: { onDelta: (t: string) => void, onDone: (full?: string) => void, onError: (msg: string) => void }) => string | Promise<void>} handler
 *   두 가지 시그니처를 모두 지원한다:
 *     1) `(text) => string` — 동기/모의 응답을 한 번에 반환 (기존 동작 유지)
 *     2) `(text, helpers) => Promise<void>` — 스트리밍.
 *        helpers.onDelta(t)  : 토큰이 도착할 때마다 호출 (UI 누적은 훅이 처리)
 *        helpers.onDone(full): 정상 종료 (full 미제공 시 누적 텍스트 그대로 사용)
 *        helpers.onError(msg): 에러 메시지 표시
 */
export function useChat(handler) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const appendAssistantStub = () => {
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])
  }

  const updateLastAssistant = (updater) => {
    setMessages((prev) => {
      if (prev.length === 0) return prev
      const last = prev[prev.length - 1]
      if (last.role !== 'assistant') return prev
      const nextContent = typeof updater === 'function' ? updater(last.content) : updater
      return [...prev.slice(0, -1), { ...last, content: nextContent }]
    })
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    let result
    try {
      result = handler(text, {
        onDelta: (token) => {
          setMessages((prev) => {
            if (prev.length === 0 || prev[prev.length - 1].role !== 'assistant') {
              return [...prev, { role: 'assistant', content: token }]
            }
            const last = prev[prev.length - 1]
            return [...prev.slice(0, -1), { ...last, content: (last.content || '') + token }]
          })
        },
        onDone: (full) => {
          if (typeof full === 'string' && full.length > 0) {
            updateLastAssistant(full)
          }
        },
        onError: (msg) => {
          updateLastAssistant((current) => current || `(오류: ${msg || '알 수 없는 오류'})`)
        },
      })
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `(오류: ${err?.message || '핸들러 실행 실패'})` },
      ])
      setIsLoading(false)
      return
    }

    if (result && typeof result.then === 'function') {
      // 스트리밍: 첫 토큰 도착 전에 빈 말풍선을 미리 보여 타이핑 효과 자연스럽게.
      appendAssistantStub()
      try {
        await result
      } catch (err) {
        updateLastAssistant((current) => current || `(오류: ${err?.message || '스트림 실패'})`)
      } finally {
        setIsLoading(false)
      }
      return
    }

    // 동기 mock 호환 경로: setTimeout 으로 약간의 지연을 주어 타이핑 인디케이터 노출.
    const reply = typeof result === 'string' ? result : ''
    setTimeout(() => {
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
      setIsLoading(false)
    }, 600 + Math.random() * 400)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return { messages, setMessages, input, setInput, isLoading, scrollRef, handleSend, handleKeyDown }
}
