"use client";

import { useEffect, useRef, useState } from "react";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import TypingIndicator from "./TypingIndicator";
import type { ChatMessage } from "@/lib/types";

// Route http du backend de l'agent IA (expose par le Dev 2) pour le chat en direct

const AI_URL = process.env.NEXT_PUBLIC_AI_URL ?? "http://localhost:8001";


// restaurantId : l'id d'un restaurant existant dans api-core
export default function ChatWidget({ restaurantId = "r1" }: { restaurantId?: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  // Un identifiant de conversation, créé une seule fois par ouverture du chat
  const conversationId = useRef(crypto.randomUUID());

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  async function handleSend(text: string) {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const res = await fetch(`${AI_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId.current,
          restaurant_id: restaurantId,
          message: text,
        }),
      });
      if (!res.ok) throw new Error(`ai-engine ${res.status}`);
      const data: { message: string } = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "agent",
          text: data.message,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "agent",
          text: "Désolé, l'assistant est indisponible pour le moment.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
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