import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
  BookCover,
  BookListItem,
  ChatBubble,
  Chip,
  CommunityPost,
  CurrentBookCard,
  Header,
  Icon,
  JourneyTimeline,
  MobileShell,
  PaigeAvatar,
  PrimaryButton,
  SearchBar,
} from '../../components/final-design/FinalDesignComponents.jsx';
import {
  chatMessages,
  communityPosts,
  communitySearches,
  completedJourneySteps,
  currentBook,
  journeySteps,
  libraryBooks,
  recommendedBooks,
  searchResults,
} from '../../data/mockFinalDesign.js';

const DEFAULT_BOOK_ID = 'reading-1';
const PROGRESS_STORAGE_KEY = 'bookjuk.sectionProgress';

const bookCatalog = libraryBooks.map((book, index) => ({
  ...currentBook,
  ...book,
  id: book.id || `reading-${index + 1}`,
  currentPage: book.progress ?? currentBook.currentPage,
}));

function findBook(bookId) {
  return bookCatalog.find((book) => book.id === bookId) || bookCatalog[0] || { ...currentBook, id: DEFAULT_BOOK_ID };
}

function clampReadCount(value) {
  return Math.min(Math.max(Number(value) || 0, 0), journeySteps.length);
}

function readProgressMap() {
  try {
    return JSON.parse(window.localStorage.getItem(PROGRESS_STORAGE_KEY) || '{}');
  } catch {
    return {};
  }
}

function getStoredReadCount(bookId) {
  return clampReadCount(readProgressMap()[bookId]);
}

function storeReadCount(bookId, readCount) {
  const progress = readProgressMap();
  progress[bookId] = clampReadCount(readCount);
  window.localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(progress));
}

function buildJourneySteps(readCount) {
  const clampedReadCount = clampReadCount(readCount);
  return journeySteps.map((step, index) => ({
    ...step,
    state: index < clampedReadCount ? 'done' : index === clampedReadCount ? 'active' : 'locked',
  }));
}

function getCurrentPage(book, readCount) {
  if (readCount >= journeySteps.length) return book.pages;
  return Math.round((book.pages / journeySteps.length) * readCount);
}

function getPageCountLabel(range) {
  const [start, end] = range.match(/\d+/g)?.map(Number) || [];
  if (!start || !end) return '';
  return `${end - start + 1}페이지`;
}

function useSelectedBook() {
  const { bookId = DEFAULT_BOOK_ID } = useParams();
  const book = findBook(bookId);
  return { book, bookId: book.id };
}

function useBookProgress(bookId) {
  const [readCount, setReadCount] = useState(() => getStoredReadCount(bookId));

  useEffect(() => {
    setReadCount(getStoredReadCount(bookId));
  }, [bookId]);

  const markCurrentSegmentRead = () => {
    setReadCount((current) => {
      const next = clampReadCount(current + 1);
      storeReadCount(bookId, next);
      return next;
    });
  };

  const safeReadCount = clampReadCount(readCount);
  return {
    currentSegment: Math.min(safeReadCount + 1, journeySteps.length),
    journey: buildJourneySteps(safeReadCount),
    markCurrentSegmentRead,
    readCount: safeReadCount,
  };
}

function Greeting() {
  return <Header title="안녕하세요, 지현님!" subtitle="오늘도 함께 읽어요" profile />;
}

