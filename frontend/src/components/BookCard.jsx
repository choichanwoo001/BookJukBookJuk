import { Link } from 'react-router-dom'
import './BookCard.css'

function BookCard({ book, isPlaceholder }) {
  if (isPlaceholder) {
    return (
      <div className="book-card placeholder">
        <div className="book-cover placeholder-cover">
          <span>책 이미지</span>
        </div>
      </div>
    )
  }

  return (
    <Link to={`/book/${book.id}`} className="book-card">
      <div className="book-cover">
        <img src={book.image} alt={book.title} />
      </div>
      <h3 className="book-title">{book.title}</h3>
      <p className="book-subtext">평점 {book.rating}</p>
    </Link>
  )
}

export default BookCard
