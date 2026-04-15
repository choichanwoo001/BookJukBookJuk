-- 하이브리드 추천 Phase 1: NetworkX KG 영속화 (Supabase)
-- Python: ai/hybrid_recommender/kg_supabase.py

create table if not exists public.kg_nodes (
  node_id text not null primary key,
  attrs jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

comment on table public.kg_nodes is '하이브리드 추천 LLM 추출 KG 노드 (NetworkX 노드 속성)';
comment on column public.kg_nodes.attrs is 'type, label 등 NetworkX 노드 속성 전체';

create table if not exists public.kg_edges (
  src_id text not null,
  dst_id text not null,
  edge_key int not null default 0,
  relation text not null default 'RELATED_TO',
  confidence double precision not null default 1.0,
  attrs jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint pk_kg_edges primary key (src_id, dst_id, edge_key),
  constraint fk_kg_edges_src foreign key (src_id) references public.kg_nodes (node_id) on delete cascade,
  constraint fk_kg_edges_dst foreign key (dst_id) references public.kg_nodes (node_id) on delete cascade
);

comment on table public.kg_edges is '하이브리드 추천 KG 멀티 엣지 (NetworkX MultiDiGraph)';

create index if not exists kg_edges_src_idx on public.kg_edges (src_id);
create index if not exists kg_edges_dst_idx on public.kg_edges (dst_id);

-- PostgREST로 전체 삭제 후 재삽입할 때 사용 (서비스 롤 권장)
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

alter table public.kg_nodes enable row level security;
alter table public.kg_edges enable row level security;
