import { useNavigate, useParams, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { getCommentById } from '../data/dummyBooks'
import { pickImageBySeed } from '../data/imagePool'
import './CommentDetail.css'

const PROFILE_PLACEHOLDER = pickImageBySeed(103)

function CommentDetail() {
  const { id, commentId } = useParams()
  const navigate = useNavigate()
  const [replyInput, setReplyInput] = useState('')

  const data = getCommentById(id ?? '', commentId ?? '')

  if (!data) {
    return <Navigate to={`/book/${id}`} replace />
  }

  const { book, comment } = data

  const handleBack = () => navigate(-1)

  return (
    <div className="comment-detail-page">
      <header className="comment-detail-header">
        <button
          type="button"
          className="comment-detail-back"
          onClick={handleBack}
          aria-label="뒤로"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="comment-detail-header-title">코멘트</h1>
        <button
          type="button"
          className="comment-detail-menu"
          aria-label="메뉴"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="1.5" fill="currentColor" />
            <circle cx="12" cy="6" r="1.5" fill="currentColor" />
            <circle cx="12" cy="18" r="1.5" fill="currentColor" />
          </svg>
        </button>
      </header>

      <main className="comment-detail-main">
        <div className="comment-detail-card">
          <div className="comment-detail-review">
            <div className="comment-detail-review-top">
              <div className="comment-detail-review-left">
                <div className="comment-detail-user">
                  <img
                    src={PROFILE_PLACEHOLDER}
                    alt=""
                    className="comment-detail-avatar"
                  />
                  <div className="comment-detail-user-meta">
                    <span className="comment-detail-username">
                      {comment.userName}
                      {comment.hasBadge && (
                        <span className="comment-detail-badge" aria-hidden>●</span>
                      )}
                    </span>
                    <span className="comment-detail-time">{comment.createdAt}</span>
                  </div>
                </div>

                <div className="comment-detail-book-info">
                  <h2 className="comment-detail-book-title">{book.title}</h2>
                  <p className="comment-detail-book-meta">
                    책 · {book.productionYear} · {book.authors || '작가'}
                  </p>
                  <span className="comment-detail-rating-badge">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                    {comment.rating}
                  </span>
                </div>
              </div>

              <div className="comment-detail-book-cover">
                <img src={book.image} alt={book.title} />
              </div>
            </div>

            <p className="comment-detail-review-body">{comment.text}</p>

            <div className="comment-detail-actions">
              <button type="button" className="comment-detail-action-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                </svg>
                좋아요
              </button>
              <span className="comment-detail-action-divider" />
              <button type="button" className="comment-detail-action-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                댓글
              </button>
              <span className="comment-detail-action-divider" />
              <button type="button" className="comment-detail-action-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="18" cy="5" r="3" />
                  <circle cx="6" cy="12" r="3" />
                  <circle cx="18" cy="19" r="3" />
                  <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                  <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                </svg>
                공유
              </button>
            </div>

            <p className="comment-detail-likes">좋아요 {comment.likeCount}</p>
          </div>

          {comment.replies && comment.replies.length > 0 && (
            <div className="comment-detail-replies">
              {comment.replies.map((reply, i) => (
                <div key={i} className="comment-detail-reply">
                  <div className="comment-detail-reply-header">
                    <img
                      src={PROFILE_PLACEHOLDER}
                      alt=""
                      className="comment-detail-reply-avatar"
                    />
                    <span className="comment-detail-reply-username">
                      {reply.userName}
                      {reply.hasBadge && (
                        <span className="comment-detail-badge" aria-hidden>●</span>
                      )}
                    </span>
                    <span className="comment-detail-reply-time">{reply.createdAt}</span>
                  </div>
                  <p className="comment-detail-reply-text">{reply.text}</p>
                  <div className="comment-detail-reply-actions">
                    <button type="button" className="comment-detail-reply-like">
                      좋아요
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
                      </svg>
                      {reply.likeCount}
                    </button>
                    <button type="button" className="comment-detail-reply-menu" aria-label="메뉴">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="1.5" fill="currentColor" />
                        <circle cx="12" cy="6" r="1.5" fill="currentColor" />
                        <circle cx="12" cy="18" r="1.5" fill="currentColor" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="comment-detail-input-row">
            <img
              src={PROFILE_PLACEHOLDER}
              alt=""
              className="comment-detail-input-avatar"
            />
            <input
              type="text"
              className="comment-detail-input"
              placeholder="댓글을 남겨보세요."
              value={replyInput}
              onChange={(e) => setReplyInput(e.target.value)}
            />
            <span className="comment-detail-input-divider" />
            <button type="button" className="comment-detail-submit-btn">
              댓글
            </button>
          </div>
        </div>

        <div className="comment-detail-bottom-spacer" />
      </main>
    </div>
  )
}

export default CommentDetail
