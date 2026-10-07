// ============================================================================
// Session de l'ADMINISTRATEUR de la plateforme
// ============================================================================
// L'administrateur n'est pas un restaurateur : il gere la plateforme entiere
// (ici, les restaurants affiches sur la page d'accueil). Sa session est donc
// stockee sous une cle DIFFERENTE de celle du restaurateur (auth.ts) : se
// connecter en admin ne donne aucun acces au dashboard d'un restaurant, et
// inversement.
//
// IMPORTANT : ce fichier ne protege rien a lui seul. Le navigateur peut
// toujours etre modifie par l'utilisateur. La vraie protection est faite par
// le SERVEUR, qui refuse (401/403) toute route /admin/... sans jeton admin
// valide. Ici, on gere seulement le confort : redirection vers la page de
// connexion, envoi du jeton, deconnexion.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ADMIN_TOKEN_KEY = "saas_admin_jwt";

export function getAdminToken(): string | null {
  // Pendant le rendu cote serveur (Next.js), window/localStorage n'existent pas.
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ADMIN_TOKEN_KEY);
}

export function clearAdminToken() {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
}

export async function adminLogin(email: string, password: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/auth/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    throw new Error("Serveur injoignable. Verifiez que l'API (ou mock-server.js) est lancee.");
  }
  if (response.status === 401 || response.status === 403) throw new Error("Identifiants administrateur invalides.");
  if (!response.ok) throw new Error(`Erreur du serveur (${response.status}).`);

  const body: unknown = await response.json();
  const token = (body as { access_token?: unknown } | null)?.access_token;
  if (typeof token !== "string" || !token) throw new Error("Reponse inattendue du serveur.");
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
}
