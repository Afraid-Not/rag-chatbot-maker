from fastapi import APIRouter
from pydantic import BaseModel

from app.core.memory_bank import MemoryBank

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryRequest(BaseModel):
    user_id: str = "default"
    key: str
    value: str


class MemoryResponse(BaseModel):
    key: str
    value: str


@router.post("/", response_model=MemoryResponse)
async def save_memory(req: MemoryRequest) -> MemoryResponse:
    bank = MemoryBank(req.user_id)
    await bank.save(req.key, req.value)
    return MemoryResponse(key=req.key, value=req.value)


@router.get("/{user_id}")
async def get_all_memories(user_id: str) -> dict[str, str]:
    bank = MemoryBank(user_id)
    return await bank.get_all()


@router.delete("/{user_id}/{key}")
async def delete_memory(user_id: str, key: str) -> dict:
    bank = MemoryBank(user_id)
    await bank.delete(key)
    return {"status": "deleted"}
