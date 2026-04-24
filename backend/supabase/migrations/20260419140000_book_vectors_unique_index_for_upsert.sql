-- book_vectors: supabase-py upsert(..., on_conflict='isbn') → PostgreSQL ON CONFLICT (isbn)
-- 부분 유니크 인덱스 (WHERE isbn IS NOT NULL)는 이 경로에서 42P10
-- ("no unique or exclusion constraint matching the ON CONFLICT specification") 가 난다.
-- isbn 전체에 대한 유니크 인덱스로 교체한다. (PostgreSQL에서는 UNIQUE 컬럼에 NULL 여러 행 허용)

drop index if exists public.book_vectors_isbn_unique;

create unique index if not exists book_vectors_isbn_unique
  on public.book_vectors (isbn);
