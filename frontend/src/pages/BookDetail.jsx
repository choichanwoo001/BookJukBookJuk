import { useMemo, useState } from 'react'
import { useNavigate, useParams, Navigate, Link } from 'react-router-dom'
import { getBookById } from '../data/dummyBooks'
import StoreMap from '../components/StoreMap'
import PopularComments from '../components/PopularComments'
import { useTab } from '../hooks/useTab'
import { CHARACTER_IMG } from '../data/constants'
import './BookDetail.css'

function BookDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [userStars, setUserStars] = useState(0)
  const [showFullDesc, setShowFullDesc] = useState(false)
  const { activeTab, setActiveTab } = useTab('story')

  const book = useMemo(() => getBookById(id ?? ''), [id])

  if (!book) {
    return <Navigate to="/" replace />
  }

  const avgRating = typeof book.rating === 'number' ? book.rating.toFixed(1) : String(book.rating)

  const handleShare = async () => {
    const url = window.location.href
    try {
      if (navigator.share) {
        await navigator.share({ title: book.title, url })
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url)
        window.alert('링크가 복사되었어요.')
      }
    } catch {
      /* 사용자 취소 등 */
    }
  }

  return (
    <div className="book-detail-page">
      <header className="book-detail-header">
        <span className="book-detail-header-spacer" />
        <button
          type="button"
          className="book-detail-close"
          onClick={() => navigate(-1)}
          aria-label="닫기"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </header>

      <main className="book-detail-main">
        <div className="book-detail-hero">
          <div className="book-detail-images">
            <div className="book-detail-img-cell">
              <div className="book-detail-img-frame book-detail-book">
                <img src={book.image} alt={book.title} />
              </div>
            </div>
            <div className="book-detail-img-cell">
              <Link
                to={`/book/${book.id}/chat`}
                className="book-detail-img-frame book-detail-character book-detail-character-btn"
                aria-label="캐릭터와 상세 토크하기"
              >
                <img src={CHARACTER_IMG} alt="캐릭터" />
              </Link>
            </div>
          </div>

          <div className="book-detail-title-row">
            <h1 className="book-detail-title">{book.title}</h1>
            <button type="button" className="book-detail-share" onClick={handleShare} aria-label="공유">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>

          <div className="book-detail-rating-block">
            <p className="book-detail-avg">
              <span className="book-detail-avg-label">평균 별점</span>
              <span className="book-detail-star-filled" aria-hidden>★</span>
              <span className="book-detail-avg-value">{avgRating}</span>
            </p>
            <div className="book-detail-stars-input" role="group" aria-label="내 별점">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  className={`book-detail-star-btn ${n <= userStars ? 'on' : ''}`}
                  onClick={() => setUserStars(n === userStars ? 0 : n)}
                  aria-label={`${n}점`}
                >
                  ★
                </button>
              ))}
            </div>
          </div>

          <div className="book-detail-actions">
            <button type="button" className="book-detail-action">보관함 추가</button>
            <button type="button" className="book-detail-action">리뷰 추가</button>
            <button type="button" className="book-detail-action">읽기 리스트 등록</button>
          </div>
        </div>

        <section className="book-detail-section">
          <div className="book-detail-tabs">
            <button
              type="button"
              className={`book-detail-tab ${activeTab === 'story' ? 'active' : ''}`}
              onClick={() => setActiveTab('story')}
            >
              줄거리
            </button>
            <button
              type="button"
              className={`book-detail-tab ${activeTab === 'author' ? 'active' : ''}`}
              onClick={() => setActiveTab('author')}
            >
              저자 정보
            </button>
          </div>

          {activeTab === 'story' && (
            <div className="book-detail-tab-content">
              <div className={`book-detail-desc ${showFullDesc ? 'expanded' : ''}`}>
                <p className="book-detail-desc-text">{book.description}</p>
                {!showFullDesc && (
                  <button
                    type="button"
                    className="book-detail-more-btn"
                    onClick={() => setShowFullDesc(true)}
                  >
                    더보기
                  </button>
                )}
              </div>
              <div className="book-detail-info-grid">
                <div className="book-detail-info-item">
                  <span className="book-detail-info-label">제작년도</span>
                  <span className="book-detail-info-value">{book.productionYear}년</span>
                </div>
                <div className="book-detail-info-item">
                  <span className="book-detail-info-label">페이지</span>
                  <span className="book-detail-info-value">{book.pages}p</span>
                </div>
                <div className="book-detail-info-item">
                  <span className="book-detail-info-label">연령 등급</span>
                  <span className="book-detail-info-value">{book.ageRating}</span>
                </div>
                <div className="book-detail-info-item">
                  <span className="book-detail-info-label">카테고리</span>
                  <span className="book-detail-info-value">{book.category}</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'author' && (
            <div className="book-detail-tab-content">
              <div className="book-detail-author-row">
                <div className="book-detail-author-avatar">
                  {book.authors.charAt(0)}
                </div>
                <div className="book-detail-author-info">
                  <p className="book-detail-author-name">{book.authors}</p>
                  <p className="book-detail-author-label">저자</p>
                </div>
              </div>
              <p className="book-detail-author-bio">{book.authorBio}</p>
            </div>
          )}
        </section>

        <div className="book-detail-divider" />

        <section className="book-detail-section">
          <PopularComments
            comments={book.popularComments}
            avgRating={book.rating}
            onCommentClick={(i) => navigate(`/book/${id}/comment/${i}`)}
          />
        </section>

        <section className="book-detail-section book-detail-section-map">
          <h2 className="book-detail-section-title">구매 가능한 근처 매장</h2>
          <StoreMap key={book.id} center={book.storeLocation} />
        </section>

        <div className="book-detail-bottom-spacer" />
      </main>
    </div>
  )
}

export default BookDetail
