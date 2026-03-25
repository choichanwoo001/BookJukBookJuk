import { useNavigate } from 'react-router-dom'
import './Login.css'

function Login() {
  const navigate = useNavigate()

  const handleBack = () => {
    navigate(-1)
  }

  const handleSocialLogin = () => {
    navigate('/')
  }

  return (
    <div className="login-page">
      {/* Header */}
      <header className="login-header">
        <button className="back-btn" onClick={handleBack} aria-label="뒤로 가기">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      </header>

      {/* Logo & Headline */}
      <section className="login-hero">
        <div className="logo">
          <svg width="56" height="48" viewBox="0 0 56 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 6L6 42" stroke="currentColor" strokeWidth="8" strokeLinecap="round"/>
            <path d="M50 6L42 42" stroke="currentColor" strokeWidth="8" strokeLinecap="round"/>
          </svg>
        </div>
        <h1 className="headline">책과 더 가까워지는 순간</h1>
        <p className="sub-headline">
          서점 위치 안내와 개인화 추천을 하나의 경험으로
        </p>
      </section>

      {/* Social Login Buttons */}
      <section className="login-buttons">
        <button className="social-btn naver-btn" onClick={handleSocialLogin}>
          <span className="social-icon naver-icon">N</span>
          <span className="social-text">네이버로 시작하기</span>
        </button>
        <button className="social-btn google-btn" onClick={handleSocialLogin}>
          <span className="social-icon google-icon">
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </span>
          <span className="social-text">구글로 시작하기</span>
        </button>
        <button className="social-btn kakao-btn" onClick={handleSocialLogin}>
          <span className="social-icon kakao-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 3c-5.52 0-10 3.59-10 8 0 2.87 1.89 5.39 4.72 6.82-.2.72-.73 2.58-.83 2.99-.13.53.2.52.38.38.14-.1 2.22-1.51 3.12-2.12.5.07 1.01.11 1.61.11 5.52 0 10-3.59 10-8s-4.48-8-10-8z"/>
            </svg>
          </span>
          <span className="social-text">카카오로 시작하기</span>
        </button>
      </section>

      {/* Bottom Links */}
      <footer className="login-footer">
        <a href="/" className="footer-link">이메일로 로그인</a>
        <span className="footer-divider">|</span>
        <a href="/" className="footer-link">이메일로 가입하기</a>
      </footer>
    </div>
  )
}

export default Login
