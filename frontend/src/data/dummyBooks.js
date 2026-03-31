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

  return {
    ...book,
    authors: AUTHORS[seed % AUTHORS.length],
    description: DESCRIPTIONS[seed % DESCRIPTIONS.length],
    authorBio: AUTHOR_BIOS[seed % AUTHOR_BIOS.length],
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
