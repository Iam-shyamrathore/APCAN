import { useCallback, useEffect, useRef } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useChatStore } from "@/stores/chatStore";
import type { WSMessage } from "@/types/chat";

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const accessToken = useAuthStore((s) => s.accessToken);
  const {
    setSessionId,
    setConnected,
    setActiveAgent,
    startStreaming,
    appendChunk,
    endStreaming,
    addToolCall,
    updateToolResult,
    addMessage,
  } = useChatStore();

  const connect = useCallback(() => {
    if (!accessToken || ws.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/api/v1/voice/ws?token=${accessToken}`;

    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setConnected(true);

    socket.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);
      handleMessage(msg);
    };

    socket.onclose = () => {
      setConnected(false);
      // Reconnect after 3s
      setTimeout(() => connect(), 3000);
    };

    socket.onerror = () => socket.close();
  }, [accessToken]);

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      const { type, data } = msg;

      switch (type) {
        case "session_created":
          setSessionId(data.session_id as string);
          break;

        case "agent_switch":
          setActiveAgent(data.agent as string);
          break;

        case "stream_start":
          startStreaming(crypto.randomUUID(), data.agent as string);
          break;

        case "stream_chunk":
          appendChunk(data.chunk as string);
          break;

        case "stream_end":
          endStreaming();
          break;

        case "tool_call":
          addToolCall({
            name: data.tool_name as string,
            args: data.arguments as Record<string, unknown>,
            loading: true,
          });
          break;

        case "tool_result":
          updateToolResult(data.tool_name as string, data.success as boolean);
          break;

        case "text_response":
          // Final response — if we were not streaming, add as new message
          if (!useChatStore.getState().isStreaming) {
            addMessage({
              id: crypto.randomUUID(),
              role: "assistant",
              content: data.text as string,
              agent: data.agent as string,
              timestamp: new Date(),
            });
          }
          break;

        case "agent_error":
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            content: `Error: ${data.error as string}`,
            agent: data.agent as string,
            timestamp: new Date(),
          });
          break;

        case "rate_limited":
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            content: "You are sending messages too fast. Please wait a moment.",
            timestamp: new Date(),
          });
          break;

        case "error":
          addMessage({
            id: crypto.randomUUID(),
            role: "assistant",
            content: `Error: ${data.error as string}`,
            timestamp: new Date(),
          });
          break;
      }
    },
    [
      setSessionId,
      setActiveAgent,
      startStreaming,
      appendChunk,
      endStreaming,
      addToolCall,
      updateToolResult,
      addMessage,
    ],
  );

  const sendMessage = useCallback(
    (text: string) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;
      ws.current.send(JSON.stringify({ type: "text_input", data: { text } }));
      // Add user message locally
      addMessage({
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date(),
      });
    },
    [addMessage],
  );

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.send(JSON.stringify({ type: "session_end", data: {} }));
      ws.current.close();
      ws.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  return { connect, disconnect, sendMessage };
}
