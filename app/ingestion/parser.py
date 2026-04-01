from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


def chunk_text(text: str, metadata: dict | None = None) -> list[dict]:
    """텍스트를 청크로 분할한다."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_text(text)

    return [
        {"content": chunk, "metadata": metadata or {}}
        for chunk in chunks
    ]