export function HomePage() {
  const { book, bookId } = useSelectedBook();
  const { currentSegment, journey, markCurrentSegmentRead, readCount } = useBookProgress(bookId);
  const isComplete = readCount >= journeySteps.length;
  const bookWithProgress = { ...book, currentPage: getCurrentPage(book, readCount) };

  if (isComplete) {
    return (
      <MobileShell activeTab="home">
        <Greeting />
        <main className="fd-scroll fd-home">
          <CurrentBookCard book={{ ...book, currentPage: book.pages }} complete />
          <JourneyTimeline steps={completedJourneySteps} complete />
          <section className="fd-prompt-card">
            <h2><Icon name="sparkles" /> 리뷰를 남겨볼까요?</h2>
            <p>Paige가 독서 기록을 정리해 리뷰에 담을 문장과 질문을 준비했어요.</p>
            <PrimaryButton to={`/books/${bookId}/review`} icon="pencil">AI 도움으로 리뷰 쓰기</PrimaryButton>
          </section>
        </main>
      </MobileShell>
    );
  }

  return (
    <MobileShell activeTab="home">
      <Greeting />
      <main className="fd-scroll fd-home">
        <CurrentBookCard book={bookWithProgress} />
        <JourneyTimeline steps={journey} currentSegment={currentSegment} onOpenStepDoubleClick={markCurrentSegmentRead} />
        <section className="fd-prompt-card">
          <h2><Icon name="sparkles" /> 지금 바로 시작해볼까요?</h2>
          <p>첫 페이지를 열면 독서 여정이 시작돼요. Paige가 함께 읽으며 요약과 질문을 준비해드릴게요.</p>
          <PrimaryButton to={`/books/${bookId}/chat`}>{currentSegment}구간 시작하기</PrimaryButton>
        </section>
      </main>
    </MobileShell>
  );
}

export function HomeCompletePage() {
  const { book, bookId } = useSelectedBook();
  return (
    <MobileShell activeTab="home">
      <Greeting />
      <main className="fd-scroll fd-home">
        <CurrentBookCard book={{ ...book, currentPage: book.pages }} complete />
        <JourneyTimeline steps={completedJourneySteps} complete />
        <section className="fd-prompt-card">
          <h2><Icon name="sparkles" /> 리뷰를 남겨볼까요?</h2>
          <p>Paige가 독서 기록을 정리해 리뷰에 담을 문장과 질문을 준비했어요.</p>
          <PrimaryButton to={`/books/${bookId}/review`} icon="pencil">AI 도움으로 리뷰 쓰기</PrimaryButton>
        </section>
      </main>
    </MobileShell>
  );
}

export function LibraryPage() {
  const [tab, setTab] = useState('읽는 중 3권');
  const tabs = ['읽는 중 3권', '완독 0권', '읽고 싶은 책 0권'];
  return (
    <MobileShell activeTab="library">
      <Header title="나의 책장" subtitle="총 3권 · 완독 0권" right={<Link className="fd-icon-button" to="/books/search" aria-label="책 추가"><Icon name="plus" /></Link>} />
      <main className="fd-scroll">
        <div className="fd-segment">
          {tabs.map((item) => (
            <button className={tab === item ? 'is-active' : ''} type="button" onClick={() => setTab(item)} key={item}>{item}</button>
          ))}
        </div>
        <div className="fd-section-title">
          <h2>{tab}</h2>
          <span>최근 순</span>
        </div>
        <div className="fd-library-list">
          {bookCatalog.map((book, index) => (
            <article className="fd-library-card" key={book.id}>
              <BookCover icon={book.icon} tone={index === 0 ? 'brown' : 'blue'} />
              <div>
                <h3>{book.title}<em>{book.state}</em></h3>
                <p>{book.author}</p>
                <span>{book.progress} / {book.pages} 페이지</span>
                <div className="fd-mini-progress"><i style={{ width: `${Math.max(Math.round((book.progress / book.pages) * 100), 2)}%` }} /></div>
                <small>{book.note}</small>
              </div>
              <PrimaryButton to={`/books/${book.id}/home`} icon="play">시작하기</PrimaryButton>
            </article>
          ))}
        </div>
      </main>
    </MobileShell>
  );
}

