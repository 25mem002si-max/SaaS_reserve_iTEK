import clsx from "clsx";
import type { ChatMessage } from "@/lib/types";

export default function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[75%] rounded-2xl px-3 py-2 text-sm",
          isUser
            ? "bg-primary text-white rounded-br-sm"
            : "bg-gray-100 text-gray-900 rounded-bl-sm"
        )}
      >
        {message.text}
      </div>
    </div>
  );
}
