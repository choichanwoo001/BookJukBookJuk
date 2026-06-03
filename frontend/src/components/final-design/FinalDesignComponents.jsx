import { Link, NavLink, useNavigate } from 'react-router-dom';

import bell from '../../assets/figma/bell.svg';
import bookOpen from '../../assets/figma/book-open.svg';
import bookmark from '../../assets/figma/bookmark.svg';
import calendar from '../../assets/figma/calendar.svg';
import check from '../../assets/figma/check.svg';
import chevronLeft from '../../assets/figma/chevron-left.svg';
import chevronRight from '../../assets/figma/chevron-right.svg';
import clock from '../../assets/figma/clock.svg';
import home from '../../assets/figma/home.svg';
import layers from '../../assets/figma/layers.svg';
import library from '../../assets/figma/library.svg';
import lock from '../../assets/figma/lock.svg';
import mapPin from '../../assets/figma/map-pin.svg';
import pencil from '../../assets/figma/pencil.svg';
import play from '../../assets/figma/play.svg';
import plus from '../../assets/figma/plus.svg';
import quote from '../../assets/figma/quote.svg';
import search from '../../assets/figma/search.svg';
import send from '../../assets/figma/send.svg';
import sparkles from '../../assets/figma/sparkles.svg';
import star from '../../assets/figma/star.svg';
import users from '../../assets/figma/users.svg';
import xIcon from '../../assets/figma/x.svg';

export const icons = {
  bell,
  bookOpen,
  bookmark,
  calendar,
  check,
  chevronLeft,
  chevronRight,
  clock,
  home,
  layers,
  library,
  lock,
  mapPin,
  pencil,
  play,
  plus,
  quote,
  search,
  send,
  sparkles,
  star,
  users,
  x: xIcon,
};

export function Icon({ name, size = 16, alt = '' }) {
  return <img className="fd-icon" src={icons[name]} alt={alt} style={{ '--icon-size': `${size / 16}rem` }} />;
}

export function MobileShell({ children, showTabBar = true, activeTab = 'home', className = '' }) {
  return (
    <div className={`fd-page-shell ${className}`}>
      {children}
      {showTabBar ? <BottomTabBar activeTab={activeTab} /> : null}
    </div>
  );
}

export function Header({ title, subtitle, backTo, right, profile = false, searchTo }) {
  const navigate = useNavigate();
  return (
    <header className="fd-header">
      <div className="fd-header-left">
        {backTo ? (
          <button className="fd-icon-button" type="button" onClick={() => navigate(backTo)} aria-label="뒤로">
            <Icon name="chevronLeft" />
          </button>
        ) : null}
        <div>
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      <div className="fd-header-actions">
        {searchTo ? (
          <Link className="fd-icon-button" to={searchTo} aria-label="검색">
            <Icon name="search" />
          </Link>
        ) : null}
        {right}
        {profile ? (
          <>
            <button className="fd-icon-button" type="button" aria-label="알림">
              <Icon name="bell" />
            </button>
            <Link className="fd-avatar" to="/books/reading-1/completion">지</Link>
          </>
        ) : null}
      </div>
    </header>
  );
}

