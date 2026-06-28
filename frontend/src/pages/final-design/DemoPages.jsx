import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Html5Qrcode } from 'html5-qrcode';

import {
  BackButton,
  Header,
  Icon,
  MobileShell,
  PrimaryButton,
} from '../../components/final-design/FinalDesignComponents.jsx';
import { ReadingWidget } from '../../components/final-design/ReadingWidget.jsx';
import { DEMO_TIMING, demoReceiptQrPayload, nextDayWidgetMessage, widgetMessage } from '../../data/demoScript.js';
import {
  addShelfSyncBook,
  getDemoUser,
  setDemoUser,
  updateDemoSession,
} from '../../utils/demoStorage.js';

const SYNC_STEPS = ['영수증 확인 중…', '구매 정보 확인 중…', '책장에 추가 중…'];

function parseReceiptPayload(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function processReceipt(payload, navigate) {
  const user = getDemoUser();
  if (!user || user.memberId !== payload.memberId) {
    window.sessionStorage.setItem('bookjuk.pendingReceipt', JSON.stringify(payload));
    navigate('/signup');
    return;
  }
  runSyncFlow(payload, navigate);
}

function runSyncFlow(payload, navigate) {
  let step = 0;
  const overlay = document.createElement('div');
  overlay.className = 'fd-sync-overlay';
  overlay.innerHTML = `<div class="fd-sync-modal"><span class="fd-button-spinner"></span><p>${SYNC_STEPS[0]}</p></div>`;
  document.body.appendChild(overlay);

  const advance = () => {
    step += 1;
    if (step < SYNC_STEPS.length) {
      overlay.querySelector('p').textContent = SYNC_STEPS[step];
      setTimeout(advance, step === 1 ? DEMO_TIMING.syncReceiptMs : DEMO_TIMING.syncShelfMs);
      return;
    }
    payload.books?.forEach((book) => addShelfSyncBook(book.id));
    updateDemoSession({ lastPage: 0, chatTurns: 0, highlightCount: 0 });
    document.body.removeChild(overlay);
    const firstBook = payload.books?.[0];
    navigate(firstBook ? `/books/${firstBook.id}/home` : '/library');
  };

  setTimeout(advance, DEMO_TIMING.syncReceiptMs);
}

export function ScanPage() {
  const navigate = useNavigate();
  const scannerRef = useRef(null);
  const [error, setError] = useState('');
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    let scanner;
    const startScanner = async () => {
      try {
        scanner = new Html5Qrcode('qr-reader');
        scannerRef.current = scanner;
        await scanner.start(
          { facingMode: 'environment' },
          { fps: 10, qrbox: { width: 220, height: 220 } },
          (decoded) => {
            const payload = parseReceiptPayload(decoded);
            if (!payload?.memberId) {
              setError('인식할 수 없는 QR 코드예요.');
              return;
            }
            scanner.stop().catch(() => {});
            setScanning(false);
            processReceipt(payload, navigate);
          },
          () => {},
        );
        setScanning(true);
      } catch {
        setError('카메라를 사용할 수 없어요. 아래 데모 버튼을 이용해주세요.');
      }
    };
    startScanner();
    return () => {
      if (scannerRef.current?.isScanning) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, [navigate]);

  const demoScan = () => {
    const payload = parseReceiptPayload(demoReceiptQrPayload);
    processReceipt(payload, navigate);
  };

  return (
    <MobileShell showTabBar={false} className="fd-scan-page">
      <Header title="QR 영수증 스캔" backTo="/library" />
      <main className="fd-scan-scroll">
        <p className="fd-scan-guide">결제 후 받은 QR 영수증을 스캔하면 구매한 책이 책장에 등록돼요.</p>
        <div className="fd-qr-reader-wrap">
          <div id="qr-reader" />
          {!scanning ? <div className="fd-qr-placeholder"><Icon name="search" size={32} /></div> : null}
        </div>
        {error ? <p className="fd-scan-error">{error}</p> : null}
        <PrimaryButton icon="sparkles" onClick={demoScan}>데모 영수증 스캔</PrimaryButton>
        <p className="fd-scan-hint">카메라가 안 되면 위 버튼으로 데모를 진행할 수 있어요.</p>
      </main>
    </MobileShell>
  );
}

export function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = (event) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setTimeout(() => {
      const pending = window.sessionStorage.getItem('bookjuk.pendingReceipt');
      const payload = pending ? parseReceiptPayload(pending) : parseReceiptPayload(demoReceiptQrPayload);
      setDemoUser({
        memberId: payload?.memberId || 'jiheon',
        name: name.trim(),
        email: email.trim(),
      });
      window.sessionStorage.removeItem('bookjuk.pendingReceipt');
      if (payload) {
        runSyncFlow(payload, navigate);
      } else {
        navigate('/library');
      }
      setLoading(false);
    }, 900);
  };

  const loginExisting = () => {
    setDemoUser({ memberId: 'jiheon', name: '지현', email: 'jiheon@demo.com' });
    const pending = window.sessionStorage.getItem('bookjuk.pendingReceipt');
    const payload = pending ? parseReceiptPayload(pending) : parseReceiptPayload(demoReceiptQrPayload);
    window.sessionStorage.removeItem('bookjuk.pendingReceipt');
    if (payload) runSyncFlow(payload, navigate);
    else navigate('/library');
  };

  return (
    <MobileShell showTabBar={false} className="fd-signup-page">
      <header className="fd-highlight-header">
        <BackButton onClick={() => navigate('/scan')} />
        <h1>회원가입</h1>
        <span aria-hidden="true" />
      </header>
      <main className="fd-signup-scroll">
        <section className="fd-prompt-card">
          <h2><Icon name="sparkles" /> 영수증을 연동하려면 가입이 필요해요</h2>
          <p>서점에서 구매한 책을 책장에 자동 등록하려면 계정을 만들어주세요.</p>
        </section>
        <form className="fd-signup-form" onSubmit={submit}>
          <label>
            이름
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="지현" required />
          </label>
          <label>
            이메일
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@email.com" />
          </label>
          <PrimaryButton icon="check" loading={loading}>가입하고 연동하기</PrimaryButton>
        </form>
        <button className="fd-signup-login-link" type="button" onClick={loginExisting}>
          이미 계정이 있어요
        </button>
      </main>
    </MobileShell>
  );
}

