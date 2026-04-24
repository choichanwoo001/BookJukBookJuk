-- clear_hybrid_kg: 두 테이블을 한 번의 TRUNCATE 로 비워야 FK 제약을 만족한다.
-- (연속 TRUNCATE 시 두 번째에서 "referenced in a foreign key" 오류가 날 수 있음)

create or replace function public.clear_hybrid_kg()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  truncate table public.kg_edges, public.kg_nodes;
end;
$$;

comment on function public.clear_hybrid_kg() is 'kg_edges / kg_nodes 전체 비우기 (전체 스냅샷 저장 전용)';
