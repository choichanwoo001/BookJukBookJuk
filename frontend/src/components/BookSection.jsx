import { useNavigate } from 'react-router-dom'
import BookCard from './BookCard'
import './BookSection.css'

function BookSection({ section }) {
  const navigate = useNavigate()

  return (
    <section className="book-section">
      <div className="section-header">
        <h2 className="section-title">
          {section.title}
        </h2>
        <button
          className="more-btn"
          aria-label="더 보기"
          onClick={() => navigate(`/section/${section.id}`)}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>
      </div>
      <div className="book-list">
        {section.books.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </section>
  )
}

export default BookSection
