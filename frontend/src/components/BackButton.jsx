import { useNavigate } from 'react-router-dom'

/**
 * 뒤로가기 버튼. to prop이 있으면 해당 경로로, 없으면 navigate(-1).
 * 기존 CSS 클래스를 유지하기 위해 className prop을 받습니다.
 */
export default function BackButton({ to, className = 'back-btn', label = '뒤로가기' }) {
  const navigate = useNavigate()
  return (
    <button
      type="button"
      className={className}
      onClick={() => (to ? navigate(to) : navigate(-1))}
      aria-label={label}
    >
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M19 12H5M12 19l-7-7 7-7" />
      </svg>
    </button>
  )
}
