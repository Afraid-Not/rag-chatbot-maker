from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.memory import router as memory_router

app = FastAPI(
    title="Diet Food RAG Chatbot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(memory_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
