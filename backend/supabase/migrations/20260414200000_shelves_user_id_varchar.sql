-- shelves.user_id 를 public.users."Key"(varchar) 와 동일 체계로 통일
-- (기존 bigint 는 추천·보관함 조인 시 users / ratings 와 맞지 않음)

alter table public.shelves
  alter column user_id type varchar(255) using user_id::text;

comment on column public.shelves.user_id is '생성한 유저 ID (users."Key" 와 동일 문자열)';
