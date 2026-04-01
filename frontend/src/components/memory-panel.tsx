"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { fetchMemories, saveMemory, deleteMemory } from "@/lib/api";

const PROFILE_KEYS = [
  { value: "이름", placeholder: "홍길동" },
  { value: "나이", placeholder: "28" },
  { value: "성별", placeholder: "남성 / 여성" },
  { value: "키", placeholder: "175cm" },
  { value: "체중", placeholder: "78kg" },
  { value: "목표체중", placeholder: "70kg" },
  { value: "알레르기", placeholder: "새우, 땅콩" },
  { value: "질환", placeholder: "당뇨, 고혈압" },
  { value: "복용약", placeholder: "메트포민, 혈압약" },
  { value: "식이제한", placeholder: "채식, 글루텐프리" },
  { value: "운동량", placeholder: "주 3회 / 거의 안 함" },
] as const;

export const MemoryPanel = () => {
  const [open, setOpen] = useState(false);
  const [memories, setMemories] = useState<Record<string, string>>({});
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchMemories();
      setMemories(data);
    } catch {
      /* 서버 미연결 시 무시 */
    }
  }, []);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const handleSave = async () => {
    if (!key.trim() || !value.trim()) return;
    setLoading(true);
    try {
      await saveMemory(key, value.trim());
      setKey("");
      setValue("");
      await load();
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (k: string) => {
    try {
      await deleteMemory(k);
      await load();
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="border-t">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors text-left"
      >
        {open ? "▾ 내 프로필 닫기" : "▸ 내 프로필"}
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-2">
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {Object.entries(memories).length === 0 && (
              <p className="text-xs text-muted-foreground">
                저장된 프로필이 없습니다
              </p>
            )}
            {Object.entries(memories).map(([k, v]) => (
              <div
                key={k}
                className="group flex items-center justify-between text-xs bg-muted rounded px-2 py-1"
              >
                <span>
                  <span className="font-medium">{k}</span>: {v}
                </span>
                <button
                  onClick={() => handleDelete(k)}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all px-1"
                >
                  x
                </button>
              </div>
            ))}
          </div>

          <Separator />

          <div className="space-y-1">
            <select
              value={key}
              onChange={(e) => setKey(e.target.value)}
              className="w-full text-xs h-7 rounded-md border border-input bg-background px-2"
            >
              <option value="">항목 선택</option>
              {PROFILE_KEYS.map((pk) => (
                <option key={pk.value} value={pk.value}>
                  {pk.value}
                </option>
              ))}
            </select>
            <Input
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={
                PROFILE_KEYS.find((pk) => pk.value === key)?.placeholder ??
                "값을 입력하세요"
              }
              className="text-xs h-7"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSave();
              }}
            />
          </div>
          <Button
            onClick={handleSave}
            disabled={loading || !key || !value.trim()}
            size="sm"
            variant="outline"
            className="w-full h-7 text-xs"
          >
            저장
          </Button>
        </div>
      )}
    </div>
  );
};
