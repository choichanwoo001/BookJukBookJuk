import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { APP_IMAGES } from '../data/imagePool'
import BookCard from '../components/BookCard'
import './Library.css'

const TABS = [
  { id: 'rated', label: '평가한' },
  { id: 'liked', label: '찜한' },
  { id: 'reading', label: '읽는중' },
  { id: 'shopping', label: '쇼핑 리스트' },
]

const makeLibraryBooks = (tab, titles) => (
  titles.map((title, i) => ({
    id: `${tab}-${i + 1}`,
    title,
    rating: Number((4.2 + (i % 4) * 0.2).toFixed(1)),
    image: APP_IMAGES[i % APP_IMAGES.length],
  }))
)

const LIBRARY_BOOKS = {
  rated: makeLibraryBooks('rated', [
    '나의 완벽한 자객님',
    '절창',
    '내 심장을 쏴라',
    '안녕이라 그랬어',
    '인터메조',
  ]),
  liked: makeLibraryBooks('liked', [
    '달러구트 꿈 백화점',
    '불편한 편의점',
    '작별하지 않는다',
    '오늘 밤, 세계에서',
    '모순',
  ]),
  reading: makeLibraryBooks('reading', [
    '클린 코드',
    '이펙티브 자바',
    '프로젝트 헤일메리',
    '해리포터 시리즈',
    '역행자',
  ]),
  shopping: makeLibraryBooks('shopping', [
    '자존감 수업',
    '부의 추월차선',
    '스타트업 한국',
    '미래학 콘서트',
    '일의 기쁨과 슬픔',
  ]),
}

function Library() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('rated')
  const activeBooks = LIBRARY_BOOKS[activeTab] ?? []

  return (
    <div className="library-page">
      <header className="library-header">
        <button
          className="back-btn"
          onClick={() => navigate(-1)}
          aria-label="뒤로가기"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="library-title">책 보관함</h1>
      </header>

      <div className="library-tabs">
        <div className="tabs-underline" />
        <div className="tabs-list">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`tab-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <main className="library-content">
        <div className="library-grid">
          {activeBooks.map((item) => (
            <BookCard key={item.id} book={item} variant="grid" />
          ))}
        </div>
      </main>
    </div>
  )
}

export default Library
