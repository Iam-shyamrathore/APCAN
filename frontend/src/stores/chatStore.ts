import { create } from "zustand";
import type { ChatMessage, ToolCallInfo } from "@/types/chat";

interface ChatState {
  messages: ChatMessage[];
  sessionId: string | null;
  activeAgent: string | null;
  isConnected: boolean;
  isStreaming: boolean;
  streamingMessageId: string | null;

  setSessionId: (id: string) => void;
  setConnected: (v: boolean) => void;
  setActiveAgent: (agent: string) => void;
  addMessage: (msg: ChatMessage) => void;
  startStreaming: (id: string, agent?: string) => void;
  appendChunk: (chunk: string) => void;
  endStreaming: () => void;
  addToolCall: (tool: ToolCallInfo) => void;
  updateToolResult: (name: string, success: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: null,
  activeAgent: null,
  isConnected: false,
  isStreaming: false,
  streamingMessageId: null,

  setSessionId: (id) => set({ sessionId: id }),
  setConnected: (v) => set({ isConnected: v }),
  setActiveAgent: (agent) => set({ activeAgent: agent }),

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  startStreaming: (id, agent) => {
    const msg: ChatMessage = {
      id,
      role: "assistant",
      content: "",
      agent,
      timestamp: new Date(),
      isStreaming: true,
      toolCalls: [],
    };
    set((s) => ({
      messages: [...s.messages, msg],
      isStreaming: true,
      streamingMessageId: id,
    }));
  },

  appendChunk: (chunk) => {
    const { streamingMessageId } = get();
    if (!streamingMessageId) return;
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === streamingMessageId ? { ...m, content: m.content + chunk } : m,
      ),
    }));
  },

  endStreaming: () => {
    const { streamingMessageId } = get();
    if (!streamingMessageId) return;
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === streamingMessageId ? { ...m, isStreaming: false } : m,
      ),
      isStreaming: false,
      streamingMessageId: null,
    }));
  },

  addToolCall: (tool) => {
    const { streamingMessageId } = get();
    if (!streamingMessageId) return;
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === streamingMessageId
          ? { ...m, toolCalls: [...(m.toolCalls ?? []), tool] }
          : m,
      ),
    }));
  },

  updateToolResult: (name, success) => {
    const { streamingMessageId } = get();
    if (!streamingMessageId) return;
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === streamingMessageId
          ? {
              ...m,
              toolCalls: m.toolCalls?.map((t) =>
                t.name === name ? { ...t, success, loading: false } : t,
              ),
            }
          : m,
      ),
    }));
  },

  clearMessages: () =>
    set({ messages: [], sessionId: null, activeAgent: null }),
}));
