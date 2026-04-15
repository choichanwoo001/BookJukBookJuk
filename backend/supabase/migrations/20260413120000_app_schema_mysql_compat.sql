-- BookJukBookJuk: 앱 테이블 추가 (MySQL 다이어그램 → PostgreSQL / Supabase)
--
-- 선행: `20260411120000_init_books.sql` 로 `public.books`(카탈로그, PK = `id` text)가 있어야 합니다.
-- 이 파일은 `books` 를 건드리지 않고, 나머지 엔티티만 생성합니다.
--
-- 도서 참조 컬럼은 값이 `public.books(id)` 와 같도록 두었습니다 (FK 제약은 없음).
-- 원본 DDL의 BIGINT book_id/review_id는 리뷰/도서 PK가 문자열이므로 text 로 두었습니다.

create extension if not exists pgcrypto;

-- ENUM (PostgreSQL)
do $$ begin
  create type public.shelf_type_enum as enum ('평가한', '읽은', '읽는중', '쇼핑리스트');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type public.book_user_state_enum as enum ('LIST', 'READING', 'RATED_ONLY', 'REVIEW_POSTED');
exception when duplicate_object then null;
end $$;

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
create table public.users (
  "Key" varchar(255) not null,
  username varchar(50) not null,
  password varchar(255) not null,
  nickname varchar(50) not null,
  profile_image_url varchar(500),
  bio text,
  preferred_genres varchar(500),
  created_at timestamptz not null default now(),
  constraint pk_users primary key ("Key")
);

comment on table public.users is '사용자';
comment on column public.users."Key" is '사용자 ID';
comment on column public.users.username is '아이디';
comment on column public.users.password is '비밀번호';
comment on column public.users.nickname is '닉네임';
comment on column public.users.profile_image_url is '프로필 이미지 URL';
comment on column public.users.bio is '자기소개';
comment on column public.users.preferred_genres is '선호 장르/태그';
comment on column public.users.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- authors
-- ---------------------------------------------------------------------------
create table public.authors (
  "Key" varchar(255) not null,
  name varchar(100) not null,
  created_at timestamptz not null default now(),
  constraint pk_authors primary key ("Key")
);

comment on column public.authors."Key" is '작가 ID';
comment on column public.authors.name is '이름';
comment on column public.authors.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- book_authors (복합 PK; 도서 쪽 = public.books.id)
-- ---------------------------------------------------------------------------
create table public.book_authors (
  "Key2" varchar(255) not null,
  "Key" text not null,
  role varchar(50) not null default '저자',
  constraint pk_book_authors primary key ("Key2", "Key")
);

comment on column public.book_authors."Key2" is '작가 ID';
comment on column public.book_authors."Key" is '도서 ID (books.id)';
comment on column public.book_authors.role is '역할 (저자, 역자, 감수 등)';

-- ---------------------------------------------------------------------------
-- reviews
-- ---------------------------------------------------------------------------
create table public.reviews (
  "Key" varchar(255) not null,
  user_id bigint not null,
  book_id text not null,
  content text not null,
  created_at timestamptz not null default now(),
  constraint pk_reviews primary key ("Key")
);

comment on column public.reviews."Key" is '리뷰 ID';
comment on column public.reviews.user_id is '사용자 ID';
comment on column public.reviews.book_id is '도서 ID (books.id)';
comment on column public.reviews.content is '리뷰 내용';
comment on column public.reviews.created_at is '작성 일시';

-- ---------------------------------------------------------------------------
-- comments
-- ---------------------------------------------------------------------------
create table public.comments (
  "Key" varchar(255) not null,
  review_id varchar(255) not null,
  user_id bigint not null,
  content text not null,
  created_at timestamptz not null default now(),
  constraint pk_comments primary key ("Key")
);

comment on column public.comments."Key" is '코멘트 ID';
comment on column public.comments.review_id is '리뷰 ID';
comment on column public.comments.user_id is '작성한 유저 ID';
comment on column public.comments.content is '댓글 내용';
comment on column public.comments.created_at is '작성 일시';

-- ---------------------------------------------------------------------------
-- conversation (대화방) — 다이어그램: conversation
-- ---------------------------------------------------------------------------
create table public.conversation (
  conversation_id varchar(255) not null,
  user_id varchar(255) not null,
  book_id text,
  created_at timestamptz not null default now(),
  type varchar(20) not null,
  constraint pk_conversation primary key (conversation_id),
  constraint conversation_type_check check (type in ('agent', 'book_detail')),
  constraint fk_conversation_user foreign key (user_id) references public.users ("Key") on delete cascade,
  constraint fk_conversation_book foreign key (book_id) references public.books (id) on delete set null
);

comment on table public.conversation is '대화방';
comment on column public.conversation.conversation_id is '대화방 ID';
comment on column public.conversation.user_id is '사용자 ID (users.Key)';
comment on column public.conversation.book_id is '도서 ID — book_detail 일 때 (books.id)';
comment on column public.conversation.created_at is '생성 일시';
comment on column public.conversation.type is 'agent | book_detail';

