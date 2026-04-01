export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string;
}

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}
