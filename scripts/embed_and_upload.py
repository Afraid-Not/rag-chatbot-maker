"""
chunks.json을 OpenAI text-embedding-3-small로 임베딩하여 Supabase에 업로드하는 스크립트.

Usage:
    python scripts/embed_and_upload.py
    python scripts/embed_and_upload.py --batch-size 100 --dry-run
"""

import json
import os
import sys
import time
from pathlib import Path

import typer
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

# Windows cp949 인코딩 문제 방지
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = typer.Typer()

CHUNKS_PATH = Path(__file__).parent.parent / "data" / "parsed" / "chunks.json"
CACHE_PATH = Path(__file__).parent.parent / "data" / "parsed" / "embeddings_cache.json"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def load_chunks(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cached_embeddings() -> list[list[float]] | None:
    """캐시된 임베딩이 있으면 로드."""
    if CACHE_PATH.exists():
        print(f"캐시 파일 발견: {CACHE_PATH}")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_embeddings_cache(embeddings: list[list[float]]):
    """임베딩 결과를 캐시 파일로 저장."""
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(embeddings, f)
    print(f"임베딩 캐시 저장: {CACHE_PATH}")


def batch_embed(client: OpenAI, texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """OpenAI API로 텍스트를 배치 임베딩."""
    # 캐시 확인
    cached = load_cached_embeddings()
    if cached and len(cached) == len(texts):
        print("캐시된 임베딩 사용 (API 호출 스킵)")
        return cached

    all_embeddings = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(embeddings)
        print(f"  Embedding... {min(i + batch_size, total)}/{total}")

        if i + batch_size < total:
            time.sleep(0.5)

    save_embeddings_cache(all_embeddings)
    return all_embeddings


def sanitize_text(text: str) -> str:
    """PostgreSQL에서 지원하지 않는 null 문자 제거."""
    return text.replace("\u0000", "")


def upload_to_supabase(supabase, chunks: list[dict], embeddings: list[list[float]], batch_size: int = 500, skip: int = 0):
    """Supabase에 배치 업로드."""
    rows = [
        {
            "content": sanitize_text(chunk["content"]),
            "metadata": chunk["metadata"],
            "embedding": embedding,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    if skip > 0:
        rows = rows[skip:]
        print(f"이미 업로드된 {skip}개 건너뜀")

    total = len(rows)
    uploaded = 0
    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("documents").insert(batch).execute()
        uploaded += len(batch)
        print(f"  Uploading... {uploaded}/{total}")


@app.command()
def main(
    batch_size: int = typer.Option(100, help="임베딩 배치 크기"),
    upload_batch: int = typer.Option(500, help="Supabase 업로드 배치 크기"),
    dry_run: bool = typer.Option(False, help="임베딩만 하고 업로드 안 함"),
    skip: int = typer.Option(0, help="이미 업로드된 행 수 (이어서 업로드)"),
):
    # 환경변수 확인
    openai_key = os.getenv("OPENAI_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not openai_key:
        console.print("[red]OPENAI_API_KEY가 .env에 없습니다.[/red]")
        raise typer.Exit(1)
    if not dry_run and (not supabase_url or not supabase_key):
        console.print("[red]SUPABASE_URL 또는 SUPABASE_KEY가 .env에 없습니다.[/red]")
        raise typer.Exit(1)

    # 청크 로드
    chunks = load_chunks(CHUNKS_PATH)
    print(f"총 {len(chunks)}개 청크 로드 완료")

    # 임베딩
    texts = [chunk["content"] for chunk in chunks]
    openai_client = OpenAI(api_key=openai_key)

    start = time.time()
    embeddings = batch_embed(openai_client, texts, batch_size=batch_size)
    elapsed = time.time() - start
    print(f"임베딩 완료: {len(embeddings)}개, {elapsed:.1f}초 소요")

    if dry_run:
        print("--dry-run 모드: 업로드 건너뜀")
        return

    # Supabase 업로드
    supabase = create_client(supabase_url, supabase_key)
    upload_to_supabase(supabase, chunks, embeddings, batch_size=upload_batch, skip=skip)
    print(f"Supabase 업로드 완료: {len(chunks)}개 문서")

    # 인덱스 생성 안내
    print("\n[안내] 벡터 인덱스를 아직 생성하지 않았다면 Supabase SQL Editor에서 실행하세요:")
    print(
        "CREATE INDEX IF NOT EXISTS documents_embedding_idx "
        "ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )


if __name__ == "__main__":
    app()
