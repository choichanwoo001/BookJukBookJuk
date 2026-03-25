import { APP_IMAGES } from './imagePool'

export const createBook = (id, title, rating, imageIndex) => ({
  id,
  title,
  rating,
  image: APP_IMAGES[imageIndex % APP_IMAGES.length],
})

export const SECTIONS = [
  {
    id: 'wishlist',
    title: '찜한 목록/이어읽기',
    showInfo: true,
    books: [
      createBook(1, 'Project Hail Mary', 4.7, 0),
      createBook(2, 'Hamlet', 4.5, 1),
      createBook(3, '클린 코드', 4.8, 2),
      createBook(4, '이펙티브 자바', 4.6, 3),
    ],
  },
  {
    id: 'hot',
    title: 'HOT 랭킹',
    showInfo: false,
    books: [
      createBook(5, '달러구트 꿈 백화점', 4.9, 4),
      createBook(6, '불편한 편의점', 4.7, 0),
      createBook(7, '작별하지 않는다', 4.6, 1),
      createBook(8, '오늘 밤, 세계에서', 4.8, 2),
    ],
  },
  {
    id: 'rating',
    title: '평균 별점이 높은 작품',
    showInfo: false,
    books: [
      createBook(9, '자존감 수업', 4.9, 3),
      createBook(10, '역행자', 4.8, 4),
      createBook(11, '부의 추월차선', 4.7, 0),
      createBook(12, '해리포터 시리즈', 4.9, 1),
    ],
  },
  {
    id: 'recommend',
    title: '영진님의 취향 저격',
    showInfo: true,
    books: [
      createBook(13, '스타트업 한국', 4.5, 2),
      createBook(14, '미래학 콘서트', 4.6, 3),
      createBook(15, '일의 기쁨과 슬픔', 4.7, 4),
      createBook(16, '모순', 4.8, 0),
    ],
  },
]

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

/** 목록용 책 객체에 상세 화면용 필드를 합칩니다. */
export function enrichBookDetail(book) {
  const seed = book.id
  const comments = COMMENT_SETS[seed % COMMENT_SETS.length].map((c, i) => ({
    id: i,
    ...c,
    userName: COMMENT_USERS[(seed + i) % COMMENT_USERS.length].name,
    hasBadge: COMMENT_USERS[(seed + i) % COMMENT_USERS.length].hasBadge,
  }))

  const AUTHORS = ['크리스텔 프티콜랭', '김영하', '한강', '조남주', '헤르만 헤세', '무라카미 하루키']
  return {
    ...book,
    authors: AUTHORS[seed % AUTHORS.length],
    productionYear: 2010 + (seed % 14),
    pages: 200 + (seed * 37) % 350,
    ageRating: AGE_RATINGS[seed % AGE_RATINGS.length],
    category: CATEGORIES[seed % CATEGORIES.length],
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
  const numId = typeof id === 'string' ? Number(id) : id
  if (Number.isNaN(numId)) return null

  for (const section of SECTIONS) {
    const found = section.books.find((b) => b.id === numId)
    if (found) return enrichBookDetail(found)
  }
  return null
}
