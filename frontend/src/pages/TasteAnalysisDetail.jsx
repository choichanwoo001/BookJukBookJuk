import { useNavigate } from 'react-router-dom'
import './TasteAnalysisDetail.css'

const RATING_BARS = [44, 62, 34, 74, 82, 32, 22, 98, 66, 88]
const PREFER_TAGS = [
  { label: '자기계발', size: 'lg' },
  { label: '인생', size: 'xl' },
  { label: '공부', size: 'sm' },
]
const PREFER_GENRES = [
  { genre: '추리', count: '3권' },
  { genre: '자기계발', count: '6권' },
]

function TasteAnalysisDetail() {
  const navigate = useNavigate()

  return (
    <div className="taste-detail-page">
      <header className="taste-detail-header">
        <button
          type="button"
          className="taste-detail-back-btn"
          onClick={() => navigate(-1)}
          aria-label="뒤로가기"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="taste-detail-title">취향분석</h1>
      </header>

      <main className="taste-detail-content">
        <section className="taste-detail-one-line">
          <span className="taste-detail-user">최찬우님은...</span>
          <span className="taste-detail-highlight">까다로운 평론가</span>
        </section>

        <section className="taste-detail-history" aria-label="사용자 이력">
          <div className="taste-detail-history-item">
            <strong>5</strong>
            <span>평가</span>
          </div>
          <span className="taste-detail-divider">|</span>
          <div className="taste-detail-history-item">
            <strong>6</strong>
            <span>코멘트</span>
          </div>
          <span className="taste-detail-divider">|</span>
          <div className="taste-detail-history-item">
            <strong>5</strong>
            <span>컬렉션</span>
          </div>
        </section>

        <section className="taste-detail-section">
          <h2 className="taste-detail-section-title">별점분포</h2>
          <div className="taste-detail-chart-wrap" aria-hidden="true">
            <div className="taste-detail-chart">
              {RATING_BARS.map((height, idx) => (
                <div
                  key={`detail-bar-${idx}`}
                  className={`taste-detail-bar ${idx === 7 ? 'active' : ''}`}
                  style={{ height: `${height}px` }}
                />
              ))}
            </div>
            <div className="taste-detail-chart-scale">
              <span>0.5</span>
              <span>5.0</span>
            </div>
          </div>
        </section>

        <section className="taste-detail-section">
          <h2 className="taste-detail-section-title">책 선호 태그</h2>
          <div className="taste-detail-tag-cloud">
            {PREFER_TAGS.map((tag) => (
              <span key={tag.label} className={`taste-detail-tag ${tag.size}`}>
                {tag.label}
              </span>
            ))}
          </div>
        </section>

        <section className="taste-detail-section">
          <h2 className="taste-detail-section-title">책 선호장르</h2>
          <div className="taste-detail-genre-list">
            {PREFER_GENRES.map((item) => (
              <div key={item.genre} className="taste-detail-genre-item">
                <strong>{item.genre}</strong>
                <span>{item.count}</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default TasteAnalysisDetail
