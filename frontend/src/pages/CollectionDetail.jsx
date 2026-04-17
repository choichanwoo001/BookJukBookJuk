import { useEffect, useState } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import BookCard from '../components/BookCard'
import PopularComments from '../components/PopularComments'
import BackButton from '../components/BackButton'
import { fetchCollectionDetail } from '../data/bookApi'
import './CollectionDetail.css'

function CollectionDetail() {
  const { sectionId } = useParams()
  const [collection, setCollection] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    if (!sectionId) return undefined
    setIsLoading(true)
    fetchCollectionDetail(sectionId)
      .then((data) => {
        if (cancelled) return
        setCollection(data.item || null)
      })
      .catch(() => {
        if (cancelled) return
        setCollection(null)
      })
      .finally(() => {
        if (cancelled) return
        setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [sectionId])

  if (!isLoading && !collection) return <Navigate to="/my" replace />
  if (!collection) return null

  return (
    <div className="collection-detail-page">
      <header className="collection-detail-header">
        <BackButton className="collection-detail-back-btn" />
        <h1 className="collection-detail-title">{collection.title}</h1>
      </header>

      <main className="collection-detail-content">
        <section className="collection-detail-description">
          <h2 className="collection-detail-section-title">컬렉션 소개</h2>
          <p className="collection-detail-description-text">
            {collection.description || `${collection.title} 주제로 모은 책 리스트입니다.`}
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
          <p className="collection-detail-like-count">좋아요 {collection.likeCount || 0}개</p>
        </div>

        <section className="collection-detail-works">
          <h2 className="collection-detail-section-title">
            작품들 <span>{collection.books?.length || 0}</span>
          </h2>
          <div className="collection-detail-grid">
            {(collection.books || []).map((book) => (
              <BookCard key={book.id} book={book} variant="grid" />
            ))}
          </div>
        </section>

        <section className="collection-detail-comments-wrap">
          <PopularComments
            title="댓글"
            showCount={false}
            showSummary={false}
            comments={collection.comments || []}
            onCommentClick={() => {}}
          />
        </section>
      </main>
    </div>
  )
}

export default CollectionDetail
