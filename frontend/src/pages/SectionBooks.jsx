import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import BookCard from '../components/BookCard'
import BackButton from '../components/BackButton'
import { fetchSectionBooks } from '../data/bookApi'
import './SectionBooks.css'

function SectionBooks() {
  const { sectionId } = useParams()
  const [section, setSection] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    if (!sectionId) return undefined
    setIsLoading(true)
    fetchSectionBooks(sectionId, 40)
      .then((data) => {
        if (cancelled) return
        setSection(data)
      })
      .catch(() => {
        if (cancelled) return
        setSection(null)
      })
      .finally(() => {
        if (cancelled) return
        setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [sectionId])

  if (!section) {
    return (
      <div className="section-books-page">
        <header className="sb-header">
          <BackButton className="sb-back-btn" />
          <h1 className="sb-title">{isLoading ? '불러오는 중...' : '섹션을 찾을 수 없어요'}</h1>
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
