"use client";

import { useEffect, useRef, useState } from "react";
import { getSocket } from "@/lib/websocket";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import TypingIndicator from "./TypingIndicator";
import type { ChatMessage } from "@/lib/types";

// Composant principal du widget de messagerie en direct, connecte au backend
// via WebSocket (agent IA du Developpeur 1, expose par le Developpeur 2).
export default function ChatWidget() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socket = getSocket();

    socket.on("agent_message", (msg: ChatMessage) => {
      setIsTyping(false);
      setMessages((prev) => [...prev, msg]);
    });

    socket.on("agent_typing", () => setIsTyping(true));

    return () => {
      socket.off("agent_message");
      socket.off("agent_typing");
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  function handleSend(text: string) {
    const socket = getSocket();
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    socket.emit("client_message", userMessage);
  }

  return (
    <div className="mx-auto w-full max-w-md flex flex-col h-[70vh] bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} />
    </div>
  );
}
