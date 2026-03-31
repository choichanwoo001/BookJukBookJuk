import { useNavigate } from 'react-router-dom'
import BookSection from '../components/BookSection'
import { SECTIONS } from '../data/dummyBooks'
import './Home.css'

function Home() {
  const navigate = useNavigate()

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
        {SECTIONS.map((section) => (
          <BookSection key={section.id} section={section} />
        ))}
        <div className="content-spacer" />
      </main>
    </div>
  )
}

export default Home
