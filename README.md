# rag-chatbot-maker

Diet food & supplement RAG chatbot with per-user memory. Korean-language domain (다이어트 식품 / 건강기능식품 상담).

## Features

- **RAG Pipeline** — Vector similarity search over ingested documents, augmented with LLM (GPT-4o)
- **Streaming Chat** — SSE-based real-time streaming responses
- **Per-User Memory Bank** — Stores user preferences and context for personalized answers
- **Data Ingestion Pipeline** — Crawl → Parse → Embed → Upload (PDF, TXT, CSV, JSON)
- **CLI Chatbot** — Terminal-based chat interface with Rich formatting
- **Web UI** — Next.js chat interface with session management and markdown rendering

## Tech Stack

| Layer     | Stack                                                                      |
| --------- | -------------------------------------------------------------------------- |
| Backend   | Python 3.12+, FastAPI, LangChain, OpenAI (GPT-4o / text-embedding-3-small) |
| Frontend  | Next.js 16, React 19, Tailwind v4, shadcn/ui                               |
| Database  | Supabase (PostgreSQL + pgvector)                                           |
| CLI       | Typer, Rich                                                                |
| Ingestion | httpx, BeautifulSoup4, PyMuPDF, tiktoken                                   |

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Pydantic Settings (.env)
│   ├── api/routes/
│   │   ├── chat.py           # POST /chat/, /chat/stream
│   │   ├── ingest.py         # POST /ingest/
│   │   └── memory.py         # CRUD /memory/
│   ├── core/
│   │   ├── rag.py            # RAG pipeline (search → memory → LLM)
│   │   ├── memory_bank.py    # Per-user key-value memory
│   │   └── embeddings.py     # Embedding utilities
│   ├── db/
│   │   ├── vector_store.py   # Supabase match_documents RPC
│   │   └── supabase.py       # Singleton Supabase client
│   └── ingestion/
│       ├── crawler.py        # Async web crawler
│       ├── parser.py         # Text chunking
│       └── loader.py         # Vector store loader
├── frontend/                 # Next.js 16 chat UI
├── scripts/
│   ├── crawl_data.py         # Crawl sources
│   ├── parse_data.py         # Parse & chunk documents
│   └── embed_and_upload.py   # Embed & upload to Supabase
├── supabase/
│   ├── setup.sql             # Tables, RPC, indexes
│   └── hybrid_search.sql     # Hybrid search function
├── cli.py                    # Terminal chatbot
└── pyproject.toml
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Supabase project with pgvector enabled
- OpenAI API key

### Database Setup

Run `supabase/setup.sql` in the Supabase SQL Editor. Vector index (ivfflat) should be created **after** data ingestion.

### Backend

```bash
conda create -n rag-chatbot python=3.12 -y
conda activate rag-chatbot
uv pip install -e .
python -m uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### CLI

```bash
python cli.py
```

### Data Pipeline

```bash
python scripts/crawl_data.py
python scripts/parse_data.py
python scripts/embed_and_upload.py --batch-size 100 --upload-batch 100
```

## Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```
OPENAI_API_KEY=sk-your-openai-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

Frontend uses `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API

| Method   | Endpoint                  | Description                         |
| -------- | ------------------------- | ----------------------------------- |
| `GET`    | `/health`                 | Health check                        |
| `POST`   | `/chat/`                  | Send question, get answer + sources |
| `POST`   | `/chat/stream`            | SSE streaming chat                  |
| `POST`   | `/ingest/`                | Ingest URL into vector store        |
| `POST`   | `/memory/`                | Save user memory (key-value)        |
| `GET`    | `/memory/{user_id}`       | Get all memories for user           |
| `DELETE` | `/memory/{user_id}/{key}` | Delete a memory entry               |
