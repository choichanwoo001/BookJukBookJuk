import { getCatalogRows } from '../bootstrap/catalogInit.js'
import { hashString } from './hashString'
import { coverForListBook } from './coverUrl'

/** booksCatalog.json / Supabase 카탈로그와 맞춘 더미 섞음 (재실행 시 같은 시드면 동일). */
const SEED_SHUFFLE = 0xbeefcafe
const BOOKS_PER_SECTION = 4
const SECTION_COUNT = 4

let catalogMapCache = null

function catalogById() {
  if (!catalogMapCache) {
    catalogMapCache = new Map(getCatalogRows().map((row) => [row.id, row]))
  }
  return catalogMapCache
}

function mulberry32(seed) {
  let a = seed >>> 0
  return function mulberry32Inner() {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), a | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), a | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function shuffleSeeded(arr, seed) {
  const rand = mulberry32(seed)
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function ratingForId(id) {
  const h = hashString(String(id))
  return Math.round((4 + (h % 10) / 10) * 10) / 10
}

function toListBook(row) {
  return {
    ...row,
    rating: ratingForId(row.id),
    image: coverForListBook(row.id, row.cover_image_url),
  }
}

const shuffled = shuffleSeeded([...getCatalogRows()], SEED_SHUFFLE)
const pickCount = Math.min(SECTION_COUNT * BOOKS_PER_SECTION, shuffled.length)
const picked = shuffled.slice(0, pickCount)

const SECTION_META = [
  { id: 'wishlist', title: '찜한 목록/이어읽기', showInfo: true },
  { id: 'hot', title: 'HOT 랭킹', showInfo: false },
  { id: 'rating', title: '평균 별점이 높은 작품', showInfo: false },
  { id: 'recommend', title: '영진님의 취향 저격', showInfo: true },
]

export const SECTIONS = SECTION_META.map((meta, sectionIndex) => ({
  ...meta,
  books: picked
    .slice(sectionIndex * BOOKS_PER_SECTION, sectionIndex * BOOKS_PER_SECTION + BOOKS_PER_SECTION)
    .map(toListBook),
}))

const COMMENT_USERS = [
  { name: '신혜미', hasBadge: true },
  { name: '에이프릴', hasBadge: true },
  { name: '독서광', hasBadge: false },
  { name: '책벌레', hasBadge: true },
  { name: '독서가', hasBadge: false },
]

const COMMENT_SETS = [
  [
    {
      text: '처음부터 끝까지 몰입했어요. 결말이 인상적이에요.',
      rating: 3.5,
      likeCount: 61,
      replyCount: 5,
      createdAt: '6년 전',
      replies: [
        { userName: '에이프릴', hasBadge: true, text: '오 헴님 이거 읽었네요 나두 좋았는데:)', likeCount: 3, createdAt: '6년 전' },
      ],
    },
    {
      text: '친구한테도 추천했어요. 책국이에요!',
      rating: 4.5,
      likeCount: 23,
      replyCount: 2,
      createdAt: '1년 전',
      replies: [],
    },
    {
      text: '표지만큼 내용도 좋았어요. 다음 작품도 기대돼요.',
      rating: 4.0,
      likeCount: 12,
      replyCount: 0,
      createdAt: '2개월 전',
      replies: [],
    },
  ],
  [
    {
      text: '주말에 읽기 딱 좋은 책이에요.',
      rating: 4.0,
      likeCount: 34,
      replyCount: 1,
      createdAt: '3개월 전',
      replies: [],
    },
    {
      text: '작가 문체가 정말 편안하게 읽혀요.',
      rating: 4.5,
      likeCount: 45,
      replyCount: 3,
      createdAt: '5개월 전',
      replies: [
        { userName: '독서광', hasBadge: false, text: '저도 이 작가 다른 책 찾아봐야겠어요!', likeCount: 2, createdAt: '5개월 전' },
      ],
    },
    {
      text: '중간에 눈물 났어요. 감동적인 장면이 많아요.',
      rating: 5.0,
      likeCount: 78,
      replyCount: 8,
      createdAt: '1년 전',
      replies: [],
    },
  ],
  [
    {
      text: '과몰입 주의! 밤새 읽었어요.',
      rating: 4.5,
      likeCount: 92,
      replyCount: 12,
      createdAt: '8개월 전',
      replies: [],
    },
    {
      text: '리뷰 보고 샀는데 기대 이상이었어요.',
      rating: 4.0,
      likeCount: 18,
      replyCount: 0,
      createdAt: '4개월 전',
      replies: [],
    },
    {
      text: '이 장르 좋아하시면 강추합니다.',
      rating: 3.5,
      likeCount: 29,
      replyCount: 4,
      createdAt: '2년 전',
      replies: [
        { userName: '책벌레', hasBadge: true, text: '맞아요 정말 재밌었어요 ㅎㅎ', likeCount: 5, createdAt: '2년 전' },
      ],
    },
  ],
]

const AGE_RATINGS = ['전체', '9세 이상', '12세 이상', '15세 이상']
const CATEGORIES = ['소설', '에세이', '자기계발', '과학', 'SF']

const AUTHORS = ['크리스텔 프티콜랭', '김영하', '한강', '조남주', '헤르만 헤세', '무라카미 하루키']

const DESCRIPTIONS = [
  '우리 사회의 가난과 슬픔, 불안과 고통, 여성의 삶을 기꺼이 직시하고 노래해온 아티스트 이랑이 지금껏 공개된 적 없었던 자신의 역사를 써내려간다. 아니, 대를 이어 내려오는 한국 여성들의 역사이자 딸, 엄마로 살아가는 것의 고통과 슬픔을.\n\n2021년 12월, 언니가 죽었다. 언니가 오래 준비하던 크리스마스 댄스 공연을 앞둔 날이었다. 이랑은 \'시끄러운 공주 스타일\'이었던 언니를 위해 머리에 장난감 왕관을 쓰고 상주를 맡았다.',
  '어느 날 갑자기 모든 것이 바뀐다. 평범했던 일상이 낯선 공간으로 변하고, 익숙했던 얼굴들이 전혀 다른 존재가 된다. 이 소설은 그 변화의 순간을 포착하며 우리에게 묻는다—당신은 지금 어디에 있냐고.',
  '삶은 언제나 우리가 이해하기 전에 먼저 지나가버린다. 그 빠른 걸음을 따라잡기 위해 우리는 기억을 붙들고, 언어를 찾고, 누군가를 사랑한다. 이 책은 그 모든 행위의 근원을 탐구한다.',
]

const AUTHOR_BIOS = [
  '이랑은 싱어송라이터이자 작가이다. 2012년 첫 앨범을 발표한 이후 음악과 글을 넘나들며 활동해왔다. 앨범 《욘욘슨》으로 한국대중음악상 최우수 포크 노래상을 수상했으며, 에세이집 《팔리지 않는 책》을 출간했다.',
  '1968년 서울 출생. 연세대학교 신학과를 졸업했다. 소설집 《나는 나를 파괴할 권리가 있다》로 데뷔했으며, 장편소설 《빛의 제국》 《퀴즈쇼》 《검은 꽃》 등을 발표했다.',
  '1970년 광주 출생. 연세대학교 국어국문학과를 졸업했다. 2005년 서울신문 신춘문예로 등단했으며 소설집 《여수의 사랑》, 장편소설 《채식주의자》 《바람이 분다, 가라》 등을 발표했다.',
]

function parseYear(y) {
  if (!y) return null
  const m = String(y).match(/\d{4}/)
  return m ? parseInt(m[0], 10) : null
}

function categoryFromKdc(kdc) {
  if (!kdc || !String(kdc).trim()) return null
  const parts = String(kdc)
    .split('>')
    .map((s) => s.trim())
    .filter(Boolean)
  return parts[parts.length - 1] || parts[0]
}

/** 목록용 책 객체에 상세 화면용 필드를 합칩니다. */
export function enrichBookDetail(book) {
  const seed = hashString(String(book.id))
  const comments = COMMENT_SETS[seed % COMMENT_SETS.length].map((c, i) => ({
    id: i,
    ...c,
    userName: COMMENT_USERS[(seed + i) % COMMENT_USERS.length].name,
    hasBadge: COMMENT_USERS[(seed + i) % COMMENT_USERS.length].hasBadge,
  }))

  const desc = book.description?.trim()
  const description = desc || DESCRIPTIONS[seed % DESCRIPTIONS.length]

  const authors = book.authors?.trim() || AUTHORS[seed % AUTHORS.length]

  const authorBio = book.author_bio?.trim() || AUTHOR_BIOS[seed % AUTHOR_BIOS.length]

  const category = categoryFromKdc(book.kdc_class_nm) || CATEGORIES[seed % CATEGORIES.length]

  const py = parseYear(book.published_year)

  return {
    ...book,
    authors,
    description,
    authorBio,
    productionYear: py ?? 2010 + (seed % 14),
    pages: 200 + (seed * 37) % 350,
    ageRating: AGE_RATINGS[seed % AGE_RATINGS.length],
    category,
    popularComments: comments,
    storeLocation: {
      lat: 37.4285 + (seed % 5) * 0.008,
      lng: 127.0043 + (seed % 3) * 0.006,
    },
  }
}

/** 책 ID와 코멘트 인덱스로 코멘트 상세 정보를 가져옵니다. */
export function getCommentById(bookId, commentId) {
  const book = getBookById(bookId)
  if (!book || !book.popularComments) return null
  const idx = typeof commentId === 'string' ? Number(commentId) : commentId
  if (Number.isNaN(idx) || idx < 0 || idx >= book.popularComments.length) return null
  return { book, comment: book.popularComments[idx] }
}

export function getBookById(id) {
  const key = id == null ? '' : String(id)
  if (!key) return null
  const row = catalogById().get(key)
  if (!row) return null
  return enrichBookDetail(toListBook(row))
}

/** 검색용: 카탈로그 전체 — initCatalog 이후 Supabase 또는 로컬 JSON */
export const ALL_BOOKS = getCatalogRows().map((row) => enrichBookDetail(toListBook(row)))
