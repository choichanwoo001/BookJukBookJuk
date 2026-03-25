import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Home from './pages/Home'
import Library from './pages/Library'
import My from './pages/My'
import Search from './pages/Search'
import BookDetail from './pages/BookDetail'
import CommentDetail from './pages/CommentDetail'
import BookChat from './pages/BookChat'
import MyChat from './pages/MyChat'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/book/:id" element={<BookDetail />} />
          <Route path="/book/:id/comment/:commentId" element={<CommentDetail />} />
          <Route path="/book/:id/chat" element={<BookChat />} />
          <Route path="/library" element={<Library />} />
          <Route path="/my" element={<My />} />
          <Route path="/my/chat" element={<MyChat />} />
        </Route>
        <Route path="/search" element={<Search />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