const PHONE_DOCK_APPS = [
  {
    id: 'phone',
    label: '전화',
    bg: 'var(--color-phone-icon-bg)',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M8.2 4.8c.4-.9 1.3-1.4 2.3-1.2l1.8.4c.9.2 1.5 1 1.5 1.9 0 .8-.4 1.5-1 2l-1 .8c1.2 2.2 3 4 5.2 5.2l.8-1c.5-.6 1.2-1 2-.9.9 0 1.7.6 1.9 1.5l.4 1.8c.2 1-.3 1.9-1.2 2.3-1 .5-2.1.8-3.2.8-5.8 0-10.5-4.7-10.5-10.5 0-1.1.3-2.2.8-3.2z"
          fill="currentColor"
        />
      </svg>
    ),
  },
  {
    id: 'messages',
    label: '메시지',
    bg: 'var(--color-phone-icon-bg-alt)',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M6 5.5h12a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H9.4L6 19.8V7.5a2 2 0 0 1 2-2z"
          fill="currentColor"
        />
        <circle cx="9.5" cy="11.5" r="0.9" fill="#fff" />
        <circle cx="12" cy="11.5" r="0.9" fill="#fff" />
        <circle cx="14.5" cy="11.5" r="0.9" fill="#fff" />
      </svg>
    ),
  },
  {
    id: 'internet',
    label: '인터넷',
    bg: 'var(--color-phone-icon-bg)',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.8" />
        <ellipse cx="12" cy="12" rx="3.2" ry="8" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M4.5 12h15M6.5 8h11M6.5 16h11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: 'camera',
    label: '카메라',
    bg: 'var(--color-phone-icon-bg-alt)',
    icon: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M7 7.5h3.2l1-1.5h3.6l1 1.5H19a2 2 0 0 1 2 2v7.5a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V9.5a2 2 0 0 1 2-2z"
          fill="currentColor"
        />
        <circle cx="13" cy="13.5" r="3.2" fill="none" stroke="#ffffff" strokeWidth="1.6" />
      </svg>
    ),
  },
];

