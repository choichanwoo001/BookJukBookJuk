import { NavLink } from 'react-router-dom'
import './BottomNav.css'

function BottomNav() {
  return (
    <nav className="bottom-nav">
      {/* 홈 */}
      <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12L12 4l9 8" />
          <path d="M5 10v9a1 1 0 0 0 1 1h4v-5h4v5h4a1 1 0 0 0 1-1v-9" />
        </svg>
        <span>홈</span>
      </NavLink>

      {/* 보관함 */}
      <NavLink to="/library" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19V6a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v13" />
          <path d="M4 19a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1" />
          <line x1="8" y1="11" x2="16" y2="11" />
          <line x1="8" y1="15" x2="13" y2="15" />
        </svg>
        <span>보관함</span>
      </NavLink>

      {/* 마이 */}
      <NavLink to="/my" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
        </svg>
        <span>마이</span>
      </NavLink>
    </nav>
  )
}

export default BottomNav
