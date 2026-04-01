"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Message } from "@/lib/types";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex flex-col gap-1",
        isUser ? "items-end" : "items-start",
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground prose prose-sm prose-neutral dark:prose-invert max-w-none",
        )}
      >
        {isUser ? (
          <span className="whitespace-pre-wrap">{message.content}</span>
        ) : (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        )}
      </div>
      {message.sources && (
        <button
          onClick={() => setShowSources(!showSources)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2"
        >
          {showSources ? "출처 숨기기" : "출처 보기"}
        </button>
      )}
      {showSources && message.sources && (
        <div className="max-w-[80%] text-xs text-muted-foreground bg-muted/50 rounded-lg px-3 py-2 whitespace-pre-wrap">
          {message.sources}
        </div>
      )}
    </div>
  );
};
