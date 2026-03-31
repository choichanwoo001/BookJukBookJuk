import { useParams } from 'react-router-dom'
import { SECTIONS } from '../data/dummyBooks'
import BookCard from '../components/BookCard'
import BackButton from '../components/BackButton'
import './SectionBooks.css'

function SectionBooks() {
  const { sectionId } = useParams()

  const section = SECTIONS.find((s) => s.id === sectionId)

  if (!section) {
    return (
      <div className="section-books-page">
        <header className="sb-header">
          <BackButton className="sb-back-btn" />
          <h1 className="sb-title">섹션을 찾을 수 없어요</h1>
        </header>
      </div>
    )
  }

  return (
    <div className="section-books-page">
      <header className="sb-header">
        <BackButton className="sb-back-btn" />
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
