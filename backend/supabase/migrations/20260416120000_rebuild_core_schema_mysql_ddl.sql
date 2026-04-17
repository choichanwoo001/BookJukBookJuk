-- BookJukBookJuk: 코어 스키마 재구성 (`public.books` 제외)
--
-- - 아래에서 `public.books` 는 드롭하지 않습니다. (도서 카탈로그는 별도로 관리)
-- - 나머지 앱·KG 테이블은 드롭 후 이 파일에서 재생성합니다.
-- - 문자열 컬럼은 text 로 통일합니다.
-- - 단일 PK 는 `{테이블명}_id` 형식(예: users_id, authors_id)입니다. `public.books` 만 예외로 PK 는 `id`(init_books).
-- - 복합 PK·FK 는 참조 대상 PK 이름과 맞춥니다(authors_id, books_id, users_id, …).
-- - book_api_cache 는 자연키 `isbn` PK 유지, kg_edges 는 (src_id, dst_id, edge_key) 복합 PK 유지.
--
-- 선행: `public.books` 가 이미 있어야 하며, 도서 FK 는 카탈로그 PK 인 `books(id)` 를 참조합니다.
--       (자식 테이블 컬럼명은 `books_id` 로 두되, 참조 대상 열은 `init_books` 의 `id` 입니다.)

-- ---------------------------------------------------------------------------
-- 1) 기존 객체 제거 — books 제외 (의존 순서: 자식 → 부모)
-- ---------------------------------------------------------------------------
drop function if exists public.clear_hybrid_kg() cascade;

drop table if exists public.kg_edges cascade;
drop table if exists public.kg_nodes cascade;

drop table if exists public.conversation_messages cascade;
drop table if exists public.conversation cascade;

drop table if exists public.comments cascade;
drop table if exists public.review_likes cascade;
drop table if exists public.reviews cascade;

drop table if exists public.shelf_books cascade;
drop table if exists public.shelves cascade;

drop table if exists public.collection_books cascade;
drop table if exists public.collections cascade;

drop table if exists public.book_user_states cascade;
drop table if exists public.ratings cascade;

drop table if exists public.book_authors cascade;

drop table if exists public.book_vectors cascade;
drop table if exists public.book_api_cache cascade;

drop table if exists public.authors cascade;
drop table if exists public.stores cascade;
drop table if exists public.users cascade;

-- public.books 는 여기서 드롭하지 않음

drop type if exists public.shelf_type_enum cascade;
drop type if exists public.book_user_state_enum cascade;

-- ---------------------------------------------------------------------------
-- 2) 확장
-- ---------------------------------------------------------------------------
create extension if not exists vector;
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- 3) ENUM (PostgreSQL)
-- ---------------------------------------------------------------------------
do $$ begin
  create type public.shelf_type_enum as enum ('평가한', '읽은', '읽는중', '쇼핑리스트');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type public.book_user_state_enum as enum ('LIST', 'READING', 'RATED_ONLY', 'REVIEW_POSTED');
exception when duplicate_object then null;
end $$;

-- ---------------------------------------------------------------------------
-- 4) 테이블 생성
-- ---------------------------------------------------------------------------

create table public.users (
  users_id text not null,
  username text not null,
  password text not null,
  nickname text not null,
  profile_image_url text,
  bio text,
  preferred_genres text,
  created_at timestamptz not null default now(),
  constraint pk_users primary key (users_id)
);

comment on table public.users is '사용자';
comment on column public.users.users_id is '사용자 ID';

-- public.books: 이 마이그레이션에서 생성/드롭하지 않음 (별도 init 또는 수동 스키마)

create table public.authors (
  authors_id text not null,
  name text not null,
  created_at timestamptz not null default now(),
  constraint pk_authors primary key (authors_id)
);

comment on column public.authors.authors_id is '작가 ID';

create table public.book_authors (
  authors_id text not null,
  books_id text not null,
  role text not null default '저자',
  constraint pk_book_authors primary key (authors_id, books_id),
  constraint fk_book_authors_author foreign key (authors_id) references public.authors (authors_id) on delete cascade,
  constraint fk_book_authors_book foreign key (books_id) references public.books (id) on delete cascade
);

