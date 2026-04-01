"""
data/ 폴더의 모든 파일(txt, csv, json, pdf, html)을 파싱하고
RAG 파이프라인용 청크 JSON으로 출력한다.

Usage:
    python scripts/parse_data.py
    python scripts/parse_data.py --chunk-size 800 --chunk-overlap 150
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

# Windows cp949 encoding fix
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import fitz  # pymupdf
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console
from rich.table import Table
import typer

# ── Defaults ────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "parsed" / "chunks.json"
SUPPORTED_EXTENSIONS = {".txt", ".csv", ".json", ".pdf", ".html"}

console = Console()
app = typer.Typer(pretty_exceptions_enable=False)


# ── Helpers ─────────────────────────────────────────────────────────────

make_chunk_id = lambda src, idx: hashlib.sha256(f"{src}::{idx}".encode()).hexdigest()[:16]


def detect_language(filename: str, content: str) -> str:
    if filename.lower().startswith("en_"):
        return "en"
    if filename.lower().startswith("kr_"):
        return "ko"
    korean_chars = len(re.findall(r"[가-힣]", content[:500]))
    return "ko" if korean_chars > 20 else "en"


def detect_category(filename: str) -> str:
    fname = filename.lower()
    rules: list[tuple[str, list[str]]] = [
        ("medical", ["병원", "비만", "질환", "의학", "질병관리청", "msd매뉴얼", "대한비만"]),
        ("ingredient", ["효능", "부작용", "nccih", "카르니틴", "가르시니아", "키토산"]),
        ("market", ["시장", "트렌드", "리포트", "보도자료", "결산"]),
        ("nutrition", ["칼로리", "영양", "nutrient", "컬리", "하이닥"]),
        ("supplement", ["nih", "건강기능식품", "식약처", "고시"]),
        ("drug", ["위고비", "glp", "비만치료"]),
        ("diet", ["다이어트", "diet", "weight", "식단", "운동"]),
        ("food", ["단백질", "요거트", "두부", "귀리", "닭가슴살", "오트밀"]),
        ("review", ["review"]),
        ("research", ["meta", "rct", "clinical", "analysis", "mechanism", "pharmacol"]),
        ("conversation", ["챗봇", "시나리오", "chatbot", "conversation"]),
    ]
    for category, keywords in rules:
        if any(kw in fname for kw in keywords):
            return category
    return "general"


# ── Parsers ─────────────────────────────────────────────────────────────

def parse_txt(path: Path) -> list[tuple[str, dict]]:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}

    # Korean header: 출처 URL / 수집일자 / 제목
    ko = re.match(r"출처\s*URL:\s*(.+?)\n수집일자:\s*(.+?)\n제목:\s*(.+?)\n", text)
    if ko:
        meta["source_url"] = ko.group(1).strip()
        meta["collected_date"] = ko.group(2).strip()
        meta["title"] = ko.group(3).strip()

    # English header: SOURCE / URL / RETRIEVED / TYPE
    en = re.match(
        r"SOURCE:\s*(.+?)\nURL:\s*(.+?)\nRETRIEVED:\s*(.+?)\n(?:TYPE:\s*(.+?)\n)?",
        text,
    )
    if en:
        meta["source"] = en.group(1).strip()
        meta["source_url"] = en.group(2).strip()
        meta["collected_date"] = en.group(3).strip()
        if en.group(4):
            meta["doc_type"] = en.group(4).strip()

    # Strip header / separator lines
    body = re.split(r"={5,}", text, maxsplit=2)
    body_text = body[-1].strip() if len(body) > 1 else text.strip()

    return [(body_text, meta)]


def parse_csv_file(path: Path) -> list[tuple[str, dict]]:
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []

    headers = list(rows[0].keys())
    sections = [" | ".join(f"{h}: {v}" for h, v in row.items() if v) for row in rows]
    combined = f"[테이블: {path.stem}]\n컬럼: {', '.join(headers)}\n\n" + "\n\n".join(sections)

    return [(combined, {"table_columns": headers, "row_count": len(rows)})]


def parse_json_data(path: Path) -> list[tuple[str, dict]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    results: list[tuple[str, dict]] = []

    if isinstance(raw, list):
        for item in raw:
            item_meta: dict = {}
            if "id" in item or "review_id" in item:
                item_meta["original_id"] = item.get("id") or item.get("review_id")
            if "category" in item:
                item_meta["original_category"] = item["category"]
            results.append((_flatten_json(item), item_meta))
        return results

    # Single nested object
    meta: dict = {}
    for key in ("source", "category", "collected_date"):
        if key in raw:
            meta[key if key != "category" else "original_category"] = raw[key]
    return [(_flatten_json(raw), meta)]


def _flatten_json(obj: object, depth: int = 0) -> str:
    indent = "  " * depth
    lines: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{indent}{k}:")
                lines.append(_flatten_json(v, depth + 1))
            else:
                lines.append(f"{indent}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(_flatten_json(item, depth))
                lines.append("")
            else:
                lines.append(f"{indent}- {item}")
    else:
        lines.append(f"{indent}{obj}")

    return "\n".join(lines)


def parse_pdf(path: Path) -> list[tuple[str, dict]]:
    doc = fitz.open(str(path))
    page_count = len(doc)
    pages_text: list[str] = []
    ocr_pages: list[int] = []

    for i in range(page_count):
        page = doc[i]
        text = page.get_text().strip()

        if text:
            pages_text.append(text)
            continue

        # OCR fallback (requires Tesseract installed)
        try:
            tp = page.get_textpage_ocr(flags=0, full=True)
            text = page.get_text("text", textpage=tp).strip()
            if text:
                pages_text.append(text)
                ocr_pages.append(i + 1)
            else:
                console.print(f"    [dim]page {i + 1}: no text extracted[/dim]")
        except Exception:
            console.print(f"    [dim]page {i + 1}: OCR unavailable, skipped[/dim]")

    pdf_meta = doc.metadata or {}
    doc.close()

    meta: dict = {"page_count": page_count}
    if pdf_meta.get("title"):
        meta["title"] = pdf_meta["title"]
    if ocr_pages:
        meta["ocr_pages"] = ocr_pages

    return [("\n\n".join(pages_text), meta)]


def parse_html(path: Path) -> list[tuple[str, dict]]:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else path.stem

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return [(text, {"title": title})]


# ── Router ──────────────────────────────────────────────────────────────

PARSERS = {
    ".txt": parse_txt,
    ".csv": parse_csv_file,
    ".json": parse_json_data,
    ".pdf": parse_pdf,
    ".html": parse_html,
}


# ── Chunking ────────────────────────────────────────────────────────────

def build_chunks(
    documents: list[tuple[str, dict, str]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[dict] = []

    for text, doc_meta, source_file in documents:
        if not text.strip():
            continue

        split_texts = splitter.split_text(text)
        lang = detect_language(source_file, text)
        cat = detect_category(source_file)
        ftype = Path(source_file).suffix.lstrip(".")

        for i, chunk_text in enumerate(split_texts):
            chunks.append({
                "id": make_chunk_id(source_file, i),
                "content": chunk_text,
                "metadata": {
                    "source_file": source_file.replace("\\", "/"),
                    "file_type": ftype,
                    "chunk_index": i,
                    "total_chunks_in_doc": len(split_texts),
                    "language": lang,
                    "category": cat,
                    **doc_meta,
                },
            })

    return chunks


# ── CLI ─────────────────────────────────────────────────────────────────

@app.command()
def main(
    data_dir: Path = typer.Option(DATA_DIR, help="데이터 디렉토리 경로"),
    output: Path = typer.Option(OUTPUT_PATH, help="출력 JSON 경로"),
    chunk_size: int = typer.Option(1000, help="청크 크기 (문자 수)"),
    chunk_overlap: int = typer.Option(200, help="청크 오버랩 (문자 수)"),
) -> None:
    """data/ 폴더의 모든 파일을 파싱 -> 청킹 -> JSON 출력"""
    console.print(f"\n[bold]data_dir :[/bold] {data_dir}")
    console.print(f"[bold]output   :[/bold] {output}")
    console.print(f"[bold]chunk    :[/bold] size={chunk_size}  overlap={chunk_overlap}\n")

    exclude_dirs = {"parsed"}
    all_files = sorted(
        f for f in data_dir.rglob("*")
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and not any(part in exclude_dirs for part in f.relative_to(data_dir).parts)
    )
    console.print(f"[bold]{len(all_files)}개 파일 발견[/bold]\n")

    documents: list[tuple[str, dict, str]] = []
    stats: dict[str, int] = {}
    errors: list[str] = []

    for fpath in all_files:
        rel = fpath.relative_to(data_dir)
        suffix = fpath.suffix.lower()
        parser = PARSERS.get(suffix)
        if not parser:
            continue

        try:
            for text, meta in parser(fpath):
                documents.append((text, meta, str(rel)))
            stats[suffix] = stats.get(suffix, 0) + 1
            console.print(f"  [green]OK[/green] {rel}")
        except Exception as e:
            errors.append(f"{rel}: {e}")
            console.print(f"  [red]FAIL[/red] {rel}: {e}")

    # Chunk
    console.print(f"\n[bold]청킹 중...[/bold]")
    chunks = build_chunks(documents, chunk_size, chunk_overlap)

    # Save
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary table
    table = Table(title="\n파싱 결과")
    table.add_column("항목", style="bold")
    table.add_column("값", justify="right")

    for ext, count in sorted(stats.items()):
        table.add_row(f"{ext} 파일", str(count))
    table.add_row("총 문서 수", str(len(documents)))
    table.add_row("총 청크 수", str(len(chunks)))
    table.add_row("출력 파일", str(output))
    if errors:
        table.add_row("오류", str(len(errors)))

    console.print(table)

    if errors:
        console.print("\n[bold red]오류 목록:[/bold red]")
        for err in errors:
            console.print(f"  - {err}")


if __name__ == "__main__":
    app()
