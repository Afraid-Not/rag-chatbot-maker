"use client";

import { Session } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { MemoryPanel } from "@/components/memory-panel";
import { cn } from "@/lib/utils";

interface SessionSidebarProps {
  sessions: Session[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export const SessionSidebar = ({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: SessionSidebarProps) => {
  const sorted = [...sessions].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );

  return (
    <div className="w-64 border-r flex flex-col h-screen fixed top-0 left-0 z-10 bg-muted/30">
      <div className="p-3">
        <Button onClick={onNew} className="w-full" variant="outline" size="sm">
          + 새 대화
        </Button>
      </div>
      <Separator />
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sorted.map((session) => (
            <div
              key={session.id}
              className={cn(
                "group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm cursor-pointer hover:bg-muted transition-colors",
                activeId === session.id && "bg-muted font-medium",
              )}
              onClick={() => onSelect(session.id)}
            >
              <span className="flex-1 truncate">{session.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(session.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all text-xs px-1"
              >
                x
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-4">
              대화 기록이 없습니다
            </p>
          )}
        </div>
      </ScrollArea>
      <MemoryPanel />
    </div>
  );
};
