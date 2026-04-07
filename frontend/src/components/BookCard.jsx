import { Link } from 'react-router-dom'
import { pickFallbackCoverById } from '../data/coverUrl'
import './BookCard.css'

function BookCard({ book, isPlaceholder, variant = 'default', to, showRating = true }) {
  if (isPlaceholder) {
    return (
      <div className="book-card placeholder">
        <div className="book-cover placeholder-cover">
          <span>책 이미지</span>
        </div>
      </div>
    )
  }

  const defaultTo =
    book?.id != null && String(book.id).length > 0 ? `/book/${String(book.id)}` : null
  const cardTo = to === undefined ? defaultTo : to
  const cardClassName = `book-card ${variant === 'grid' ? 'book-card-grid' : ''}`.trim()

  const content = (
    <>
      <div className="book-cover">
        <img
          src={book.image}
          alt={book.title}
          onError={(e) => {
            const el = e.currentTarget
            if (el.dataset.fallback === '1') return
            el.dataset.fallback = '1'
            el.src = pickFallbackCoverById(book.id)
          }}
        />
      </div>
      <h3 className="book-title">{book.title}</h3>
      {showRating && typeof book.rating === 'number' && (
        <p className="book-subtext">평점 {book.rating}</p>
      )}
    </>
  )

  if (!cardTo) {
    return (
      <div className={cardClassName}>
        {content}
      </div>
    )
  }

  return (
    <Link to={cardTo} className={cardClassName}>
      {content}
    </Link>
  )
}

export default BookCard
