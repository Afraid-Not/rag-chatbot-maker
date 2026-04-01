"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ChatPanelProps {
  messages: Message[];
  onSend: (message: string) => void;
  loading: boolean;
}

export const ChatPanel = ({ messages, onSend, loading }: ChatPanelProps) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 p-4">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-20">
              <p className="text-lg font-medium">다이어트 식품 RAG 챗봇</p>
              <p className="text-sm mt-1">궁금한 것을 질문해보세요</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
          {loading && (
            <div className="flex items-start">
              <div className="bg-muted rounded-2xl px-4 py-2.5 text-sm text-muted-foreground">
                <span className="animate-pulse">생각하는 중...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>
      <div className="max-w-2xl mx-auto w-full">
        <ChatInput onSend={onSend} disabled={loading} />
      </div>
    </div>
  );
};
