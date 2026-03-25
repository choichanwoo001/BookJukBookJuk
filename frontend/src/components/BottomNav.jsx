import { NavLink } from 'react-router-dom'
import { pickImageBySeed } from '../data/imagePool'
import './BottomNav.css'

function BottomNav() {
  return (
    <nav className="bottom-nav">
      <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        <span>홈</span>
      </NavLink>
      <NavLink to="/library" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
        <span>보관함</span>
      </NavLink>
      <NavLink to="/my" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <span className="nav-icon my-icon">
          <img src={pickImageBySeed(106)} alt="마이" />
          <span className="nav-badge" aria-hidden="true" />
        </span>
        <span>마이</span>
      </NavLink>
    </nav>
  )
}

export default BottomNav
