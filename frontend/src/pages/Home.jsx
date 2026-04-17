import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BookSection from '../components/BookSection'
import { fetchHomeSections } from '../data/bookApi'
import './Home.css'

function Home() {
  const navigate = useNavigate()
  const [sectionsData, setSectionsData] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    fetchHomeSections(4)
      .then((data) => {
        if (cancelled) return
        setSectionsData(Array.isArray(data.items) ? data.items : [])
      })
      .catch(() => {
        if (cancelled) return
        setSectionsData([])
      })
      .finally(() => {
        if (cancelled) return
        setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const sections = useMemo(() => sectionsData, [sectionsData])

  return (
    <div className="home-page">
      <header className="home-header">
        <h1 className="header-logo">Verso</h1>
        <button
          className="search-btn"
          onClick={() => navigate('/search')}
          aria-label="검색"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </button>
      </header>

      <main className="home-content">
        {!isLoading && sections.length === 0 && (
          <p className="empty-message">표시할 책 데이터가 없습니다.</p>
        )}
        {sections.map((section) => (
          <BookSection key={section.id} section={section} />
        ))}
        <div className="content-spacer" />
      </main>
    </div>
  )
}

export default Home
