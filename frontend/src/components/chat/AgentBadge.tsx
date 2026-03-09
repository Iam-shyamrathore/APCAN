import { cn } from "@/lib/utils";
import { AGENT_COLORS, AGENT_LABELS } from "@/types/chat";

export function AgentBadge({ agent }: { agent?: string }) {
  if (!agent) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        AGENT_COLORS[agent] ?? AGENT_COLORS.general,
      )}
    >
      {AGENT_LABELS[agent] ?? agent}
    </span>
  );
}
