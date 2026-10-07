"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { adminLogin } from "@/lib/admin-auth";

// ============================================================================
// Connexion administrateur (/admin/login)
// ============================================================================
// Page distincte de /login (connexion des restaurateurs) : l'administrateur
// utilise ses propres identifiants et obtient un jeton admin.
export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      await adminLogin(email.trim(), password);
      router.replace("/admin/restaurants");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connexion impossible.");
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-900 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow-xl">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Administration</h1>
          <p className="mt-1 text-sm text-gray-600">Acces reserve aux administrateurs de la plateforme.</p>
        </div>
        <div>
          <label htmlFor="admin-email" className="block text-sm font-medium text-gray-700">Email</label>
          <input id="admin-email" type="email" autoComplete="username" required value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-light" />
        </div>
        <div>
          <label htmlFor="admin-password" className="block text-sm font-medium text-gray-700">Mot de passe</label>
          <input id="admin-password" type="password" autoComplete="current-password" required value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary-light" />
        </div>
        {error && <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-danger">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full rounded-full bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-50">
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </main>
  );
}
