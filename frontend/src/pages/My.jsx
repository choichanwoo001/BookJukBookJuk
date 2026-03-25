import { useNavigate } from 'react-router-dom'
import { pickImageBySeed } from '../data/imagePool'
import './My.css'

// 간단한 강아지 라인 일러스트 SVG
function DogIllustration() {
  return (
    <svg viewBox="0 0 120 120" className="dog-illustration" fill="none" stroke="currentColor" strokeWidth="1.5">
      <ellipse cx="60" cy="70" rx="28" ry="30" />
      <circle cx="60" cy="45" r="22" />
      <ellipse cx="45" cy="42" rx="4" ry="5" fill="currentColor" />
      <ellipse cx="75" cy="42" rx="4" ry="5" fill="currentColor" />
      <path d="M55 55 Q60 60 65 55" strokeLinecap="round" />
      <path d="M35 65 Q20 55 25 45" strokeLinecap="round" />
      <path d="M85 65 Q100 55 95 45" strokeLinecap="round" />
      <path d="M35 85 Q35 100 45 98" strokeLinecap="round" />
      <path d="M85 85 Q85 100 75 98" strokeLinecap="round" />
    </svg>
  )
}

function My() {
  const navigate = useNavigate()

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
          <div className="profile-illustration">
            <DogIllustration />
          </div>
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

        <button className="taste-analysis-bar">
          <span>취향분석</span>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>

        <div className="collection-box">
          <span>컬렉션</span>
        </div>

        <button className="qr-link-bar">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
            <rect x="14" y="14" width="3" height="3" />
            <rect x="19" y="14" width="2" height="2" />
          </svg>
          <span>qr로 매장 기기와 연동하기</span>
        </button>
      </main>
    </div>
  )
}

export default My