-- ---------------------------------------------------------------------------
-- conversation_messages (메시지) — 다이어그램: conversationMessage
-- ---------------------------------------------------------------------------
create table public.conversation_messages (
  message_id varchar(255) not null,
  conversation_id varchar(255) not null,
  role varchar(10) not null,
  content text not null,
  intent varchar(255),
  created_at timestamptz not null default now(),
  constraint pk_conversation_messages primary key (message_id),
  constraint conversation_messages_role_check check (role in ('user', 'ai')),
  constraint fk_conversation_messages_room foreign key (conversation_id) references public.conversation (conversation_id) on delete cascade
);

comment on table public.conversation_messages is '대화 메시지';
comment on column public.conversation_messages.message_id is '메시지 ID';
comment on column public.conversation_messages.conversation_id is '대화방 ID';
comment on column public.conversation_messages.role is 'user | ai';
comment on column public.conversation_messages.content is '내용';
comment on column public.conversation_messages.intent is 'agent 사용일 때만';
comment on column public.conversation_messages.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- review_likes
-- ---------------------------------------------------------------------------
create table public.review_likes (
  "Key" varchar(255) not null,
  "Key2" varchar(255) not null,
  created_at timestamptz not null default now(),
  constraint pk_review_likes primary key ("Key", "Key2")
);

comment on column public.review_likes."Key" is '사용자 ID';
comment on column public.review_likes."Key2" is '리뷰 ID';
comment on column public.review_likes.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- ratings
-- ---------------------------------------------------------------------------
create table public.ratings (
  "Key" varchar(255) not null,
  "Key2" text not null,
  score numeric(2, 1) not null,
  registered_at timestamptz not null default now(),
  constraint pk_ratings primary key ("Key", "Key2")
);

comment on column public.ratings."Key" is '사용자 ID';
comment on column public.ratings."Key2" is '도서 ID (books.id)';
comment on column public.ratings.score is '별점';
comment on column public.ratings.registered_at is '등록 일시';

-- ---------------------------------------------------------------------------
-- book_api_cache (원본에 PK 없음 → isbn을 PK로 두고 NOT NULL)
-- ---------------------------------------------------------------------------
create table public.book_api_cache (
  isbn varchar(20) not null,
  description text,
  author_bio text,
  editorial_review text,
  keywords jsonb,
  subject_names jsonb,
  wiki_book_summary text,
  wiki_author_summary text,
  wiki_extra_sections jsonb,
  cached_at timestamptz not null default now(),
  expires_at timestamptz not null,
  constraint pk_book_api_cache primary key (isbn)
);

comment on column public.book_api_cache.isbn is 'ISBN';
comment on column public.book_api_cache.description is '소개글';
comment on column public.book_api_cache.author_bio is '저자 소개';
comment on column public.book_api_cache.editorial_review is '편집자 리뷰';
comment on column public.book_api_cache.keywords is '키워드 목록 (단어 + 가중치)';
comment on column public.book_api_cache.subject_names is '주제 분류명 목록';
comment on column public.book_api_cache.wiki_book_summary is '위키 책 요약';
comment on column public.book_api_cache.wiki_author_summary is '위키 저자 요약';
comment on column public.book_api_cache.wiki_extra_sections is '위키 추가 섹션 (등장인물, 시대배경 등)';
comment on column public.book_api_cache.cached_at is '캐시 생성 일시';
comment on column public.book_api_cache.expires_at is '캐시 만료 일시';

-- ---------------------------------------------------------------------------
-- shelves
-- ---------------------------------------------------------------------------
create table public.shelves (
  "Key" varchar(255) not null,
  user_id bigint not null,
  shelf_type public.shelf_type_enum not null,
  created_at timestamptz not null default now(),
  constraint pk_shelves primary key ("Key")
);

comment on column public.shelves."Key" is '보관함 ID';
comment on column public.shelves.user_id is '생성한 유저 ID';
comment on column public.shelves.shelf_type is '보관함 타입';
comment on column public.shelves.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- shelf_books
-- ---------------------------------------------------------------------------
create table public.shelf_books (
  "Key" text not null,
  "Key2" varchar(255) not null,
  added_at timestamptz not null default now(),
  constraint pk_shelf_books primary key ("Key", "Key2")
);

comment on column public.shelf_books."Key" is '도서 ID (books.id)';
comment on column public.shelf_books."Key2" is '보관함 ID';
comment on column public.shelf_books.added_at is '추가 일시';

-- ---------------------------------------------------------------------------
-- book_vectors (원본에 PK 없음 → 대체 키)
-- ---------------------------------------------------------------------------
create table public.book_vectors (
  id uuid not null default gen_random_uuid(),
  isbn varchar(20),
  title varchar(300) not null,
  authors varchar(500),
  vector jsonb not null,
  kdc_class varchar(50),
  is_cold_start boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint pk_book_vectors primary key (id)
);

create unique index if not exists book_vectors_isbn_unique on public.book_vectors (isbn) where isbn is not null;