export function ChatPage() {
  const { book, bookId } = useSelectedBook();
  const { currentSegment, journey } = useBookProgress(bookId);
  const currentStep = journey[currentSegment - 1] || journey[0];
  const [messages, setMessages] = useState(chatMessages);
  const [draft, setDraft] = useState('');
  const addMessage = (event) => {
    event.preventDefault();
    if (!draft.trim()) return;
    setMessages([...messages, { role: 'user', content: draft.trim() }, { role: 'ai', content: '좋아요. 그 문장을 오늘의 기록에 남겨두고, 다음 질문을 이어갈게요.' }]);
    setDraft('');
  };
  return (
    <MobileShell showTabBar={false} className="fd-chat-page">
      <Header title="오늘의 독서" backTo={`/books/${bookId}/home`} right={<Link className="fd-soft-button" to={`/books/${bookId}/highlight`}>저장</Link>} />
      <section className="fd-range-card">
        <div>
          <span><Icon name="bookOpen" /> 오늘 읽은 범위</span>
          <h2>{currentStep.pages}</h2>
          <p>{book.title} · {currentSegment}구간</p>
        </div>
        <Icon name="pencil" />
      </section>
      <main className="fd-chat-scroll">
        {messages.map((message, index) => <ChatBubble message={message} key={`${message.role}-${index}`} />)}
      </main>
      <form className="fd-input-bar" onSubmit={addMessage}>
        <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Paige에게 말하기..." />
        <button type="submit" aria-label="전송"><Icon name="send" size={18} /></button>
      </form>
    </MobileShell>
  );
}

export function HighlightPage() {
  const { book, bookId } = useSelectedBook();
  const navigate = useNavigate();
  const { currentSegment } = useBookProgress(bookId);
  const saveHighlight = () => {
    navigate(`/books/${bookId}/summary`);
  };
  return (
    <MobileShell showTabBar={false}>
      <Header title="하이라이트 저장" backTo={`/books/${bookId}/chat`} />
      <main className="fd-scroll">
        <section className="fd-context-row">
          <Chip icon="bookOpen">{book.title} · {currentSegment}구간</Chip>
          <p>이 문장을 어떤 감정으로 기억할까요?</p>
        </section>
        <section className="fd-quote-card">
          <blockquote>어른이 된다는 말을 들을수록 나는 어느 지점으로부터 멀어지는 것 같았다.</blockquote>
          <cite>1장, 23p</cite>
        </section>
        <section className="fd-section">
          <h2 className="fd-mini-title"><Icon name="quote" /> 감정 태그</h2>
          <div className="fd-wrap">{['공감', '인상적', '다시 읽기', '질문'].map((tag, index) => <Chip selected={index < 2} key={tag}>{tag}</Chip>)}</div>
        </section>
        <section className="fd-section">
          <h2 className="fd-mini-title"><Icon name="pencil" /> 내 메모</h2>
          <textarea className="fd-memo-box" defaultValue={"취약해질 때 자주 생각나는 문장.\n'어른답게'가 뭔지 다시 생각하게 된다."} />
        </section>
        <PrimaryButton icon="bookmark" onClick={saveHighlight}>저장하기</PrimaryButton>
      </main>
    </MobileShell>
  );
}

export function SummaryPage() {
  const { book, bookId } = useSelectedBook();
  const navigate = useNavigate();
  const { currentSegment, journey, markCurrentSegmentRead } = useBookProgress(bookId);
  const currentStep = journey[currentSegment - 1] || journey[0];
  const completeToday = () => {
    markCurrentSegmentRead();
    navigate(`/books/${bookId}/home`);
  };
  return (
    <MobileShell showTabBar={false}>
      <Header title="오늘의 요약" backTo={`/books/${bookId}/highlight`} right={<button className="fd-soft-button" type="button" onClick={completeToday}>완료</button>} />
      <main className="fd-scroll">
        <section className="fd-summary-hero">
          <p>2026.06.03</p>
          <h2>{currentStep.pages} · {getPageCountLabel(currentStep.pages)}</h2>
          <span>{book.title} · {currentSegment}구간 · {currentStep.subtitle}</span>
        </section>
        <section className="fd-ai-card">
          <div><PaigeAvatar /><h2>Paige의 요약</h2><Chip selected>AI 요약</Chip></div>
          <p>오늘 읽은 구간에서는 어른이 된다는 감각을 관계와 거리감 속에서 바라보는 장면이 중요하게 드러나요.</p>
        </section>
        <section className="fd-quote-card">
          <h2>오늘의 하이라이트</h2>
          <blockquote>어른이 된다는 말을 들을수록 나는 어느 지점으로부터 멀어지는 것 같았다.</blockquote>
          <cite>1장, 23p</cite>
        </section>
        <section className="fd-section">
          <h2 className="fd-mini-title">오늘의 키워드</h2>
          <div className="fd-wrap">{['#자아', '#어른다움', '#관계', '#흔들림', '#자기이해'].map((tag) => <Chip selected key={tag}>{tag}</Chip>)}</div>
        </section>
        <PrimaryButton icon="check" onClick={completeToday}>오늘 기록 완료하기</PrimaryButton>
      </main>
    </MobileShell>
  );
}