function PhoneStatusBar() {
  const now = new Date();
  const timeLabel = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;

  return (
    <header className="fd-phone-status-bar" aria-label="상태 표시줄">
      <span className="fd-phone-status-time">{timeLabel}</span>
      <div className="fd-phone-status-icons" aria-hidden="true">
        <svg className="fd-phone-status-icon fd-phone-status-wifi" viewBox="0 0 24 24">
          <path d="M4.5 9.5c4.5-4.5 10.5-4.5 15 0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <path d="M7.5 12.5c2.8-2.8 6.2-2.8 9 0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <path d="M10.5 15.5c1.1-1.1 2.9-1.1 4 0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          <circle cx="12.5" cy="18" r="1.2" fill="currentColor" />
        </svg>
        <svg className="fd-phone-status-icon fd-phone-status-signal" viewBox="0 0 24 24">
          <rect x="3" y="14" width="3" height="7" rx="1" fill="currentColor" />
          <rect x="8" y="11" width="3" height="10" rx="1" fill="currentColor" />
          <rect x="13" y="8" width="3" height="13" rx="1" fill="currentColor" />
          <rect x="18" y="5" width="3" height="16" rx="1" fill="currentColor" />
        </svg>
        <svg className="fd-phone-status-icon fd-phone-status-battery" viewBox="0 0 28 14">
          <rect x="1" y="2" width="22" height="10" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <rect x="24" y="5" width="2.5" height="4" rx="1" fill="currentColor" />
          <rect x="3.2" y="4" width="16" height="6" rx="1.2" fill="currentColor" />
        </svg>
      </div>
    </header>
  );
}

function PhoneWidgetDemoPage({ message, onWidgetClick }) {
  return (
    <div className="fd-phone-home-page">
      <div className="fd-phone-device" role="presentation">
        <div className="fd-phone-screen">
          <div className="fd-phone-wallpaper" aria-hidden="true" />
          <PhoneStatusBar />
          <main className="fd-phone-content">
            <ReadingWidget onClick={onWidgetClick} message={message} />
          </main>
          <footer className="fd-phone-bottom-chrome">
            <div className="fd-phone-page-indicator" aria-hidden="true">
              <span className="fd-phone-page-fold" />
              <span className="fd-phone-page-dot" />
              <span className="fd-phone-page-dot fd-phone-page-dot--active" />
              <span className="fd-phone-page-dot" />
              <span className="fd-phone-page-dot" />
            </div>
            <nav className="fd-phone-dock" aria-label="고정 앱">
              {PHONE_DOCK_APPS.map((app) => (
                <div className="fd-phone-dock-app" key={app.id} style={{ '--phone-icon-bg': app.bg }}>
                  <span className="fd-phone-dock-icon">{app.icon}</span>
                  <span className="visually-hidden">{app.label}</span>
                </div>
              ))}
            </nav>
            <div className="fd-phone-nav-bar" aria-hidden="true">
              <span className="fd-phone-nav-btn fd-phone-nav-btn--recent" />
              <span className="fd-phone-nav-btn fd-phone-nav-btn--home" />
              <span className="fd-phone-nav-btn fd-phone-nav-btn--back" />
            </div>
          </footer>
        </div>
      </div>
      <Link className="fd-phone-back-to-app" to="/">앱으로 돌아가기</Link>
    </div>
  );
}

export function PhoneHomePage() {
  const navigate = useNavigate();

  const openLibraryFromWidget = () => {
    addShelfSyncBook(widgetMessage.bookId);
    navigate('/library');
  };

  return <PhoneWidgetDemoPage message={widgetMessage} onWidgetClick={openLibraryFromWidget} />;
}

export function NextDayPage() {
  const navigate = useNavigate();

  const openReadingFromWidget = () => {
    navigate(`/books/${nextDayWidgetMessage.bookId}/home`);
  };

  return <PhoneWidgetDemoPage message={nextDayWidgetMessage} onWidgetClick={openReadingFromWidget} />;
}
