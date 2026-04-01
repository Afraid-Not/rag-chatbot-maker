"use client";

import { useState, useEffect, useCallback } from "react";
import { Session, Message } from "@/lib/types";
import {
  loadSessions,
  saveSessions,
  createSession,
  addMessageToSession,
  updateLastMessage,
  deleteSession,
} from "@/lib/sessions";
import { sendChatStream } from "@/lib/api";
import { ChatPanel } from "@/components/chat-panel";
import { SessionSidebar } from "@/components/session-sidebar";

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = loadSessions();
    setSessions(saved);
    if (saved.length > 0) {
      setActiveId(saved[0].id);
    }
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
      saveSessions(sessions);
    }
  }, [sessions, mounted]);

  const activeSession = sessions.find((s) => s.id === activeId) ?? null;

  const handleNew = useCallback(() => {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveId(session.id);
  }, []);

  const handleDelete = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const updated = deleteSession(prev, id);
        if (activeId === id) {
          setActiveId(updated.length > 0 ? updated[0].id : null);
        }
        return updated;
      });
    },
    [activeId],
  );

  const handleSend = useCallback(
    async (content: string) => {
      let currentId = activeId;

      if (!currentId) {
        const session = createSession();
        setSessions((prev) => [session, ...prev]);
        currentId = session.id;
        setActiveId(currentId);
      }

      const userMsg: Message = { role: "user", content };
      setSessions((prev) => addMessageToSession(prev, currentId!, userMsg));

      // 빈 assistant 메시지 추가 (스트리밍으로 채워짐)
      const emptyMsg: Message = { role: "assistant", content: "" };
      setSessions((prev) => addMessageToSession(prev, currentId!, emptyMsg));

      setLoading(true);
      try {
        await sendChatStream(
          content,
          "default",
          (chunk) => {
            setSessions((prev) =>
              updateLastMessage(prev, currentId!, (msg) => ({
                ...msg,
                content: msg.content + chunk,
              })),
            );
          },
          (sources) => {
            setSessions((prev) =>
              updateLastMessage(prev, currentId!, (msg) => ({
                ...msg,
                sources,
              })),
            );
          },
        );
      } catch {
        setSessions((prev) =>
          updateLastMessage(prev, currentId!, (msg) => ({
            ...msg,
            content:
              msg.content || "오류가 발생했습니다. 서버 연결을 확인해주세요.",
          })),
        );
      } finally {
        setLoading(false);
      }
    },
    [activeId],
  );

  if (!mounted) return null;

  return (
    <div className="flex h-screen">
      <SessionSidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNew}
        onDelete={handleDelete}
      />
      <main className="flex-1 flex flex-col ml-64">
        <ChatPanel
          messages={activeSession?.messages ?? []}
          onSend={handleSend}
          loading={loading}
        />
      </main>
    </div>
  );
}
