const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const defaultHeaders: Record<string, string> = {
  "Content-Type": "application/json",
  "ngrok-skip-browser-warning": "true",
};

export const sendChatStream = async (
  question: string,
  userId: string = "default",
  onChunk: (text: string) => void,
  onSources: (sources: string) => void,
) => {
  const res = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ question, user_id: userId }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") return;

      // 출처 파싱
      if (data.includes("[SOURCES]")) {
        const match = data.match(/\[SOURCES\]([\s\S]*?)\[\/SOURCES\]/);
        if (match) onSources(match[1]);
      } else {
        onChunk(data);
      }
    }
  }
};

export const fetchMemories = async (
  userId: string = "default",
): Promise<Record<string, string>> => {
  const res = await fetch(`${API_URL}/memory/${userId}`, {
    headers: { "ngrok-skip-browser-warning": "true" },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};

export const saveMemory = async (
  key: string,
  value: string,
  userId: string = "default",
) => {
  const res = await fetch(`${API_URL}/memory/`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ user_id: userId, key, value }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};

export const deleteMemory = async (key: string, userId: string = "default") => {
  const res = await fetch(`${API_URL}/memory/${userId}/${key}`, {
    method: "DELETE",
    headers: { "ngrok-skip-browser-warning": "true" },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};
