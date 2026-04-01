from datetime import datetime, timezone

from app.db.supabase import get_supabase_client


class MemoryBank:
    def __init__(self, user_id: str = "default"):
        self.client = get_supabase_client()
        self.user_id = user_id
        self.table = "memory_bank"

    async def save(self, key: str, value: str) -> dict:
        """사용자 프로필/선호도 저장 (upsert)."""
        data = {
            "user_id": self.user_id,
            "key": key,
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        result = (
            self.client.table(self.table)
            .upsert(data, on_conflict="user_id,key")
            .execute()
        )
        return result.data

    async def get(self, key: str) -> str | None:
        """특정 키의 메모리 조회."""
        result = (
            self.client.table(self.table)
            .select("value")
            .eq("user_id", self.user_id)
            .eq("key", key)
            .execute()
        )
        if result.data:
            return result.data[0]["value"]
        return None

    async def get_all(self) -> dict[str, str]:
        """사용자의 모든 메모리 조회."""
        result = (
            self.client.table(self.table)
            .select("key, value")
            .eq("user_id", self.user_id)
            .execute()
        )
        return {row["key"]: row["value"] for row in result.data}

    async def delete(self, key: str) -> None:
        """특정 메모리 삭제."""
        (
            self.client.table(self.table)
            .delete()
            .eq("user_id", self.user_id)
            .eq("key", key)
            .execute()
        )

    async def build_context(self) -> str:
        """메모리를 LLM 컨텍스트 문자열로 변환."""
        memories = await self.get_all()
        if not memories:
            return ""
        lines = [f"- {k}: {v}" for k, v in memories.items()]
        return "사용자 프로필:\n" + "\n".join(lines)
