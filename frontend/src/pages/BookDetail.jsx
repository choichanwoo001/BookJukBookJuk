import { useMemo, useState, useCallback } from 'react'
import { useNavigate, useParams, Navigate } from 'react-router-dom'
import { getBookById } from '../data/dummyBooks'
import { pickImageBySeed } from '../data/imagePool'
import StoreMap from '../components/StoreMap'
import './BookDetail.css'

const CHARACTER_IMG = pickImageBySeed(102)

/* ---------- 반별점 렌더링 ---------- */
function StarDisplay({ rating }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.25 && rating - full < 0.75
  const stars = [1, 2, 3, 4, 5].map((n) => {
    if (n <= full) return 'full'
    if (n === full + 1 && half) return 'half'
    return 'empty'
  })
  return (
    <span className="pc-star-display" aria-label={`${rating}점`}>
      {stars.map((type, i) => (
        <span key={i} className={`pc-star pc-star-${type}`}>★</span>
      ))}
    </span>
  )
}

/* ---------- 별점 분포 차트 ---------- */
function RatingChart({ comments }) {
  const counts = [5, 4, 3, 2, 1].map((star) =>
    comments.filter((c) => Math.round(c.rating) === star).length
  )
  const maxCount = Math.max(...counts, 1)
  const labels = ['1.0', '2.0', '3.0', '4.0', '5.0']
  const orderedCounts = [...counts].reverse() // 1→5 순으로 표시
  return (
    <div className="pc-chart">
      <div className="pc-chart-bars">
        {orderedCounts.map((count, i) => (
          <div key={i} className="pc-chart-bar-wrap">
            <div
              className="pc-chart-bar"
              style={{ height: `${Math.round((count / maxCount) * 100)}%` }}
            />
          </div>
        ))}
      </div>
      <div className="pc-chart-labels">
        {labels.map((l) => (
          <span key={l} className="pc-chart-label">{l}</span>
        ))}
      </div>
    </div>
  )
}

/* ---------- 인기 코멘트 섹션 ---------- */
function PopularComments({ comments, avgRating, onCommentClick }) {
  const [expandedIdx, setExpandedIdx] = useState(null)
  const total = comments.length
  const avg = typeof avgRating === 'number' ? avgRating.toFixed(1) : String(avgRating)

  const toggleExpand = useCallback((e, i) => {
    e.stopPropagation()
    setExpandedIdx((prev) => (prev === i ? null : i))
  }, [])

  return (
    <div className="pc-wrap">
      {/* 헤더 */}
      <h2 className="pc-title">코멘트 <span className="pc-count">{total}</span></h2>

      {/* 평균별점 + 차트 */}
      <div className="pc-summary">
        <div className="pc-avg-block">
          <span className="pc-avg-num">{avg}</span>
          <span className="pc-avg-sub">({total}명)</span>
        </div>
        <RatingChart comments={comments} />
      </div>

      <div className="pc-divider" />

      {/* 코멘트 목록 */}
      <ul className="pc-list">
        {comments.map((comment, i) => {
          const text = typeof comment === 'string' ? comment : comment.text
          const rating = typeof comment === 'string' ? 4 : comment.rating
          const likeCount = comment.likeCount ?? 0
          const replyCount = comment.replyCount ?? 0
          const userName = comment.userName ?? '독자'
          const hasBadge = comment.hasBadge ?? false
          const isExpanded = expandedIdx === i
          const isLong = text.length > 80

          return (
            <li
              key={i}
              className="pc-comment-item"
              role="button"
              tabIndex={0}
              onClick={() => onCommentClick(i)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onCommentClick(i)
                }
              }}
            >
              {/* 상단: 별점 + 유저 */}
              <div className="pc-comment-top">
                <StarDisplay rating={rating} />
                <div className="pc-user-row">
                  <span className="pc-username">{userName}</span>
                  <div className="pc-avatar">{userName.charAt(0)}</div>
                </div>
              </div>

              {/* 본문 */}
              <p className={`pc-comment-text ${isExpanded || !isLong ? 'expanded' : ''}`}>
                {text}
                {isLong && !isExpanded && (
                  <span className="pc-text-fade" />
                )}
              </p>
              {isLong && !isExpanded && (
                <button
                  type="button"
                  className="pc-more-text-btn"
                  onClick={(e) => toggleExpand(e, i)}
                >
                  더보기
                </button>
              )}

              {/* 하단: 좋아요 / 댓글 / 메뉴 */}
              <div className="pc-comment-footer">
                <button type="button" className="pc-footer-btn" onClick={(e) => e.stopPropagation()}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" />
                    <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                  </svg>
                  <span>{likeCount}</span>
                </button>
                <button type="button" className="pc-footer-btn" onClick={(e) => e.stopPropagation()}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  <span>{replyCount}</span>
                </button>
                <button type="button" className="pc-footer-menu" onClick={(e) => e.stopPropagation()} aria-label="더보기">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" />
                  </svg>
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function BookDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [userStars, setUserStars] = useState(0)
  const [showFullDesc, setShowFullDesc] = useState(false)
  const [activeTab, setActiveTab] = useState('story')

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
              <button
                type="button"
                className="book-detail-img-frame book-detail-character book-detail-character-btn"
                onClick={() => navigate(`/book/${book.id}/chat`)}
                aria-label="캐릭터와 상세 토크하기"
              >
                <img src={CHARACTER_IMG} alt="캐릭터" />
              </button>
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
            bookId={id}
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