export function SearchPage() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const submit = (event) => {
    event.preventDefault();
    navigate('/books/search/results');
  };
  return (
    <MobileShell activeTab="library">
      <Header title="책 추가" backTo="/library" right={<Link className="fd-cancel" to="/library">취소</Link>} />
      <main className="fd-scroll">
        <SearchBar value={query} onChange={setQuery} onSubmit={submit} placeholder="책 제목이나 작가를 검색해보세요" />
        <section className="fd-section">
          <div className="fd-section-title"><h2><Icon name="clock" /> 최근 검색</h2><span>전체 삭제</span></div>
          <div className="fd-wrap">{['채식주의자', '불편한 편의점', '아몬드', '한강'].map((item) => <Chip icon="search" key={item}>{item}</Chip>)}</div>
        </section>
        <section className="fd-section">
          <div className="fd-section-title"><h2><Icon name="sparkles" /> 추천 도서</h2><span>더 보기 <Icon name="chevronRight" size={12} /></span></div>
          {recommendedBooks.map((book) => <BookListItem book={book} key={book.title} />)}
        </section>
        <section className="fd-manual-card">
          <h2><Icon name="bookOpen" /> 직접 책 등록하기</h2>
          <input placeholder="책 제목" />
          <input placeholder="작가" />
          <div><input placeholder="출판사" /><input placeholder="총 페이지 수" /></div>
          <PrimaryButton icon="bookOpen">이 책 읽기 시작</PrimaryButton>
        </section>
      </main>
    </MobileShell>
  );
}

export function SearchResultsPage() {
  const [filter, setFilter] = useState('전체');
  const visible = useMemo(() => (filter === '전체' ? searchResults : searchResults.filter((book) => book.category === filter)), [filter]);
  return (
    <MobileShell activeTab="library">
      <Header title="검색 결과" backTo="/books/search" />
      <main className="fd-scroll">
        <SearchBar value="한강" placeholder="검색어" />
        <div className="fd-result-head"><h2>"한강"</h2><p>총 {searchResults.length}권의 책을 찾았어요</p><Chip selected>{searchResults.length}권</Chip></div>
        <div className="fd-wrap">{['전체', '소설', '에세이', '최신'].map((item) => <Chip selected={filter === item} onClick={() => setFilter(item)} key={item}>{item}</Chip>)}</div>
        {visible.map((book) => <BookListItem book={book} action={book.action} key={book.title} />)}
      </main>
    </MobileShell>
  );
}

export function CommunityPage() {
  const [tab, setTab] = useState('팔로잉');
  return (
    <MobileShell activeTab="community">
      <Header title="커뮤니티" subtitle="팔로우한 사람들의 독서 후기를 확인해보세요" searchTo="/community/search" right={<button className="fd-icon-button" type="button" aria-label="알림"><Icon name="bell" /></button>} />
      <main className="fd-scroll">
        <div className="fd-wrap">{['팔로잉', '추천', '평론가', '독자'].map((item) => <Chip selected={tab === item} onClick={() => setTab(item)} key={item}>{item}</Chip>)}</div>
        {communityPosts.map((post) => <CommunityPost post={post} key={post.user} />)}
        <section className="fd-prompt-card">
          <h2><Icon name="check" /> 왜 이 리뷰를 신뢰할 수 있나요?</h2>
          <p>별점만이 아니라 읽은 기간, 저장 횟수, 하이라이트 같은 독서 흔적을 함께 보여드려요.</p>
        </section>
      </main>
    </MobileShell>
  );
}

