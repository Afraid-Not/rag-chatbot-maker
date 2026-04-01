-- 1) documents 테이블에 tsvector 컬럼 추가 (generated column)
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS content_tsvector tsvector
    GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED;

-- 2) tsvector GIN 인덱스
CREATE INDEX IF NOT EXISTS documents_content_tsvector_idx
    ON documents USING gin (content_tsvector);

-- 3) 하이브리드 검색 함수 (RRF: Reciprocal Rank Fusion)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text text,
    query_embedding vector(1536),
    match_count int DEFAULT 4,
    filter jsonb DEFAULT '{}',
    vector_weight float DEFAULT 0.7,
    keyword_weight float DEFAULT 0.3,
    rrf_k int DEFAULT 60
)
RETURNS TABLE (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            documents.id,
            ROW_NUMBER() OVER (ORDER BY documents.embedding <=> query_embedding) AS rank
        FROM documents
        WHERE documents.metadata @> filter
        ORDER BY documents.embedding <=> query_embedding
        LIMIT LEAST(match_count * 4, 100)
    ),
    keyword_results AS (
        SELECT
            documents.id,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank(documents.content_tsvector, plainto_tsquery('simple', query_text)) DESC
            ) AS rank
        FROM documents
        WHERE documents.metadata @> filter
          AND documents.content_tsvector @@ plainto_tsquery('simple', query_text)
        ORDER BY ts_rank(documents.content_tsvector, plainto_tsquery('simple', query_text)) DESC
        LIMIT LEAST(match_count * 4, 100)
    )
    SELECT
        d.id,
        d.content,
        d.metadata,
        (
            COALESCE(vector_weight / (rrf_k + v.rank), 0.0) +
            COALESCE(keyword_weight / (rrf_k + k.rank), 0.0)
        )::float AS similarity
    FROM vector_results v
    FULL OUTER JOIN keyword_results k ON v.id = k.id
    JOIN documents d ON d.id = COALESCE(v.id, k.id)
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;
