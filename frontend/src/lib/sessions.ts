import { Session, Message } from "./types";

const STORAGE_KEY = "rag-chat-sessions";

export const generateId = () => crypto.randomUUID();

export const loadSessions = (): Session[] => {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : [];
};

export const saveSessions = (sessions: Session[]) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
};

export const createSession = (): Session => {
  const now = new Date().toISOString();
  return {
    id: generateId(),
    title: "새 대화",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
};

export const updateSessionTitle = (session: Session): string => {
  const firstUserMsg = session.messages.find((m) => m.role === "user");
  if (!firstUserMsg) return "새 대화";
  return (
    firstUserMsg.content.slice(0, 30) +
    (firstUserMsg.content.length > 30 ? "..." : "")
  );
};

export const addMessageToSession = (
  sessions: Session[],
  sessionId: string,
  message: Message,
): Session[] => {
  return sessions.map((s) => {
    if (s.id !== sessionId) return s;
    const updated = {
      ...s,
      messages: [...s.messages, message],
      updatedAt: new Date().toISOString(),
    };
    updated.title = updateSessionTitle(updated);
    return updated;
  });
};

export const deleteSession = (
  sessions: Session[],
  sessionId: string,
): Session[] => {
  return sessions.filter((s) => s.id !== sessionId);
};

export const updateLastMessage = (
  sessions: Session[],
  sessionId: string,
  updater: (msg: Message) => Message,
): Session[] => {
  return sessions.map((s) => {
    if (s.id !== sessionId || s.messages.length === 0) return s;
    const messages = [...s.messages];
    messages[messages.length - 1] = updater(messages[messages.length - 1]);
    return { ...s, messages, updatedAt: new Date().toISOString() };
  });
};
