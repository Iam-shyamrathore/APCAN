import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/chat";
import { AgentBadge } from "./AgentBadge";
import { ToolCallCard } from "./ToolCallCard";
import { Bot, User } from "lucide-react";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-primary/20 text-primary"
            : "bg-secondary text-muted-foreground",
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Content */}
      <div className={cn("max-w-[75%] space-y-1", isUser && "items-end")}>
        {!isUser && message.agent && (
          <div className="mb-1">
            <AgentBadge agent={message.agent} />
          </div>
        )}

        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-md"
              : "bg-card border border-border text-card-foreground rounded-tl-md",
          )}
        >
          {message.content}
          {message.isStreaming && (
            <span className="ml-1 inline-block h-4 w-0.5 animate-pulse bg-primary" />
          )}
        </div>

        {/* Tool calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="space-y-1">
            {message.toolCalls.map((tool, i) => (
              <ToolCallCard key={`${tool.name}-${i}`} tool={tool} />
            ))}
          </div>
        )}

        <p
          className={cn(
            "text-[10px] text-muted-foreground",
            isUser && "text-right",
          )}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}
