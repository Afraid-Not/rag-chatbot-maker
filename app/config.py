from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    supabase_url: str
    supabase_key: str

    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
