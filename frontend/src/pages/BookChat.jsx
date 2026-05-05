import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Navigate } from 'react-router-dom'
import { CHARACTER_IMG } from '../data/constants'
import BackButton from '../components/BackButton'
import { useChat } from '../hooks/useChat'
import { ensureBookChatSession, fetchBookDetail, streamBookChat } from '../data/bookApi'
import './BookChat.css'

function BookChatInner({ book, id }) {
  const [sessionStatus, setSessionStatus] = useState('building') // 'building' | 'ready' | 'error'
  const [sessionError, setSessionError] = useState('')

  const { messages, input, setInput, isLoading, scrollRef, handleSend, handleKeyDown } = useChat(
    (text, helpers) =>
      streamBookChat(id, text, {
        onDelta: helpers.onDelta,
        onDone: helpers.onDone,
        onRejected: (rejectionText) => {
          // 관련성 가드 탈락 → 거절 메시지를 일반 응답처럼 출력
          helpers.onDone(rejectionText)
        },
        onError: helpers.onError,
      }),
  )

  useEffect(() => {
    if (!id) return undefined
    let cancelled = false
    setSessionStatus('building')
    setSessionError('')
    ensureBookChatSession(id)
      .then(() => {
        if (cancelled) return
        setSessionStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setSessionStatus('error')
        setSessionError(err?.message || '세션 준비 실패')
      })
    return () => {
      cancelled = true
    }
  }, [id])

  const sendDisabled = !input.trim() || isLoading || sessionStatus !== 'ready'

  return (
    <div className="book-chat-page">
      <header className="book-chat-header">
        <BackButton className="book-chat-back" to={`/book/${id}`} label="뒤로" />
        <div className="book-chat-header-title">
          <span className="book-chat-header-label">상세 토크</span>
          <span className="book-chat-header-book">{book.title}</span>
        </div>
        <span className="book-chat-header-spacer" />
      </header>

      <section className="book-chat-character-panel" aria-label="캐릭터 안내">
        <div className="book-chat-welcome-character">
          <img src={CHARACTER_IMG} alt="캐릭터" />
        </div>
        <p className="book-chat-welcome-text">안녕하세요! 저는 이 책의 친구예요.</p>
        <p className="book-chat-welcome-sub">{book.title}에 대해 궁금한 점을 물어보세요.</p>
        {sessionStatus === 'building' && (
          <p className="book-chat-welcome-sub" style={{ opacity: 0.7 }}>
            책 자료를 준비 중이에요... (최대 1분 정도 걸릴 수 있어요)
          </p>
        )}
        {sessionStatus === 'error' && (
          <p className="book-chat-welcome-sub" style={{ opacity: 0.8 }}>
            세션 준비 실패: {sessionError}
          </p>
        )}
      </section>

      <div className="book-chat-messages" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`book-chat-bubble-wrap ${msg.role === 'user' ? 'user' : 'assistant'}`}
          >
            {msg.role === 'assistant' && (
              <div className="book-chat-avatar">
                <img src={CHARACTER_IMG} alt="캐릭터" />
              </div>
            )}
            <div className={`book-chat-bubble ${msg.role}`}>
              <span>{msg.content || (msg.role === 'assistant' && isLoading ? '•••' : '')}</span>
            </div>
          </div>
        ))}

        {messages.length === 0 && (
          <p className="book-chat-empty-hint">
            {sessionStatus === 'ready'
              ? '메시지를 입력하면 대화가 시작돼요.'
              : sessionStatus === 'building'
                ? '책 자료를 준비 중이에요...'
                : '세션을 준비할 수 없어요.'}
          </p>
        )}
      </div>

      <footer className="book-chat-footer">
        <div className="book-chat-input-wrap">
          <input
            type="text"
            className="book-chat-input"
            placeholder={
              sessionStatus === 'ready' ? '메시지를 입력하세요' : '준비 중이에요...'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sessionStatus !== 'ready' || isLoading}
            maxLength={500}
          />
          <button
            type="button"
            className="book-chat-send"
            onClick={handleSend}
            disabled={sendDisabled}
            aria-label="보내기"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </footer>
    </div>
  )
}

function BookChat() {
  const { id } = useParams()
  const [book, setBook] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    if (!id) return undefined
    setIsLoading(true)
    fetchBookDetail(id)
      .then((data) => {
        if (cancelled) return
        setBook(data)
      })
      .catch(() => {
        if (cancelled) return
        setBook(null)
      })
      .finally(() => {
        if (cancelled) return
        setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  if (!book && !isLoading) {
    return <Navigate to="/" replace />
  }
  if (!book) return null

  return <BookChatInner book={book} id={id} />
}

export default BookChat