comment on column public.book_authors.authors_id is '작가 ID';
comment on column public.book_authors.books_id is '도서 ID';

create table public.reviews (
  reviews_id text not null,
  users_id text not null,
  books_id text not null,
  content text not null,
  created_at timestamptz not null default now(),
  constraint pk_reviews primary key (reviews_id),
  constraint fk_reviews_user foreign key (users_id) references public.users (users_id) on delete cascade,
  constraint fk_reviews_book foreign key (books_id) references public.books (id) on delete cascade
);

comment on column public.reviews.reviews_id is '리뷰 ID';

create table public.comments (
  comments_id text not null,
  reviews_id text not null,
  users_id text not null,
  content text not null,
  created_at timestamptz not null default now(),
  constraint pk_comments primary key (comments_id),
  constraint fk_comments_review foreign key (reviews_id) references public.reviews (reviews_id) on delete cascade,
  constraint fk_comments_user foreign key (users_id) references public.users (users_id) on delete cascade
);

comment on column public.comments.comments_id is '코멘트 ID';

create table public.ratings (
  users_id text not null,
  books_id text not null,
  score numeric(2, 1) not null,
  registered_at timestamptz not null default now(),
  constraint pk_ratings primary key (users_id, books_id),
  constraint fk_ratings_user foreign key (users_id) references public.users (users_id) on delete cascade,
  constraint fk_ratings_book foreign key (books_id) references public.books (id) on delete cascade
);

create table public.conversation (
  conversation_id text not null,
  users_id text not null,
  books_id text,
  created_at timestamptz not null default now(),
  type text not null,
  constraint pk_conversation primary key (conversation_id),
  constraint conversation_type_check check (type in ('agent', 'book_detail')),
  constraint fk_conversation_user foreign key (users_id) references public.users (users_id) on delete cascade,
  constraint fk_conversation_book foreign key (books_id) references public.books (id) on delete set null
);

comment on table public.conversation is '대화방';
comment on column public.conversation.type is 'agent | book_detail';

create table public.conversation_messages (
  conversation_messages_id text not null,
  conversation_id text not null,
  role text not null,
  content text not null,
  intent text,
  created_at timestamptz not null default now(),
  constraint pk_conversation_messages primary key (conversation_messages_id),
  constraint conversation_messages_role_check check (role in ('user', 'ai')),
  constraint fk_conversation_messages_room foreign key (conversation_id) references public.conversation (conversation_id) on delete cascade
);

comment on table public.conversation_messages is '대화 메시지';

create table public.review_likes (
  users_id text not null,
  reviews_id text not null,
  created_at timestamptz not null default now(),
  constraint pk_review_likes primary key (users_id, reviews_id),
  constraint fk_review_likes_user foreign key (users_id) references public.users (users_id) on delete cascade,
  constraint fk_review_likes_review foreign key (reviews_id) references public.reviews (reviews_id) on delete cascade
);

