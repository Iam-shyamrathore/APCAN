import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { AgentBadge } from "@/components/chat/AgentBadge";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Wifi, WifiOff } from "lucide-react";

export function ChatPage() {
  const { messages, isConnected, activeAgent, sessionId, isStreaming } =
    useChatStore();
  const { connect, sendMessage } = useWebSocket();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    connect();
  }, [connect]);

  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border bg-card px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <MessageSquare size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Voice AI Assistant</h1>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {isConnected ? (
                <>
                  <Wifi size={12} className="text-success" />
                  <span>Connected</span>
                </>
              ) : (
                <>
                  <WifiOff size={12} className="text-destructive" />
                  <span>Disconnected</span>
                </>
              )}
              {sessionId && (
                <span className="text-muted-foreground/50">
                  • {sessionId.slice(0, 8)}…
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {activeAgent && <AgentBadge agent={activeAgent} />}
          {isStreaming && <Badge variant="outline">Streaming…</Badge>}
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <MessageSquare size={32} className="text-primary" />
            </div>
            <h2 className="text-xl font-semibold">How can I help you?</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              I can help with patient intake, appointment scheduling, care
              management, and administrative tasks. Just type your request
              below.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {[
                "Find patient John Doe",
                "Schedule an appointment for tomorrow",
                "Show recent encounters",
                "What are the vitals for patient #1?",
              ].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  className="rounded-full border border-border bg-card px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={sendMessage} disabled={!isConnected} />
      </div>
    </div>
  );
}
