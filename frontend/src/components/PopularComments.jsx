import { useState, useCallback } from 'react'
import './PopularComments.css'

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

function RatingChart({ comments }) {
  const counts = [5, 4, 3, 2, 1].map((star) =>
    comments.filter((c) => Math.round(c.rating) === star).length
  )
  const maxCount = Math.max(...counts, 1)
  const labels = ['1.0', '2.0', '3.0', '4.0', '5.0']
  const orderedCounts = [...counts].reverse()

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
        {labels.map((label) => (
          <span key={label} className="pc-chart-label">{label}</span>
        ))}
      </div>
    </div>
  )
}

function PopularComments({
  comments,
  avgRating,
  onCommentClick = () => {},
  title = '코멘트',
  showCount = true,
  showSummary = true,
}) {
  const [expandedIdx, setExpandedIdx] = useState(null)
  const total = comments.length
  const avg = typeof avgRating === 'number' ? avgRating.toFixed(1) : String(avgRating ?? '0.0')

  const toggleExpand = useCallback((e, i) => {
    e.stopPropagation()
    setExpandedIdx((prev) => (prev === i ? null : i))
  }, [])

  return (
    <div className="pc-wrap">
      <h2 className="pc-title">
        {title}
        {showCount && <span className="pc-count"> {total}</span>}
      </h2>

      {showSummary && (
        <>
          <div className="pc-summary">
            <div className="pc-avg-block">
              <span className="pc-avg-num">{avg}</span>
              <span className="pc-avg-sub">({total}명)</span>
            </div>
            <RatingChart comments={comments} />
          </div>
          <div className="pc-divider" />
        </>
      )}

      <ul className="pc-list">
        {comments.map((comment, i) => {
          const text = typeof comment === 'string' ? comment : comment.text
          const rating = typeof comment === 'string' ? 4 : comment.rating
          const likeCount = comment.likeCount ?? 0
          const replyCount = comment.replyCount ?? 0
          const userName = comment.userName ?? '독자'
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
              <div className="pc-comment-top">
                <StarDisplay rating={rating} />
                <div className="pc-user-row">
                  <span className="pc-username">{userName}</span>
                  <div className="pc-avatar">{userName.charAt(0)}</div>
                </div>
              </div>

              <p className={`pc-comment-text ${isExpanded || !isLong ? 'expanded' : ''}`}>
                {text}
                {isLong && !isExpanded && <span className="pc-text-fade" />}
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

export default PopularComments
