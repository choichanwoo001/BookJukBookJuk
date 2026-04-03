import { Outlet, useLocation } from 'react-router-dom'
import BottomNav from './BottomNav'
import './Layout.css'

function Layout() {
  const { pathname } = useLocation()
  const hideBottomNav = /^\/book\/[^/]+\/chat$/.test(pathname) || pathname === '/my/chat'

  return (
    <div className="app-layout">
      <Outlet />
      {!hideBottomNav && <BottomNav />}
    </div>
  )
}

export default Layout
