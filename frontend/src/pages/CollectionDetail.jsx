import { Navigate, useNavigate, useParams } from 'react-router-dom'
import BookCard from '../components/BookCard'
import PopularComments from '../components/PopularComments'
import { SECTIONS } from '../data/dummyBooks'
import './CollectionDetail.css'

function CollectionDetail() {
  const navigate = useNavigate()
  const { sectionId } = useParams()
  const section = SECTIONS.find((item) => item.id === sectionId)
  const likeCount = 600 + section.books.length * 17
  const comments = [
    { userName: 'C♥', text: '올려주시는 컬렉션 항상 잘 보고 있어요.', likeCount: 2, replyCount: 1, rating: 4, createdAt: '8년 전' },
    { userName: '가브리엘', text: '감사합니다!', likeCount: 2, replyCount: 0, rating: 3.5, createdAt: '8년 전' },
    { userName: '책벌레', text: '표지만큼 내용도 좋았어요. 다음 작품도 기대돼요.', likeCount: 12, replyCount: 0, rating: 4 },
  ]

  if (!section) return <Navigate to="/my" replace />

  return (
    <div className="collection-detail-page">
      <header className="collection-detail-header">
        <button
          type="button"
          className="collection-detail-back-btn"
          onClick={() => navigate(-1)}
          aria-label="뒤로가기"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="collection-detail-title">{section.title}</h1>
      </header>

      <main className="collection-detail-content">
        <section className="collection-detail-description">
          <h2 className="collection-detail-section-title">컬렉션 소개</h2>
          <p className="collection-detail-description-text">
            {section.title} 주제로 모은 책 리스트입니다. 관심 있는 책부터 골라서 상세 페이지에서 코멘트와
            별점을 확인해 보세요.
          </p>
        </section>

        <section className="collection-detail-actions">
          <button type="button" className="collection-detail-action-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z" />
              <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
            </svg>
            <span>좋아요</span>
          </button>
          <button type="button" className="collection-detail-action-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span>댓글</span>
          </button>
          <button type="button" className="collection-detail-action-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="18" cy="5" r="3" />
              <circle cx="6" cy="12" r="3" />
              <circle cx="18" cy="19" r="3" />
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            <span>공유</span>
          </button>
        </section>

        <div className="collection-detail-meta-row">
          <p className="collection-detail-like-count">좋아요 {likeCount}개</p>
        </div>

        <section className="collection-detail-works">
          <h2 className="collection-detail-section-title">
            작품들 <span>{section.books.length}</span>
          </h2>
          <div className="collection-detail-grid">
            {section.books.map((book) => (
              <BookCard key={book.id} book={book} variant="grid" />
            ))}
          </div>
        </section>

        <section className="collection-detail-comments-wrap">
          <PopularComments
            title="댓글"
            showCount={false}
            showSummary={false}
            comments={comments}
            onCommentClick={() => {}}
          />
        </section>
      </main>
    </div>
  )
}

export default CollectionDetail
