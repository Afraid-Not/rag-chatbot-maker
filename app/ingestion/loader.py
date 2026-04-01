from langchain_core.documents import Document

from app.db.vector_store import get_vector_store
from app.ingestion.crawler import crawl
from app.ingestion.parser import chunk_text


async def ingest_url(url: str) -> int:
    """URL을 크롤링 → 청킹 → vector store에 적재한다."""
    text = await crawl(url)
    chunks = chunk_text(text, metadata={"source": url})

    documents = [
        Document(page_content=c["content"], metadata=c["metadata"])
        for c in chunks
    ]

    vector_store = get_vector_store()
    vector_store.add_documents(documents)

    return len(documents)
