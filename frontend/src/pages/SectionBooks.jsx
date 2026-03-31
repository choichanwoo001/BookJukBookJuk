import { useNavigate, useParams } from 'react-router-dom'
import { SECTIONS } from '../data/dummyBooks'
import BookCard from '../components/BookCard'
import './SectionBooks.css'

function SectionBooks() {
  const { sectionId } = useParams()
  const navigate = useNavigate()

  const section = SECTIONS.find((s) => s.id === sectionId)

  if (!section) {
    return (
      <div className="section-books-page">
        <header className="sb-header">
          <button className="sb-back-btn" onClick={() => navigate(-1)} aria-label="뒤로가기">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="sb-title">섹션을 찾을 수 없어요</h1>
        </header>
      </div>
    )
  }

  return (
    <div className="section-books-page">
      <header className="sb-header">
        <button className="sb-back-btn" onClick={() => navigate(-1)} aria-label="뒤로가기">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="sb-title">{section.title}</h1>
      </header>

      <main className="sb-content">
        <div className="sb-grid">
          {section.books.map((book) => (
            <BookCard key={book.id} book={book} variant="grid" />
          ))}
        </div>
      </main>
    </div>
  )
}

export default SectionBooks
