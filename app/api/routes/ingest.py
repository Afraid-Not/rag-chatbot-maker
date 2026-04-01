from fastapi import APIRouter
from pydantic import BaseModel

from app.ingestion.loader import ingest_url

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    url: str


class IngestResponse(BaseModel):
    chunks_loaded: int


@router.post("/", response_model=IngestResponse)
async def ingest(req: IngestRequest) -> IngestResponse:
    count = await ingest_url(req.url)
    return IngestResponse(chunks_loaded=count)
