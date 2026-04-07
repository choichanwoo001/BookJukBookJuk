/** ISBN 등 문자열 id에 대한 결정적 32비트 해시 (목업 시드용). */
export function hashString(str) {
  let h = 0
  const s = String(str ?? '')
  for (let i = 0; i < s.length; i++) {
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0
  }
  return Math.abs(h)
}
