import re

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.db.supabase import get_supabase_client

_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


class VectorStore:
    """Supabase match_documents RPC를 직접 호출하는 벡터 스토어."""

    def __init__(self):
        settings = get_settings()
        self.client = get_supabase_client()
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )

    def similarity_search(self, query: str, k: int = 4, filter: dict | None = None) -> list[Document]:
        vector = self.embeddings.embed_query(query)
        result = self.client.rpc(
            "match_documents",
            {
                "query_embedding": vector,
                "match_count": k,
                "filter": filter or {},
            },
        ).execute()

        return self._to_documents(result.data)

    def hybrid_search(self, query: str, k: int = 4, filter: dict | None = None) -> list[Document]:
        """벡터 + 키워드 하이브리드 검색 (RRF)."""
        vector = self.embeddings.embed_query(query)
        result = self.client.rpc(
            "hybrid_search",
            {
                "query_text": query,
                "query_embedding": vector,
                "match_count": k,
                "filter": filter or {},
            },
        ).execute()

        return self._to_documents(result.data)

    def _to_documents(self, rows: list[dict]) -> list[Document]:
        return [
            Document(
                page_content=_SURROGATE_RE.sub("", row["content"]),
                metadata={**row["metadata"], "similarity": row["similarity"]},
            )
            for row in rows
        ]


def get_vector_store() -> VectorStore:
    return VectorStore()
