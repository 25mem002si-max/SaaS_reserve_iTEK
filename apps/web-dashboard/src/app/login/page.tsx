"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";

// Authentification JWT du restaurateur (multi-tenant)
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [recoveryMessage, setRecoveryMessage] = useState<string | null>(null);
  const [registrationMessage, setRegistrationMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError("Identifiants invalides");
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-white p-6 rounded-xl shadow"
      >
        <h1 className="text-xl font-semibold mb-4">Connexion Restaurateur</h1>

        <label className="block text-sm mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border rounded-lg p-2 mb-3"
          required
        />

        <label className="block text-sm mb-1">Mot de passe</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border rounded-lg p-2 mb-3"
          required
        />

        <button
          type="submit"
          className="w-full bg-primary text-white rounded-lg p-2 font-medium"
        >
          Se connecter
        </button>

        {recoveryMessage && (
          <p className="text-sm text-gray-600 mb-2" role="status">
            {recoveryMessage}
          </p>
        )}

        {error && <p className="text-danger text-sm mb-2">{error}</p>}

        
        <button
          type="button"
          onClick={() => setRecoveryMessage("La récupération du mot de passe sera bientôt disponible.")}
          className="block ml-auto text-sm text-primary hover:underline mb-3"
        >
          Mot de passe oublié ?
        </button>

        <button
          type="button"
          onClick={() => setRegistrationMessage("La création de compte sera bientôt disponible.")}
          className="block mx-auto text-sm text-primary hover:underline"
        >
          Créer un compte
        </button>

        {registrationMessage && (
          <p className="text-sm text-gray-600 mt-2 text-center" role="status">
            {registrationMessage}
          </p>
        )}

      </form>
    </main>
  );
}
