import { useNavigate } from 'react-router-dom'
import { pickImageBySeed } from '../data/imagePool'
import { SECTIONS } from '../data/dummyBooks'
import './My.css'

function My() {
  const navigate = useNavigate()
  const collections = SECTIONS.map((section) => ({
    id: section.id,
    title: section.title,
    books: section.books.slice(0, 4),
  }))

  return (
    <div className="my-page">
      <header className="my-header">
        <h1 className="my-header-title">나의 북적북적</h1>
        <div className="my-header-actions">
          <button
            className="icon-btn"
            onClick={() => navigate('/search')}
            aria-label="검색"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
          </button>
          <button className="icon-btn" aria-label="메뉴">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        </div>
      </header>

      <main className="my-content">
        <section className="profile-section">
          <button
            type="button"
            className="profile-illustration profile-illustration-btn"
            onClick={() => navigate('/my/chat')}
            aria-label="캐릭터와 대화하기"
          >
            <img
              src="/images/custom-character.png"
              alt="마이페이지 캐릭터"
              className="character-illustration"
            />
          </button>
          <div className="profile-info">
            <button
              type="button"
              className="profile-avatar-wrap profile-avatar-btn"
              onClick={() => navigate('/my/chat')}
              aria-label="캐릭터와 대화하기"
            >
              <div className="profile-avatar">
                <img src={pickImageBySeed(105)} alt="프로필" onError={(e) => { e.target.onError = null; e.target.style.display = 'none'; }} />
              </div>
            </button>
            <div className="profile-details">
              <h2 className="profile-name">최찬우</h2>
              <div className="profile-stats">
                <span>팔로우 0</span>
                <span className="stats-divider">|</span>
                <span>팔로워 0</span>
              </div>
              <div className="profile-buttons">
                <button className="profile-btn">프로필 수정</button>
                <button className="profile-btn">프로필 공유</button>
              </div>
            </div>
          </div>
        </section>

        <div className="activity-stats">
          <div className="stat-item">
            <span className="stat-value">0</span>
            <span className="stat-label">평가</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">0</span>
            <span className="stat-label">평가</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">0</span>
            <span className="stat-label">평가</span>
          </div>
        </div>

        <section className="taste-analysis-section" aria-label="취향분석">
          <h2 className="taste-analysis-title">취향분석</h2>
          <span className="taste-analysis-badge">#별점분포</span>
          <p className="taste-analysis-summary">작품을 남들보다 진지하고 비판적으로 보는 '지성파'.</p>

          <div className="taste-analysis-chart-wrap" aria-hidden="true">
            <span className="taste-analysis-scale taste-analysis-scale-left">0.5</span>
            <div className="taste-analysis-chart">
              {[10, 12, 18, 34, 52, 48, 48, 42, 24, 14].map((height, index) => (
                <div
                  key={`taste-bar-${index}`}
                  className={`taste-analysis-bar ${index === 4 ? 'active' : ''}`}
                  style={{ height: `${height}px` }}
                />
              ))}
            </div>
            <span className="taste-analysis-scale taste-analysis-scale-right">5</span>
            <span className="taste-analysis-highlight">2.5</span>
          </div>

          <button
            type="button"
            className="taste-analysis-more-btn"
            onClick={() => navigate('/my/taste-analysis')}
          >
            <span>모든 분석 보기</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </section>

        <section className="my-collection-section" aria-label="내 컬랙션">
          <h2 className="my-collection-title">내 컬랙션</h2>
          <div className="my-collection-list" role="list">
            {collections.map((collection) => (
              <button
                key={collection.id}
                type="button"
                className="my-collection-card"
                role="listitem"
                onClick={() => navigate(`/collection/${collection.id}`)}
                aria-label={`${collection.title} 컬렉션 보기`}
              >
                <div className="my-collection-grid">
                  {collection.books.map((book) => (
                    <div key={book.id} className="my-collection-cover">
                      <img src={book.image} alt={book.title} />
                    </div>
                  ))}
                </div>
                <p className="my-collection-name">{collection.title}</p>
              </button>
            ))}
          </div>
        </section>

      </main>

      <button className="qr-link-bar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" />
          <rect x="14" y="3" width="7" height="7" />
          <rect x="3" y="14" width="7" height="7" />
          <rect x="14" y="14" width="3" height="3" />
          <rect x="19" y="14" width="2" height="2" />
        </svg>
        <span>qr로 매장 기기와 연동하기</span>
      </button>
    </div>
  )
}

export default My
