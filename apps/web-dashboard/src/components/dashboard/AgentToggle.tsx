"use client";

import { useState } from "react";
import { toggleAgent } from "@/lib/api";

// Interrupteur d'activation/desactivation de l'agent IA pour ce restaurant
export default function AgentToggle() {
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    setLoading(true);
    try {
      const next = !enabled;
      await toggleAgent(next);
      setEnabled(next);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`px-4 py-2 rounded-full text-sm font-medium ${
        enabled ? "bg-success text-white" : "bg-gray-300 text-gray-700"
      }`}
    >
      Agent IA : {enabled ? "Actif" : "Desactive"}
    </button>
  );
}