export function CommunitySearchPage() {
  const [query, setQuery] = useState('');
  return (
    <MobileShell activeTab="community">
      <Header title="검색" subtitle="커뮤니티에서 사람과 책을 찾아보세요" backTo="/community" />
      <main className="fd-scroll">
        <SearchBar value={query} onChange={setQuery} placeholder="평론가, 독자, 책 제목을 검색해보세요" />
        <section className="fd-section">
          <h2 className="fd-mini-title">추천 검색</h2>
          <div className="fd-wrap">{communitySearches.map((item) => <Chip icon="search" key={item}>{item}</Chip>)}</div>
        </section>
        <section className="fd-section">
          <div className="fd-section-title"><h2>최근 검색</h2><span>전체 삭제</span></div>
          <div className="fd-search-history">{['지은', '작별하지 않는다', '무라카미 류'].map((item) => <span key={item}><Icon name="clock" /> {item}</span>)}</div>
        </section>
      </main>
    </MobileShell>
  );
}

export function AiReviewPage() {
  const { bookId } = useSelectedBook();
  const navigate = useNavigate();
  const memories = [
    {
      date: '6/1',
      text: '"읽다 보니 어른이 된다는 게 나이를 먹는 일보다 사람들 사이에서 나를 어떻게 바라보는지가 더 중요하다고 느꼈어요."',
    },
    {
      date: '6/3',
      text: '"엄마와의 장면에서 내 이야기 같다는 말을 남겼어요."',
    },
    {
      date: '6/9',
      text: '"다 읽고 나서는 어른이 된다는 게 성장만이 아니라 무언가를 포기하는 일이기도 하다고 느꼈어요."',
    },
  ];
  const questions = [
    {
      label: 'Q1 · 대화 기반',
      text: "'어른아 어른답지'라고 했는데, 다 읽고 나서 그 생각이 달라진 게 있었나요?",
    },
    {
      label: 'Q2 · 대화 기반',
      text: '엄마 장면에서 본인 이야기 같다고 했잖아요. 그 감정을 리뷰에 한 문장으로 적는다면 어떻게 표현할 수 있을까요?',
    },
    {
      label: 'Q3 · 하이라이트 기반',
      quote: '"어른스럽다는 말을 들을수록 나는 점점 나로부터 멀어지는 것 같았다"',
      text: '이 문장이 왜 인상 깊었는지도 리뷰에 담아볼까요?',
      tone: 'purple',
    },
  ];

  return (
    <MobileShell showTabBar={false} className="fd-ai-review-page">
      <div className="fd-status-bar" aria-hidden="true">
        <span>9:41</span>
        <div>
          <i className="fd-signal-icon" />
          <i className="fd-wifi-icon" />
          <i className="fd-battery-icon" />
        </div>
      </div>
      <header className="fd-review-header">
        <button type="button" onClick={() => navigate(`/books/${bookId}/home-complete`)} aria-label="뒤로">
          <Icon name="chevronLeft" size={17} />
        </button>
        <h1>리뷰 작성</h1>
        <span>지</span>
      </header>
      <main className="fd-review-scroll">
        <section className="fd-review-book-head">
          <div className="fd-review-cover" aria-hidden="true"><span /></div>
          <div>
            <h2>어른이 된다는 것 <em>완독</em></h2>
            <p>김혜진 · 224페이지 · 1~5구간 완료</p>
          </div>
        </section>

        <section className="fd-review-panel fd-review-listened">
          <div className="fd-review-panel-head">
            <PaigeAvatar />
            <h2>Paige가 우리 독서 대화를 돌아봤어요</h2>
            <span>AI 회고</span>
          </div>
          <div className="fd-review-divider" />
          <div className="fd-memory-list">
            {memories.map((item) => (
              <article className="fd-review-memory" key={item.date}>
                <b>{item.date}</b>
                <p>{item.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="fd-review-question-section">
          <h2><Icon name="search" size={15} /> 리뷰 작성에 도움이 될 질문이에요</h2>
          {questions.map((item) => (
            <article className={`fd-review-question ${item.tone === 'purple' ? 'is-purple' : ''}`} key={item.label}>
              <span>{item.label}</span>
              {item.quote ? <blockquote>{item.quote}</blockquote> : null}
              <p>{item.text}</p>
            </article>
          ))}
        </section>

        <section className="fd-review-panel fd-review-draft">
          <div className="fd-review-panel-head">
            <PaigeAvatar />
            <h2>Paige의 리뷰 초안</h2>
            <span><Icon name="sparkles" size={12} /> AI 생성</span>
          </div>
          <div className="fd-review-divider" />
          <div className="fd-draft-box">
            <p>『어른이 된다는 것』은 성장이란 이름으로 어른다움을 강요받는 순간들을 조용하고 현실적으로 보여주는 책이다.</p>
            <p>읽는 내내 어른이 된다는 것이 더 단단해지는 일이 아니라, 오히려 나를 잃지 않기 위해 계속 흔들리고 질문하는 과정처럼 느껴졌다. 특히 관계 속에서 스스로를 바라보게 되는 장면들이 오랫동안 마음에 남았다.</p>
          </div>
          <p className="fd-draft-caption">이 초안은 이전 대화와 하이라이트를 바탕으로 생성되었어요</p>
        </section>

        <section className="fd-my-review-section">
          <div className="fd-my-review-head">
            <h2><Icon name="pencil" size={15} /> 내 리뷰</h2>
            <span>초안 기반으로 수정 중</span>
          </div>
          <div className="fd-review-tools" aria-label="리뷰 수정 제안">
            {['더 짧게', '더 감성적으로', '더 솔직하게', '다시 제안'].map((item, index) => (
              <button className={index === 3 ? 'is-purple' : ''} type="button" key={item}>{item}</button>
            ))}
          </div>
          <label className="fd-review-editor-wrap">
            <textarea
              className="fd-review-editor"
              defaultValue={'어른이 된다는 건 성장만을 의미하지 않는다.\n이 책은 관계 속에서 스스로를 바라보게 만드는 순간들을 담담하게 보여준다.\n\n읽는 동안 나는 어른다움이란 정답을 아는 상태가 아니라, 흔들리면서도 계속 살아가는 법을 배워가는 과정일 수 있다고 느꼈다.'}
            />
            <span>89자</span>
          </label>
        </section>
      </main>
      <footer className="fd-review-submit-bar">
        <PrimaryButton to={`/books/${bookId}/completion`} icon="send">리뷰 게시하기</PrimaryButton>
      </footer>
    </MobileShell>
  );
}

export function CompletionPage() {
  const { bookId } = useSelectedBook();
  const navigate = useNavigate();
  const journey = [
    { title: '1구간 읽음', subtitle: '낯선 어른의 시작', pages: '1p ~ 45p' },
    { title: '2구간 읽음', subtitle: '관계 속에서 흔들리는 나', pages: '46p ~ 90p' },
    { title: '3구간 읽음', subtitle: '책임과 선택의 무게', pages: '91p ~ 135p' },
    { title: '4구간 읽음', subtitle: '나만의 기준을 세우는 시간', pages: '136p ~ 180p' },
    { title: '5구간 읽음', subtitle: '어른이 된다는 것의 의미', pages: '181p ~ 224p' },
  ];

  return (
    <MobileShell activeTab="record" className="fd-complete-page">
      <div className="fd-status-bar" aria-hidden="true">
        <span>9:41</span>
        <div>
          <i className="fd-signal-icon" />
          <i className="fd-wifi-icon" />
          <i className="fd-battery-icon" />
        </div>
      </div>
      <header className="fd-review-header fd-complete-header">
        <button type="button" onClick={() => navigate(`/books/${bookId}/home-complete`)} aria-label="뒤로">
          <Icon name="chevronLeft" size={17} />
        </button>
        <h1>완독 완료</h1>
        <button className="fd-share-button" type="button" aria-label="공유"><span /></button>
      </header>

      <main className="fd-complete-scroll">
        <section className="fd-complete-hero">
          <div className="fd-sparkle-row" aria-hidden="true"><span>✨</span><span>☆</span><span>✨</span></div>
          <div className="fd-party-icon" aria-hidden="true">🎉</div>
          <h2>완독을 축하해요!</h2>
          <p>어른이 된다는 것을 끝까지 함께 읽었어요.</p>
        </section>

        <section className="fd-complete-book-card">
          <div className="fd-complete-chips">
            <span><i className="fd-mini-circle">⌄</i> 독서 완료</span>
            <span><Icon name="calendar" size={12} /> 2026.05.22 완독</span>
          </div>
          <div className="fd-complete-book-main">
            <div className="fd-flower-cover" aria-hidden="true">🌸</div>
            <div>
              <h2>어른이 된다는 것</h2>
              <strong>김혜진</strong>
              <p>224페이지</p>
              <span>★★★★<i>☆</i> <b>4.0</b></span>
            </div>
          </div>
        </section>

        <section className="fd-complete-panel fd-complete-journey-panel">
          <h2><Icon name="layers" size={15} /> 나의 독서 여정</h2>
          <div className="fd-complete-stats">
            <article><span><Icon name="calendar" size={18} /></span><strong>12일</strong><p>독서일수</p></article>
            <article><span><Icon name="bookOpen" size={18} /></span><strong>224p</strong><p>읽은 페이지</p></article>
            <article><span><Icon name="pencil" size={18} /></span><strong>8개</strong><p>남긴 기록</p></article>
          </div>
          <div className="fd-complete-section-head">
            <h3><Icon name="mapPin" size={15} /> 나의 독서 여정</h3>
            <span>⌁ 5 / 5 구간 완료</span>
          </div>
          <div className="fd-complete-timeline">
            {journey.map((step, index) => (
              <article className="fd-complete-step" key={step.title}>
                <div><span>✓</span>{index < journey.length - 1 ? <i /> : null}</div>
                <section>
                  <h4>{step.title}</h4>
                  <strong>{step.subtitle}</strong>
                  <p>{step.pages}</p>
                </section>
              </article>
            ))}
            <div className="fd-complete-timeline-line" />
          </div>
        </section>

        <section className="fd-complete-panel fd-complete-ai-card">
          <div className="fd-complete-card-head">
            <h2><span>✣</span> AI의 한마디</h2>
            <em>+ AI</em>
          </div>
          <p>이 책을 읽으며 당신은 인물의 선택과 사회적 시선에 대해 깊이 생각했어요. 기록 속 키워드는 '자아', '억압', '물', '저항'이 가장 많이 등장했어요.</p>
          <small>✣ 12일간의 독서 기록을 분석했어요</small>
        </section>

        <section className="fd-complete-panel fd-one-line-review">
          <div className="fd-complete-card-head">
            <h2>〃 나의 한 줄 평</h2>
            <em><Icon name="pencil" size={12} /> 수정</em>
          </div>
          <blockquote>이해받지 못한 선택이 한 사람의 삶을 어떻게 바꾸는지 보여주는 책.</blockquote>
        </section>

        <section className="fd-complete-panel fd-keyword-card">
          <div className="fd-complete-card-head">
            <h2><span className="fd-tag-mark">◇</span> 많이 남긴 키워드</h2>
            <em>6개</em>
          </div>
          <div>
            {['#자아', '#억압', '#물', '#저항', '#꿈', '#사회'].map((tag) => <span key={tag}>{tag}</span>)}
          </div>
        </section>

        <section className="fd-complete-panel fd-next-card">
          <h2>→ 다음으로</h2>
          <div>
            <Link to={`/books/${bookId}/home-complete`}>
              <span className="fd-next-icon is-green">|||</span>
              <strong>완독 기록 확인하기</strong>
              <p>완독 탭에서 기록 보기</p>
              <Icon name="chevronRight" size={14} />
            </Link>
            <Link to="/books/search">
              <span className="fd-next-icon">✣</span>
              <strong>비슷한 책 추천받기</strong>
              <p>AI가 고른 다음 책 보기</p>
              <Icon name="chevronRight" size={14} />
            </Link>
          </div>
        </section>

        <PrimaryButton to={`/books/${bookId}/home-complete`} icon="star">완독 기록 보기</PrimaryButton>
      </main>
    </MobileShell>
  );
}