create table public.book_api_cache (
  isbn text not null,
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

create table public.shelves (
  shelves_id text not null,
  users_id text not null,
  shelf_type public.shelf_type_enum not null,
  created_at timestamptz not null default now(),
  constraint pk_shelves primary key (shelves_id),
  constraint fk_shelves_user foreign key (users_id) references public.users (users_id) on delete cascade
);

comment on column public.shelves.shelves_id is '보관함 ID';

create table public.shelf_books (
  books_id text not null,
  shelves_id text not null,
  added_at timestamptz not null default now(),
  constraint pk_shelf_books primary key (books_id, shelves_id),
  constraint fk_shelf_books_book foreign key (books_id) references public.books (id) on delete cascade,
  constraint fk_shelf_books_shelf foreign key (shelves_id) references public.shelves (shelves_id) on delete cascade
);

create table public.book_vectors (
  book_vectors_id uuid not null default gen_random_uuid(),
  isbn text,
  title text not null,
  authors text,
  vector jsonb not null,
  kdc_class text,
  is_cold_start boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint pk_book_vectors primary key (book_vectors_id)
);

create unique index if not exists book_vectors_isbn_unique on public.book_vectors (isbn) where isbn is not null;

create table public.collections (
  collections_id text not null,
  users_id text not null,
  title text not null,
  description text,
  is_public boolean not null default true,
  created_at timestamptz not null default now(),
  constraint pk_collections primary key (collections_id),
  constraint fk_collections_user foreign key (users_id) references public.users (users_id) on delete cascade
);

create table public.collection_books (
  books_id text not null,
  collections_id text not null,
  order_index integer not null default 0,
  added_at timestamptz not null default now(),
  constraint pk_collection_books primary key (books_id, collections_id),
  constraint fk_collection_books_book foreign key (books_id) references public.books (id) on delete cascade,
  constraint fk_collection_books_collection foreign key (collections_id) references public.collections (collections_id) on delete cascade
);

create table public.book_user_states (
  users_id text not null,
  books_id text not null,
  shelf_state public.book_user_state_enum not null,
  reading_proof_url text,
  comment_prompted_at timestamptz,
  context_tags jsonb,
  updated_at timestamptz not null default now(),
  constraint pk_book_user_states primary key (users_id, books_id),
  constraint fk_book_user_states_user foreign key (users_id) references public.users (users_id) on delete cascade,
  constraint fk_book_user_states_book foreign key (books_id) references public.books (id) on delete cascade
);

create table public.stores (
  stores_id text not null,
  name text not null,
  address text,
  latitude numeric(10, 7),
  longitude numeric(10, 7),
  phone text,
  business_hours text,
  created_at timestamptz not null default now(),
  constraint pk_stores primary key (stores_id)
);

-- ---------------------------------------------------------------------------
-- 5) 하이브리드 추천 KG
-- ---------------------------------------------------------------------------
create table public.kg_nodes (
  kg_nodes_id text not null primary key,
  attrs jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

comment on table public.kg_nodes is '하이브리드 추천 LLM 추출 KG 노드 (NetworkX 노드 속성)';

create table public.kg_edges (
  src_id text not null,
  dst_id text not null,
  edge_key int not null default 0,
  relation text not null default 'RELATED_TO',
  confidence double precision not null default 1.0,
  attrs jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint pk_kg_edges primary key (src_id, dst_id, edge_key),
  constraint fk_kg_edges_src foreign key (src_id) references public.kg_nodes (kg_nodes_id) on delete cascade,
  constraint fk_kg_edges_dst foreign key (dst_id) references public.kg_nodes (kg_nodes_id) on delete cascade
);

create index if not exists kg_edges_src_idx on public.kg_edges (src_id);
create index if not exists kg_edges_dst_idx on public.kg_edges (dst_id);

create or replace function public.clear_hybrid_kg()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  truncate table public.kg_edges;
  truncate table public.kg_nodes;
end;
$$;

comment on function public.clear_hybrid_kg() is 'kg_edges / kg_nodes 전체 비우기 (전체 스냅샷 저장 전용)';

revoke all on function public.clear_hybrid_kg() from public;
grant execute on function public.clear_hybrid_kg() to service_role;

-- ---------------------------------------------------------------------------
-- 6) RLS
-- ---------------------------------------------------------------------------
-- `20260411120000_init_books` / `20260413120000_app_schema_*` 에서 이미 만든 정책과
-- 이름이 겹칠 수 있으므로 멱등하게 드롭 후 재생성합니다.
drop policy if exists books_select_public on public.books;
alter table public.books enable row level security;
create policy books_select_public
  on public.books
  for select
  to anon, authenticated
  using (true);

drop policy if exists authors_select_public on public.authors;
alter table public.authors enable row level security;
create policy authors_select_public
  on public.authors
  for select
  to anon, authenticated
  using (true);

drop policy if exists book_authors_select_public on public.book_authors;
alter table public.book_authors enable row level security;
create policy book_authors_select_public
  on public.book_authors
  for select
  to anon, authenticated
  using (true);

drop policy if exists stores_select_public on public.stores;
alter table public.stores enable row level security;
create policy stores_select_public
  on public.stores
  for select
  to anon, authenticated
  using (true);

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

alter table public.kg_nodes enable row level security;
alter table public.kg_edges enable row level security;
