-- BookJukBookJuk: 책 카탈로그 (export_books_catalog.py 가 Supabase에서 JSON 폴백용으로 내보내는 컬럼과 대응)
-- Supabase SQL Editor에 붙여 넣거나 Supabase CLI로 동일 경로 마이그레이션을 적용

create extension if not exists vector;

create table if not exists public.books (
  id text primary key,
  title text not null default '',
  authors text not null default '',
  description text not null default '',
  author_bio text not null default '',
  editorial_review text not null default '',
  publisher text not null default '',
  published_year text not null default '',
  kdc_class_no text not null default '',
  kdc_class_nm text not null default '',
  sector integer not null default 0,
  cover_image_url text not null default '',
  -- OpenAI text-embedding-3-small 등 (1536차원). 미사용 시 null
  embedding vector(1536)
);

create index if not exists books_sector_idx on public.books (sector);

-- 임베딩을 채운 뒤 유사도 검색 시 주석 해제·lists 튜닝
-- create index if not exists books_embedding_ivfflat
--   on public.books using ivfflat (embedding vector_cosine_ops) with (lists = 100);

alter table public.books enable row level security;

-- 익명(anon) 키로 앱에서 목록 조회 가능
create policy "books_select_public"
  on public.books
  for select
  to anon, authenticated
  using (true);

-- 쓰기는 서비스 롤(시드 스크립트) 또는 로그인 사용자 정책을 별도로 추가
