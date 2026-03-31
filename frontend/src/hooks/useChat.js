import { useState, useRef, useEffect } from 'react'

/**
 * 채팅 공통 로직 훅.
 * @param {(text: string) => string} getResponse - 사용자 메시지를 받아 응답 문자열을 반환하는 함수
 */
export function useChat(getResponse) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    setTimeout(() => {
      const reply = getResponse(text)
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

  return { messages, input, setInput, isLoading, scrollRef, handleSend, handleKeyDown }
}
