import { useState, useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTab } from '../hooks/useTab'
import { ALL_BOOKS } from '../data/dummyBooks'
import './Search.css'

const TABS = [
  { id: 'book', label: '책' },
  { id: 'author', label: '작가' },
  { id: 'collection', label: '컬렉션' },
  { id: 'user', label: '유저' },
]

function Search() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const { activeTab, setActiveTab } = useTab('book')

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []

    if (activeTab === 'book') {
      return ALL_BOOKS.filter(
        (b) =>
          b.title.toLowerCase().includes(q) ||
          (b.authors && b.authors.toLowerCase().includes(q))
      )
    }

    // 작가/컬렉션/유저는 추후 API 연동 시 구현
    return []
  }, [query, activeTab])

  const showResults = query.trim().length > 0

  return (
    <div className="search-page">
      <header className="search-header">
        <div className="search-input-wrap">
          <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="책 제목, 작가로 검색"
            className="search-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button
              type="button"
              className="search-clear"
              onClick={() => setQuery('')}
              aria-label="검색어 지우기"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <button className="search-cancel" onClick={() => navigate(-1)}>취소</button>
      </header>

      <nav className="search-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`search-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="search-content">
        {!showResults && (
          <p className="empty-message">검색어를 입력해 주세요</p>
        )}

        {showResults && activeTab === 'book' && results.length === 0 && (
          <p className="empty-message">검색 결과가 없습니다</p>
        )}

        {showResults && activeTab !== 'book' && (
          <p className="empty-message">이 탭의 검색은 준비 중입니다</p>
        )}

        {showResults && activeTab === 'book' && results.length > 0 && (
          <ul className="search-results">
            {results.map((book) => (
              <li key={book.id} className="search-result-item">
                <Link to={`/book/${book.id}`} className="search-result-link">
                  <div className="search-result-thumb">
                    <img src={book.image} alt={book.title} />
                  </div>
                  <div className="search-result-info">
                    <h3 className="search-result-title">{book.title}</h3>
                    <p className="search-result-meta">
                      {book.category || '책'} · {book.productionYear || '-'} · {book.authors || '-'}
                    </p>
                    {book.rating && (
                      <span className="search-result-badge">평점 {book.rating}</span>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}

export default Search
