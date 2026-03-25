export const APP_IMAGES = [
  '/images/user-cover-1.png',
  '/images/user-cover-2.png',
  '/images/user-cover-3.png',
  '/images/user-cover-4.png',
  '/images/user-cover-5.png',
]

export function pickImageBySeed(seed = 0) {
  const num = Number(seed)
  const safe = Number.isFinite(num) ? Math.abs(Math.trunc(num)) : 0
  return APP_IMAGES[safe % APP_IMAGES.length]
}
