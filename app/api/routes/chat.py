from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.rag import ask, ask_stream

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: str


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    result = await ask(req.question, req.user_id)
    return ChatResponse(**result)


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        async for chunk in ask_stream(req.question, req.user_id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
