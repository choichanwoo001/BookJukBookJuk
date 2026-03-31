import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './BookChat.css'

const CHARACTER_IMG = '/images/custom-character.png'

/** 마이페이지 캐릭터의 목업 응답 */
function getMockResponse(userMessage) {
  const msg = userMessage.toLowerCase().trim()
  const greetings = ['안녕', 'hello', '하이', '반가', 'ㅎㅇ']

  if (greetings.some((g) => msg.includes(g))) {
    return '안녕하세요! 저는 북적북적의 친구예요. 오늘은 어떤 책을 읽으셨나요? 편하게 이야기해 주세요!'
  }
  if (msg.includes('추천') || msg.includes('추천해')) {
    return '요즘 인기 있는 책들이 많아요! 취향분석을 통해 나에게 딱 맞는 책을 추천받아 보세요. 마이페이지에서 취향분석을 확인해 보실 수 있어요.'
  }
  if (msg.includes('책') && (msg.includes('뭐') || msg.includes('어떤'))) {
    return '좋은 질문이에요! 북적북적에서 다양한 책을 만나보실 수 있어요. 홈에서 인기 도서를, 검색에서 원하는 키워드로 찾아보세요.'
  }
  if (msg.includes('감사') || msg.includes('고마') || msg.includes('thx')) {
    return '천만에요! 더 궁금한 게 있으면 언제든 물어보세요. 즐거운 독서 되세요!'
  }
  if (msg.includes('읽') || msg.includes('독서')) {
    return '책 읽는 시간은 참 좋죠! 북적북적 라이브러리에서 읽은 책을 기록하고, 다른 사람들과 소통해 보세요.'
  }
  if (msg.includes('컬렉션') || msg.includes('모음')) {
    return '마이페이지에서 컬렉션을 만들어 나만의 책 모음을 꾸밀 수 있어요. 관심 있는 주제별로 정리해 보세요!'
  }

  return '흥미로운 이야기네요! 책 추천, 독서 기록, 취향분석 등에 대해 물어보시면 도움을 드릴게요.'
}

function MyChat() {
  const navigate = useNavigate()
  const scrollRef = useRef(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    setTimeout(() => {
      const reply = getMockResponse(text)
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
          onClick={() => navigate('/my')}
          aria-label="뒤로"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <div className="book-chat-header-title">
          <span className="book-chat-header-label">상세 토크</span>
          <span className="book-chat-header-book">북적북적 친구</span>
        </div>
        <span className="book-chat-header-spacer" />
      </header>

      <section className="book-chat-character-panel" aria-label="캐릭터 안내">
        <div className="book-chat-welcome-character">
          <img src={CHARACTER_IMG} alt="캐릭터" onError={(e) => { e.target.style.display = 'none' }} />
        </div>
        <p className="book-chat-welcome-text">안녕하세요! 저는 북적북적의 친구예요.</p>
        <p className="book-chat-welcome-sub">책 추천, 독서 기록, 취향분석 등 무엇이든 물어보세요.</p>
      </section>

      <div className="book-chat-messages" ref={scrollRef}>

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`book-chat-bubble-wrap ${msg.role === 'user' ? 'user' : 'assistant'}`}
          >
            {msg.role === 'assistant' && (
              <div className="book-chat-avatar">
                <img src={CHARACTER_IMG} alt="캐릭터" onError={(e) => { e.target.style.display = 'none' }} />
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
              <img src={CHARACTER_IMG} alt="캐릭터" onError={(e) => { e.target.style.display = 'none' }} />
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

export default MyChat
