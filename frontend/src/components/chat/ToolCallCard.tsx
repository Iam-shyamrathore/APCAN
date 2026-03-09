import { cn } from "@/lib/utils";
import { Wrench, Check, Loader2 } from "lucide-react";
import type { ToolCallInfo } from "@/types/chat";

export function ToolCallCard({ tool }: { tool: ToolCallInfo }) {
  return (
    <div className="my-1 flex items-center gap-2 rounded-lg bg-secondary/50 px-3 py-2 text-xs">
      <Wrench size={12} className="shrink-0 text-muted-foreground" />
      <span className="font-mono text-muted-foreground">{tool.name}</span>
      <span className="ml-auto">
        {tool.loading ? (
          <Loader2 size={12} className="animate-spin text-primary" />
        ) : tool.success ? (
          <Check size={12} className="text-success" />
        ) : (
          <span className={cn("text-destructive")}>failed</span>
        )}
      </span>
    </div>
  );
}
