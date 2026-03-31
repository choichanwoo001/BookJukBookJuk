# BookJukBookJuk (책국책국)

> "책과 더 가까워지는 순간" — 소셜 도서 발견, AI 추천, 독서 어시스턴트 Paige를 결합한 모바일 웹앱

---

## 문서 목차

- [Paige 에이전트 설계](#paige-에이전트-설계)
- [프론트엔드 구조](#프론트엔드-구조)
- [AI 백엔드 구조](#ai-백엔드-구조)

---

## Paige 에이전트 설계

핵심 설계 문서는 아래 flow 문서를 참고해 주세요.

- `Paige_agent_flow_docs.md`: `ai/paigee/docs/Paigee_agent_flow_docs.md`

---

## 프론트엔드 구조

`frontend/src/` 기준으로 작성된 문서입니다.

### 기술 스택

| 항목 | 내용 |
|------|------|
| 프레임워크 | React 18 + Vite |
| 라우팅 | React Router v6 |
| 상태 관리 | React hooks (useState) — Redux/Context 없음 |
| 지도 | React-Leaflet (OpenStreetMap) |
| 스타일링 | CSS Custom Properties 기반 디자인 시스템 |

---

### 라우팅 구조 (`App.jsx`)

```
BrowserRouter
├── /login                         → Login (레이아웃 없음)
├── Layout (BottomNav 포함)
│   ├── /                          → Home
│   ├── /book/:id                  → BookDetail
│   ├── /book/:id/comment/:commentId → CommentDetail
│   ├── /book/:id/chat             → BookChat
│   ├── /library                   → Library
│   ├── /my                        → My
│   ├── /my/chat                   → MyChat
│   ├── /my/taste-analysis         → TasteAnalysisDetail
│   ├── /section/:sectionId        → SectionBooks
│   └── /collection/:sectionId     → CollectionDetail
├── /search                        → Search (레이아웃 없음, 전체화면)
└── *                              → / 로 리다이렉트
```

> **주의:** 채팅 페이지(`/chat`)에서는 `Layout` 컴포넌트가 자동으로 BottomNav를 숨깁니다.

---

### 페이지 목록

| 파일 | 라우트 | 설명 |
|------|--------|------|
| `Home.jsx` | `/` | 홈 화면. BookSection 단위로 위시리스트·HOT 랭킹·별점 높은 작품·추천 도서를 가로 스크롤로 표시 |
| `Login.jsx` | `/login` | 네이버·구글·카카오 소셜 로그인 (현재 mock) |
| `Library.jsx` | `/library` | 내 책 컬렉션. 탭: 평가함 / 좋아요 / 읽는 중 / 구매 목록 |
| `My.jsx` | `/my` | 프로필·활동 통계·취향 분석 요약·내 컬렉션·Paige 진입 버튼 |
| `Search.jsx` | `/search` | 전체 화면 검색. 탭: 책 / 작가 / 컬렉션 / 유저 (책 탭만 구현) |
| `BookDetail.jsx` | `/book/:id` | 책 상세. 별점 입력, 컬렉션 추가, 코멘트, 지도, AI 캐릭터 버튼 |
| `BookChat.jsx` | `/book/:id/chat` | 책 전용 AI 채팅. mock 응답 생성기 포함 |
| `MyChat.jsx` | `/my/chat` | 전체 도우미 Paige 채팅. 추천·컬렉션·독서 진행 안내 |
| `CommentDetail.jsx` | `/book/:id/comment/:commentId` | 코멘트 상세. 좋아요·답글·공유 |
| `SectionBooks.jsx` | `/section/:sectionId` | 섹션 내 전체 책 그리드 |
| `CollectionDetail.jsx` | `/collection/:sectionId` | 컬렉션 상세. 책 목록·코멘트 |
| `TasteAnalysisDetail.jsx` | `/my/taste-analysis` | 취향 분석 상세. 별점 분포 차트·선호 태그·장르 |

---

### 컴포넌트 목록

| 파일 | 설명 |
|------|------|
| `Layout.jsx` | 앱 전체 레이아웃 래퍼. `<Outlet>` + BottomNav 조합 |
| `BottomNav.jsx` | 하단 탭 바 (홈·서재·마이) |
| `BackButton.jsx` | 뒤로가기 버튼. `to` prop 지정 시 해당 경로로 이동, 없으면 `navigate(-1)` |
| `BookSection.jsx` | 제목 + 가로 스크롤 BookCard 리스트. "더보기" 버튼으로 `/section/:id` 이동 |
| `BookCard.jsx` | 책 카드 단일 컴포넌트. `variant="default"` (세로) / `"grid"` (정방형) |
| `PopularComments.jsx` | 코멘트 목록 + 평점 분포 차트 (RatingChart 내장) |
| `StarDisplay.jsx` | 읽기 전용 별점 표시 (0.5 단위 반별 지원) |
| `StoreMap.jsx` | React-Leaflet 기반 서점 위치 지도 |

---

### 커스텀 훅

| 파일 | 설명 |
|------|------|
| `hooks/useChat.js` | 채팅 공통 로직. `messages`, `input`, `isLoading`, `handleSend`, `handleKeyDown`, `scrollRef` 반환. 응답 함수를 파라미터로 받아 BookChat·MyChat 양쪽에서 재사용 |
| `hooks/useTab.js` | 탭 상태 관리. `activeTab`, `setActiveTab` 반환 |

---

### 데이터 파일

현재 프론트엔드는 백엔드와 연결되지 않은 **mock 데이터**로 동작합니다.

| 파일 | 설명 |
|------|------|
| `data/dummyBooks.js` | 핵심 mock DB. `SECTIONS` 배열(4개 섹션), `enrichBookDetail()`, `getBookById()`, `getCommentById()` 포함 |
| `data/imagePool.js` | 책 커버 이미지 풀. `pickImageBySeed(id)` 로 ID 기반 일관된 이미지 선택 |
| `data/constants.js` | 앱 공통 상수. `CHARACTER_IMG` (캐릭터 이미지 경로) 등 |

**dummyBooks 데이터 구조:**
```js
{
  id, title, rating,          // 기본 정보
  image, authors, description, authorBio,
  productionYear, pages, ageRating, category,
  popularComments: [...],     // 코멘트 배열
  storeLocation: { lat, lng } // 서점 좌표
}
```

---

### 디자인 시스템 (`styles/tokens.css`)

모든 색상·타이포그래피는 CSS Custom Properties로 관리합니다. **컴포넌트에 값을 하드코딩하지 마세요.**

**팔레트:**

| 변수 | 값 | 용도 |
|------|----|------|
| `--palette-cyan-main` | `#92C7CF` | 브랜드 주색 |
| `--palette-cyan-soft` | `#AAD7D9` | 브랜드 보조색 |
| `--palette-cream` | `#FBF9F1` | 배경 기본 |
| `--palette-warm-gray` | `#E5E1DA` | 서피스·테두리 |

**시맨틱 색상 변수 (사용 권장):**
```css
var(--color-brand-primary)   /* 주 브랜드색 */
var(--color-bg-base)         /* 페이지 배경 */
var(--color-bg-surface)      /* 카드·패널 배경 */
var(--color-text-primary)    /* 본문 텍스트 */
var(--color-text-muted)      /* 보조 텍스트 */
var(--color-rating-star)     /* 별점 골드 */
```

**타이포그래피:**
```css
var(--font-size-xs)    /* 12px */
var(--font-size-sm)    /* 13px */
var(--font-size-md)    /* 14px */
var(--font-size-base)  /* 15px */
var(--font-size-lg)    /* 16px */
var(--font-size-xl)    /* 18px */
var(--font-size-2xl)   /* 20px */
var(--font-size-3xl)   /* 22px */
```

**유틸리티 클래스:**
```
.text-title / .text-body / .text-caption
.text-primary / .text-muted / .text-subtle
.bg-base / .bg-surface
.page-container   /* 최대 430px, 중앙 정렬 */
.page-header      /* sticky 헤더 */
.hide-scrollbar   /* 크로스브라우저 스크롤바 숨김 */
```

---

### 현재 상태 및 다음 작업

- **프론트 ↔ AI 백엔드 미연결:** 모든 데이터는 mock. 연결하려면 FastAPI 서버 레이어 필요
- `BookChat.jsx`, `MyChat.jsx`의 mock 응답 함수를 실제 API 호출로 교체해야 함
- `dummyBooks.js`를 실제 API 응답으로 대체해야 함
- Paige 에이전트 구현 예정 (`ai/paigee/` 참고)

---

## AI 백엔드 구조

자세한 내용은 `CLAUDE.md` 및 `ai/paigee/docs/Paigee_agent_flow_docs.md` 참고.

