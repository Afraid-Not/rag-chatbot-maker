-- pgvector 확장 활성화
create extension if not exists vector;

-- 문서 테이블 (vector store)
create table if not exists documents (
    id bigserial primary key,
    content text not null,
    metadata jsonb default '{}',
    embedding vector(1536)  -- text-embedding-3-small 차원
);

-- 유사도 검색 함수
create or replace function match_documents(
    query_embedding vector(1536),
    match_count int default 4,
    filter jsonb default '{}'
)
returns table (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) as similarity
    from documents
    where documents.metadata @> filter
    order by documents.embedding <=> query_embedding
    limit match_count;
end;
$$;

-- metadata 필터링용 GIN 인덱스
create index if not exists documents_metadata_idx
    on documents using gin (metadata jsonb_path_ops);

-- 벡터 인덱스는 데이터 삽입 후 별도 실행할 것
-- 이유: ivfflat은 기존 데이터 기반으로 클러스터링하므로 빈 테이블에 생성하면 효과 없음
-- 데이터 업로드 후 아래 실행:
-- create index if not exists documents_embedding_idx
--     on documents using ivfflat (embedding vector_cosine_ops)
--     with (lists = 100);

-- Memory Bank 테이블
create table if not exists memory_bank (
    id bigserial primary key,
    user_id text not null,
    key text not null,
    value text not null,
    updated_at timestamptz default now(),
    unique(user_id, key)
);

-- Memory Bank 인덱스
create index if not exists memory_bank_user_idx on memory_bank(user_id);