comment on column public.book_vectors.isbn is 'ISBN';
comment on column public.book_vectors.title is '제목';
comment on column public.book_vectors.authors is '저자';
comment on column public.book_vectors.vector is '1536차원 임베딩 벡터';
comment on column public.book_vectors.kdc_class is 'KDC 십진분류';
comment on column public.book_vectors.is_cold_start is '콜드스타트 여부 (정보 부족으로 LLM 태그 추론)';
comment on column public.book_vectors.created_at is '생성 일시';
comment on column public.book_vectors.updated_at is '수정 일시';

-- ---------------------------------------------------------------------------
-- collections
-- ---------------------------------------------------------------------------
create table public.collections (
  "Key" varchar(255) not null,
  user_id bigint not null,
  title varchar(200) not null,
  description text,
  is_public boolean not null default true,
  created_at timestamptz not null default now(),
  constraint pk_collections primary key ("Key")
);

comment on column public.collections."Key" is '컬렉션 ID';
comment on column public.collections.user_id is '생성한 유저 ID';
comment on column public.collections.title is '컬렉션 제목';
comment on column public.collections.description is '컬렉션 설명';
comment on column public.collections.is_public is '공개 여부';
comment on column public.collections.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- collection_books
-- ---------------------------------------------------------------------------
create table public.collection_books (
  "Key" text not null,
  "Key2" varchar(255) not null,
  order_index integer not null default 0,
  added_at timestamptz not null default now(),
  constraint pk_collection_books primary key ("Key", "Key2")
);

comment on column public.collection_books."Key" is '도서 ID (books.id)';
comment on column public.collection_books."Key2" is '컬렉션 ID';
comment on column public.collection_books.order_index is '순서';
comment on column public.collection_books.added_at is '추가 일시';

-- ---------------------------------------------------------------------------
-- book_user_states
-- ---------------------------------------------------------------------------
create table public.book_user_states (
  "Key2" varchar(255) not null,
  "Key" text not null,
  shelf_state public.book_user_state_enum not null,
  reading_proof_url varchar(500),
  comment_prompted_at timestamptz,
  context_tags jsonb,
  updated_at timestamptz not null default now(),
  constraint pk_book_user_states primary key ("Key2", "Key")
);

comment on column public.book_user_states."Key2" is '사용자 ID';
comment on column public.book_user_states."Key" is '도서 ID (books.id)';
comment on column public.book_user_states.shelf_state is '서재 상태';
comment on column public.book_user_states.reading_proof_url is '읽는 중 인증 이미지 URL';
comment on column public.book_user_states.comment_prompted_at is '마지막 댓글 작성 유도 일시';
comment on column public.book_user_states.context_tags is '맥락 태그 (STORE_DISCOVERED 등)';
comment on column public.book_user_states.updated_at is '수정 일시';

-- ---------------------------------------------------------------------------
-- stores
-- ---------------------------------------------------------------------------
create table public.stores (
  "Key" varchar(255) not null,
  name varchar(200) not null,
  address varchar(500),
  latitude numeric(10, 7),
  longitude numeric(10, 7),
  phone varchar(20),
  business_hours varchar(200),
  created_at timestamptz not null default now(),
  constraint pk_stores primary key ("Key")
);

comment on column public.stores."Key" is '서점 ID';
comment on column public.stores.name is '서점 이름';
comment on column public.stores.address is '주소';
comment on column public.stores.latitude is '위도';
comment on column public.stores.longitude is '경도';
comment on column public.stores.phone is '전화번호';
comment on column public.stores.business_hours is '영업 시간';
comment on column public.stores.created_at is '생성 일시';

-- ---------------------------------------------------------------------------
-- RLS: public.books 는 `init_books` 마이그레이션에서 이미 RLS+select 정책 적용됨.
--     여기서는 추가 테이블만 설정. 프로덕션 전 정책을 앱 요구에 맞게 확장하세요.
-- ---------------------------------------------------------------------------
alter table public.authors enable row level security;
create policy authors_select_public
  on public.authors
  for select
  to anon, authenticated
  using (true);

alter table public.book_authors enable row level security;
create policy book_authors_select_public
  on public.book_authors
  for select
  to anon, authenticated
  using (true);

alter table public.stores enable row level security;
create policy stores_select_public
  on public.stores
  for select
  to anon, authenticated
  using (true);

-- 그 외: RLS만 켜고 정책 없음 → PostgREST에서는 서비스 롤 등만 접근 (앱 정책 추가 전까지)
alter table public.users enable row level security;
alter table public.reviews enable row level security;
alter table public.comments enable row level security;
alter table public.conversation enable row level security;
alter table public.conversation_messages enable row level security;
alter table public.review_likes enable row level security;
alter table public.ratings enable row level security;
alter table public.book_api_cache enable row level security;
alter table public.shelves enable row level security;
alter table public.shelf_books enable row level security;
alter table public.book_vectors enable row level security;
alter table public.collections enable row level security;
alter table public.collection_books enable row level security;
alter table public.book_user_states enable row level security;
