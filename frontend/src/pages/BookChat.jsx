import { useState, useRef, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getBookById } from '../data/dummyBooks'
import { Navigate } from 'react-router-dom'
import './BookChat.css'

const CHARACTER_IMG = '/images/custom-character.png'

/** 책 정보를 바탕으로 캐릭터의 목업 응답을 생성합니다. */
function getMockResponse(book, userMessage) {
  const msg = userMessage.toLowerCase().trim()
  const greetings = ['안녕', 'hello', '하이', '반가', 'ㅎㅇ']

  if (greetings.some((g) => msg.includes(g))) {
    return `안녕하세요! 저는 이 책의 친구예요. ${book.title}에 대해 궁금한 게 있으시면 편하게 물어보세요!`
  }
  if (msg.includes('줄거리') || msg.includes('내용') || msg.includes('스토리')) {
    return `${book.title}은 ${book.category} 분야의 작품이에요. ${book.pages}쪽 분량으로 읽기에 부담 없는 길이예요. 인기 코멘트를 보면 "${book.popularComments?.[0] || '많은 분들이 좋아하셨어요'}"라고 하시는 분이 많아요.`
  }
  if (msg.includes('작가') || msg.includes('저자')) {
    return `이 책의 작가에 대해서는 아직 제가 자세히 알지 못해요. 하지만 ${book.category} 분야에서 쓰신 분이시에요. 더 알고 싶으시면 검색해 보시거나 서점에서 소개를 확인해 보세요!`
  }
  if (msg.includes('추천') || msg.includes('어때') || msg.includes('읽을만')) {
    return `평균 별점 ${typeof book.rating === 'number' ? book.rating.toFixed(1) : book.rating}점이에요. "${book.popularComments?.[0] || '독자들이 좋아하는 책'}"이란 말씀이 많아요. ${book.ageRating} 연령이라 많은 분들이 읽으실 수 있어요.`
  }
  if (msg.includes('카테고리') || msg.includes('장르')) {
    return `${book.title}은 ${book.category} 장르예요. ${book.pages}쪽, ${book.productionYear}년에 출간되었어요.`
  }
  if (msg.includes('감사') || msg.includes('고마') || msg.includes('thx')) {
    return '천만에요! 더 궁금한 게 있으면 언제든 물어보세요. 책 읽는 즐거움이 가득하길 바랄게요!'
  }
  if (msg.includes('?')) {
    return `${book.title}에 대한 질문이시군요. 제가 아는 범위에서 말씀드리면, 이 책은 ${book.category} 분야이고 ${book.pages}쪽 분량이에요. 구체적으로 어떤 부분이 궁금하신가요?`
  }

  return `${book.title}에 대해 관심 가져주셔서 감사해요. 줄거리, 작가, 추천 이유, 카테고리 같은 걸 물어보시면 더 자세히 말씀드릴 수 있어요!`
}

function BookChat() {
  const { id } = useParams()
  const navigate = useNavigate()
  const scrollRef = useRef(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const book = getBookById(id ?? '')

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  if (!book) {
    return <Navigate to="/" replace />
  }

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    setTimeout(() => {
      const reply = getMockResponse(book, text)
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

  return (
    <div className="book-chat-page">
      <header className="book-chat-header">
        <button
          type="button"
          className="book-chat-back"
          onClick={() => navigate(`/book/${id}`)}
          aria-label="뒤로"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
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
              <span>{msg.content}</span>
            </div>
          </div>
        ))}

        {messages.length === 0 && (
          <p className="book-chat-empty-hint">메시지를 입력하면 대화가 시작돼요.</p>
        )}

        {isLoading && (
          <div className="book-chat-bubble-wrap assistant">
            <div className="book-chat-avatar">
              <img src={CHARACTER_IMG} alt="캐릭터" />
            </div>
            <div className="book-chat-bubble assistant loading">
              <span className="book-chat-typing">•••</span>
            </div>
          </div>
        )}
      </div>

      <footer className="book-chat-footer">
        <div className="book-chat-input-wrap">
          <input
            type="text"
            className="book-chat-input"
            placeholder="메시지를 입력하세요"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            maxLength={500}
          />
          <button
            type="button"
            className="book-chat-send"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
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

export default BookChat
