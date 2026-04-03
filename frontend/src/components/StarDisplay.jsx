/**
 * 읽기 전용 별점 표시 컴포넌트 (전체/반/빈 별).
 * CSS: pc-star-display, pc-star, pc-star-full/half/empty (PopularComments.css)
 */
export default function StarDisplay({ rating }) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.25 && rating - full < 0.75
  const stars = [1, 2, 3, 4, 5].map((n) => {
    if (n <= full) return 'full'
    if (n === full + 1 && half) return 'half'
    return 'empty'
  })

  return (
    <span className="pc-star-display" aria-label={`${rating}점`}>
      {stars.map((type, i) => (
        <span key={i} className={`pc-star pc-star-${type}`}>★</span>
      ))}
    </span>
  )
}
