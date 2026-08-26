"use client";

import { useState } from "react";

export default function ChatInput({
  onSend,
}: {
  onSend: (text: string) => void;
}) {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim()) return;
    onSend(value.trim());
    setValue("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex border-t p-2 gap-2">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ecrivez votre message..."
        className="flex-1 border rounded-full px-4 py-2 text-sm outline-none"
      />
      <button
        type="submit"
        className="bg-primary text-white rounded-full px-4 py-2 text-sm font-medium"
      >
        Envoyer
      </button>
    </form>
  );
}
