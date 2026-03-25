import BookCard from './BookCard'
import './BookSection.css'

function BookSection({ section }) {
  return (
    <section className="book-section">
      <div className="section-header">
        <h2 className="section-title">
          {section.title}
          {section.showInfo && (
            <span className="info-icon" title="자세히 보기">(i)</span>
          )}
        </h2>
        <button className="more-btn" aria-label="더 보기">
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