export function BottomTabBar({ activeTab }) {
  const tabs = [
    { id: 'home', label: '홈', to: '/', icon: 'home' },
    { id: 'library', label: '책장', to: '/library', icon: 'library' },
    { id: 'community', label: '커뮤니티', to: '/community', icon: 'users' },
    { id: 'record', label: '나의 기록', to: '/books/reading-1/completion', icon: 'bookmark' },
  ];
  return (
    <nav className="fd-bottom-tab" aria-label="주요 메뉴">
      {tabs.map((tab) => (
        <NavLink className={tab.id === activeTab ? 'is-active' : ''} to={tab.to} key={tab.id}>
          <Icon name={tab.icon} size={22} />
          <span>{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export function Chip({ children, icon, selected = false, onClick }) {
  return (
    <button className={`fd-chip ${selected ? 'is-selected' : ''}`} type="button" onClick={onClick}>
      {icon ? <Icon name={icon} size={13} /> : null}
      <span>{children}</span>
    </button>
  );
}

export function PrimaryButton({ children, icon = 'play', to, onClick, variant = 'primary' }) {
  const content = (
    <>
      {icon ? <Icon name={icon} size={18} /> : null}
      <span>{children}</span>
    </>
  );
  if (to) {
    return <Link className={`fd-primary-button fd-primary-button--${variant}`} to={to}>{content}</Link>;
  }
  return <button className={`fd-primary-button fd-primary-button--${variant}`} type="button" onClick={onClick}>{content}</button>;
}

export function SearchBar({ value, placeholder, onChange, onSubmit }) {
  return (
    <form className="fd-search-bar" onSubmit={onSubmit}>
      <Icon name="search" size={18} />
      <input value={value} placeholder={placeholder} onChange={(event) => onChange?.(event.target.value)} />
      {value ? (
        <button type="button" onClick={() => onChange?.('')} aria-label="검색어 지우기">
          <Icon name="x" size={14} />
        </button>
      ) : null}
    </form>
  );
}

export function BookCover({ icon, tone = 'brown', large = false }) {
  return <div className={`fd-book-cover fd-book-cover--${tone} ${large ? 'is-large' : ''}`}><span>{icon}</span></div>;
}

export function CurrentBookCard({ book, complete = false }) {
  const percent = complete ? 100 : Math.round((book.currentPage / book.pages) * 100);
  return (
    <section className={`fd-current-card ${complete ? 'is-complete' : ''}`}>
      <div className="fd-card-row">
        <Chip icon={complete ? 'check' : 'bookOpen'}>{complete ? '완독' : '읽는 중'}</Chip>
        <span className="fd-card-badge">{complete ? '5구간 완료' : 'NEW'}</span>
      </div>
      <div className="fd-book-main">
        <BookCover icon={book.icon} large />
        <div>
          <h2>{book.title}</h2>
          <strong>{book.author}</strong>
          <p>{book.pages}페이지</p>
          <div className="fd-progress-row">
            <span className="fd-progress-track"><span style={{ width: `${Math.max(percent, complete ? 100 : 1)}%` }} /></span>
            <b>{percent}%</b>
          </div>
        </div>
      </div>
      <div className="fd-card-foot">
        <span><Icon name="bookOpen" size={12} /> {complete ? book.pages : book.currentPage} / {book.pages} 페이지</span>
        <span>{complete ? '오늘 완독' : '오늘 시작'}</span>
      </div>
    </section>
  );
}

export function JourneyTimeline({ steps, complete = false, currentSegment = 1, onOpenStepDoubleClick }) {
  return (
    <section className="fd-section">
      <div className="fd-section-title">
        <h2><Icon name="mapPin" size={15} /> 나의 독서 여정</h2>
        <span className={`fd-section-state ${complete ? 'is-complete' : ''}`}>
          <Icon name={complete ? 'check' : 'layers'} size={12} />
          {complete ? `${steps.length} / ${steps.length} 구간 완료` : `${currentSegment} / ${steps.length} 구간`}
        </span>
      </div>
      <div className="fd-timeline-card">
        {steps.map((step, index) => (
          <article
            className={`fd-timeline-step is-${step.state}`}
            key={step.title}
            onDoubleClick={step.state === 'active' ? () => onOpenStepDoubleClick?.(index) : undefined}
            title={step.state === 'active' ? '더블클릭하면 이 구간을 읽음 처리합니다' : undefined}
          >
            <div className="fd-timeline-rail">
              <span>{step.state === 'done' ? <Icon name="check" size={12} /> : step.state === 'active' ? <Icon name="star" size={12} /> : <Icon name="lock" size={11} />}</span>
              {index < steps.length - 1 ? <i /> : null}
            </div>
            <div>
              <h3>{step.title}{step.state === 'active' ? <em>현재 위치</em> : null}</h3>
              <strong>{step.subtitle}</strong>
              <p>{step.pages}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function BookListItem({ book, action = '추가', onAction }) {
  return (
    <article className="fd-book-list-item">
      <BookCover icon={book.icon} tone={book.tone || 'pink'} />
      <div>
        <h3>{book.title}</h3>
        <strong>{book.author}</strong>
        <p>{book.meta || `${book.pages || 224}페이지`}</p>
        {book.summary ? <small>{book.summary}</small> : null}
      </div>
      <button type="button" onClick={onAction}>
        <Icon name={action === '읽기 시작' ? 'play' : 'plus'} size={12} />
        {action}
      </button>
    </article>
  );
}

export function PaigeAvatar() {
  return <span className="fd-paige-avatar">P</span>;
}

export function ChatBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <article className={`fd-chat-row ${isUser ? 'is-user' : 'is-ai'}`}>
      {!isUser ? <PaigeAvatar /> : null}
      <div>
        {!isUser ? <span className="fd-chat-name">Paige</span> : null}
        <p>{message.content}</p>
      </div>
    </article>
  );
}

export function CommunityPost({ post }) {
  return (
    <article className="fd-community-card">
      <div className="fd-reviewer-row">
        <span className="fd-avatar">{post.avatar}</span>
        <div>
          <h3>{post.user}<em>{post.role}</em></h3>
          <p>{post.date}</p>
        </div>
        <Chip icon="check" selected>팔로잉</Chip>
      </div>
      <div className="fd-community-book">
        <BookCover icon={post.book.icon} tone="purple" />
        <div>
          <h4>{post.book.title}</h4>
          <p>{post.book.author}</p>
          <span>★★★★<i>☆</i> {post.book.rating}</span>
        </div>
      </div>
      <blockquote>{post.review}</blockquote>
      <div className="fd-traces">
        {post.traces.map((trace) => <Chip icon="calendar" key={trace}>{trace}</Chip>)}
      </div>
      <div className="fd-quote-line"><Icon name="quote" size={13} /> {post.quote}</div>
      <div className="fd-card-actions">
        <button type="button"><Icon name="bookmark" size={14} /> 책장에 담기</button>
        <button type="button"><Icon name="search" size={14} /> 리뷰 전체보기</button>
      </div>
    </article>
  );
}
